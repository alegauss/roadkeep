import { spawn } from 'node:child_process'

import {
  outcomeOf,
  readSessionLine,
  type SessionCall,
  type SessionEvent,
  type SessionOutcome,
} from '@rk/core'

/**
 * A Claude Code session as a process this app owns.
 *
 * In `shell` for the reason the transport is: `core` states what a session is handed and
 * how its stream reads, and this is the part that spawns. The two are separable, and only
 * this half knows what an operating system is.
 *
 * **Owned, killable, and its exit drawn.** The three failures the design names each become
 * a state rather than a crash: no `claude` on the machine, a session that exits non-zero,
 * and a session cancelled from the window.
 *
 * **stdin is the session's other half** (RG272). The prompt goes in as the first message, and
 * standard input stays open for the answers to the questions the session asks while it runs. It
 * is closed at the `result` line, which is where the session stops reading and exits — left open
 * past it, the process would wait on input that is never coming.
 *
 * **No shell.** The prompt is a whole JSON payload with quotes and newlines in it, and it
 * is one element of an argv array. A shell is where that becomes a quoting defect.
 */

export interface RunningSession {
  /** Stop it. Safe to call twice, and safe after it has already exited. */
  cancel(): void
  /** Resolves when the process is gone, whatever became of it. */
  readonly finished: Promise<SessionOutcome>
  /** Every event read so far, in the order the session wrote them. */
  readonly events: readonly SessionEvent[]
  /**
   * Write one line to the session's standard input (RG272). False where it no longer reads it —
   * ended, killed, or past its `result` — and nothing was written.
   */
  write(line: string): boolean
}

export interface SessionWatcher {
  /** One event, as soon as its line is complete. RG40 is what draws these. */
  onEvent?(event: SessionEvent): void
  /**
   * Every line, raw, as it completes — before it is read into anything.
   *
   * The raw form has to stay reachable for a live session and not only for a finished
   * one: a run that goes wrong is diagnosed from what it actually emitted, and an event
   * is a reading of a line rather than the line itself.
   */
  onLine?(line: string): void
  /** A line the reader could not parse. Kept apart from an event it read and ignored. */
  onUnreadable?(line: string): void
}

/**
 * Start a session and hand back something that can be watched and stopped.
 *
 * Nothing here waits for the whole run before reporting: `stream-json` exists so that a
 * window can show the turns as they happen, and buffering to the end would throw away
 * exactly what it is for.
 *
 * @param env the session's environment: inherited whole, unless RG205 decided one variable
 *   is not the session's to see.
 */
export function startSession(
  call: SessionCall,
  watcher: SessionWatcher = {},
  env: NodeJS.ProcessEnv = process.env,
): RunningSession {
  const events: SessionEvent[] = []
  let cancelled = false
  let stderr = ''
  let child: ReturnType<typeof spawn> | null = null
  // Whether standard input still takes a line: false from the `result` line, or once it closed.
  let reading = false
  const closeInput = () => {
    reading = false
    child?.stdin?.end()
  }

  const finished = new Promise<SessionOutcome>((resolve) => {
    let settled = false
    const settle = (outcome: SessionOutcome) => {
      if (settled) return
      settled = true
      resolve(outcome)
    }

    try {
      child = spawn(call.command, [...call.argv], {
        cwd: call.cwd,
        shell: false,
        windowsHide: true,
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
      })
      // A session that exits first leaves a write with nowhere to go, and that is not a crash.
      child.stdin?.on('error', () => undefined)
      child.stdin?.on('close', () => {
        reading = false
      })
      reading = true
      for (const line of call.input) child.stdin?.write(`${line}\n`)
      // Nothing to say is nothing to wait for: a call with no message would hold the CLI open.
      if (call.input.length === 0) closeInput()
    } catch (cause) {
      // Node can throw synchronously for a command that cannot be spawned at all.
      settle({
        state: 'unavailable',
        sessionId: '',
        code: null,
        said: cause instanceof Error ? cause.message : String(cause),
        result: '',
        denials: [],
      })
      return
    }

    // One JSON object per line, and a chunk boundary can fall anywhere — including inside
    // a prompt echoed back. So lines are assembled here rather than assumed.
    let pending = ''
    const take = (chunk: string) => {
      pending += chunk
      let cut = pending.indexOf('\n')
      while (cut !== -1) {
        const line = pending.slice(0, cut)
        pending = pending.slice(cut + 1)
        offer(line)
        cut = pending.indexOf('\n')
      }
    }

    const offer = (line: string) => {
      if (line.trim() === '') return
      watcher.onLine?.(line)
      const event = readSessionLine(line)
      if (event === null) {
        watcher.onUnreadable?.(line)
        return
      }
      events.push(event)
      watcher.onEvent?.(event)
      // The turn is over, and the session reads nothing more: closing is what lets it exit.
      if (event.kind === 'finished') closeInput()
    }

    child.stdout?.setEncoding('utf8')
    child.stdout?.on('data', (chunk: string) => take(chunk))
    child.stderr?.setEncoding('utf8')
    child.stderr?.on('data', (chunk: string) => {
      stderr += chunk
    })

    child.on('error', (cause: NodeJS.ErrnoException) => {
      // ENOENT is the machine having no `claude`, which is a state of its own: a fact
      // about the machine rather than a session that went wrong. Naming which copy would
      // have answered is RG43's.
      settle({
        state: cause.code === 'ENOENT' ? 'unavailable' : 'failed',
        sessionId: '',
        code: null,
        said: cause.message,
        result: '',
        denials: [],
      })
    })

    child.on('close', (code: number | null) => {
      // Whatever is left without a trailing newline is still a line.
      if (pending.trim() !== '') offer(pending)
      pending = ''
      settle(outcomeOf(events, { code, cancelled, said: stderr.trim() }))
    })
  })

  return {
    cancel() {
      if (child === null) return
      cancelled = true
      child.kill()
    },
    finished,
    get events() {
      return events
    },
    write(line) {
      const input = child?.stdin
      if (!reading || input?.writable !== true) return false
      input.write(`${line}\n`)
      return true
    },
  }
}
