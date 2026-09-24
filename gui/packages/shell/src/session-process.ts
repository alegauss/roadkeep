import { spawn, type ChildProcess } from 'node:child_process'

import {
  query,
  type CanUseTool,
  type Options,
  type PermissionResult,
  type PermissionUpdate,
  type SpawnedProcess,
  type SpawnOptions,
} from '@anthropic-ai/claude-agent-sdk'
import {
  answeredBy,
  asRecord,
  outcomeOf,
  readSessionLine,
  type SessionCall,
  type SessionEvent,
  type SessionOutcome,
} from '@rk/core'

/**
 * A Claude Code session as a process this app owns, carried by the Agent SDK (RG273).
 *
 * In `shell` for the reason the transport is: `core` states what a session is handed and
 * how its stream reads, and this is the part that spawns. The two are separable, and only
 * this half knows what an operating system is — or that there is an SDK at all.
 *
 * **The protocol is the SDK's.** The prompt on standard input, a question as a
 * `control_request`, its answer, and standard input closed at the `result`: RG272 wrote that
 * by hand, and `@anthropic-ai/claude-agent-sdk` is Anthropic publishing it. What this keeps is
 * the record. Every message the SDK yields is offered as the line it was, so `readSessionLine`,
 * the sessions and every screen read what they read before; and a question `canUseTool` is
 * asked becomes the `control_request` line RG272's reader takes, answered when its
 * `control_response` is written back.
 *
 * **The person's `claude`, never a bundled one.** The SDK installs a native Claude Code per
 * platform and runs it when told nothing. It is always told: the executable is the command
 * RG43 resolved, spawned here with the rest of its command line in front of the SDK's flags,
 * so the session signs in as whoever the person is. `electron-builder.yml` packages built
 * output only, so the SDK's binary never ships either.
 *
 * **What the CLI would have done, named rather than defaulted.** The SDK's defaults are not
 * `claude -p`'s: left alone it runs with an empty system prompt. So the session gets Claude
 * Code's own, loads the user's, the project's and the local settings — which is where
 * `CLAUDE.md`, rules and skills come from — and runs in the environment RG205 composed, whole,
 * since the SDK replaces the environment rather than merging it.
 *
 * **Owned, killable, and its exit drawn.** The three failures the design names each become
 * a state rather than a crash: no `claude` on the machine, a session that exits non-zero,
 * and a session cancelled from the window. Cancelling is the SDK's abort and the process
 * killed at once: left to the SDK, a session in the middle of a turn reads the end of its input
 * as nothing more to come, finishes the turn, and is killed only after a seven-second grace —
 * measured, with the window saying running all the while somebody pressed Stop.
 */

export interface RunningSession {
  /** Stop it. Safe to call twice, and safe after it has already exited. */
  cancel(): void
  /** Resolves when the process is gone, whatever became of it. */
  readonly finished: Promise<SessionOutcome>
  /** Every event read so far, in the order the session wrote them. */
  readonly events: readonly SessionEvent[]
  /**
   * Answer a question the session is waiting on (RG272), with the `control_response` line that
   * answers it. False where nothing by that id is waiting — answered, withdrawn, or the session
   * ended — and nothing was sent.
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
   *
   * Every line is a message the SDK read (RG273). Output that is not JSON at all is the SDK's
   * to drop and never reaches here; what the process says outside the protocol is its stderr,
   * which the outcome carries.
   */
  onLine?(line: string): void
}

/** The settings a session loads, named: the CLI's own set, and a default the SDK has changed. */
const SETTING_SOURCES: Options['settingSources'] = ['user', 'project', 'local']

/** Claude Code's own system prompt, which is what a `claude` started by hand runs with. */
const CLAUDE_CODE_PROMPT: Options['systemPrompt'] = { type: 'preset', preset: 'claude_code' }

/** What the agent reads for a question the session itself withdrew, or one the run outlived. */
const NOT_ANSWERED = 'The question was withdrawn before the person watching answered it.'

/** The answer a `control_response` line carries, as the SDK takes one. */
function permissionIn(line: string): PermissionResult | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(line)
  } catch {
    return null
  }
  const answer = asRecord(asRecord(asRecord(parsed)?.['response'])?.['response'])
  if (answer?.['behavior'] === 'deny') {
    const message = answer['message']
    return { behavior: 'deny', message: typeof message === 'string' ? message : NOT_ANSWERED }
  }
  if (answer?.['behavior'] !== 'allow') return null
  const input = asRecord(answer['updatedInput'])
  const permissions: unknown = answer['updatedPermissions']
  // The engine's own suggestions coming back, which `answerLine` narrowed to the session: kept
  // where they are objects at all, since what is in one is the engine's grammar and not this app's.
  const updates = Array.isArray(permissions)
    ? permissions.filter((one): one is PermissionUpdate => asRecord(one) !== null)
    : []
  return {
    behavior: 'allow',
    ...(input === null ? {} : { updatedInput: input }),
    ...(updates.length === 0 ? {} : { updatedPermissions: updates }),
  }
}

/**
 * Start a session and hand back something that can be watched and stopped.
 *
 * Nothing here waits for the whole run before reporting: a window shows the turns as they
 * happen, and buffering to the end would throw away exactly what the stream is for.
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
  const abort = new AbortController()
  /**
   * What the run has come to so far, in one object rather than as locals: every field is written
   * from a callback, and a local a checker only ever sees assigned once reads as never changing.
   */
  const standing = {
    cancelled: false,
    ended: false,
    stderr: '',
    code: null as number | null,
    failure: null as NodeJS.ErrnoException | null,
    exited: Promise.resolve(),
    child: null as ChildProcess | null,
  }
  // Every question still waiting on a person, by the engine's own id for it.
  const waiting = new Map<string, (answer: PermissionResult) => void>()

  const offer = (line: string) => {
    if (line.trim() === '') return
    watcher.onLine?.(line)
    const event = readSessionLine(line)
    if (event === null) return
    events.push(event)
    watcher.onEvent?.(event)
  }

  /**
   * The agent's own command line, spawned: its command, the rest of what it resolved as, then
   * the SDK's flags. The SDK names the executable back as the command, or — for a path it takes
   * for a script — as the first argument after a runtime; either way what follows it is the SDK's.
   */
  const spawnAgent = (options: SpawnOptions): SpawnedProcess => {
    const flags =
      options.command === call.command
        ? options.args
        : options.args.slice(options.args.indexOf(call.command) + 1)
    const child: ChildProcess = spawn(call.command, [...call.prefix, ...flags], {
      cwd: options.cwd,
      env: options.env,
      shell: false,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'pipe'],
    })
    standing.child = child
    standing.exited = new Promise((resolve) => {
      child.once('close', (exit: number | null) => {
        standing.code = exit
        resolve()
      })
      child.once('error', (cause: NodeJS.ErrnoException) => {
        // ENOENT is the machine having no `claude`: a fact about the machine, and a state of its
        // own. The process never started, so nothing else will end the run.
        standing.failure = cause
        abort.abort()
        resolve()
      })
    })
    const { stdin, stdout, stderr: errors } = child
    if (stdin === null || stdout === null || errors === null) {
      throw new Error('the session was spawned without the pipes it is read over')
    }
    stdin.on('error', () => undefined)
    errors.setEncoding('utf8')
    errors.on('data', (chunk: string) => {
      standing.stderr += chunk
    })
    // The SDK's own signal, which it raises once standard input closed and its grace ran out.
    options.signal.addEventListener('abort', () => child.kill(), { once: true })
    // What the SDK asks of a process is what a child already is, once its two pipes are known
    // to be there: the same object, with the types saying what the spawn settled.
    return Object.assign(child, { stdin, stdout })
  }

  const canUseTool: CanUseTool = (tool, input, asked) =>
    new Promise((resolve) => {
      const requestId = asked.requestId
      const line = JSON.stringify({
        type: 'control_request',
        request_id: requestId,
        request: {
          subtype: 'can_use_tool',
          tool_name: tool,
          display_name: asked.displayName,
          input,
          description: asked.description,
          permission_suggestions: asked.suggestions ?? [],
          tool_use_id: asked.toolUseID,
        },
      })
      waiting.set(requestId, resolve)
      asked.signal.addEventListener(
        'abort',
        () => {
          if (!waiting.delete(requestId)) return
          offer(JSON.stringify({ type: 'control_cancel_request', request_id: requestId }))
          resolve({ behavior: 'deny', message: NOT_ANSWERED })
        },
        { once: true },
      )
      // After the messages already read have been offered: the SDK asks as soon as it reads the
      // request, which can be before the call it holds up has reached the record.
      setImmediate(() => {
        if (waiting.has(requestId)) offer(line)
      })
    })

  const finished = (async (): Promise<SessionOutcome> => {
    let thrown = ''
    try {
      const messages = query({
        prompt: call.prompt,
        options: {
          abortController: abort,
          cwd: call.cwd,
          env: { ...env },
          pathToClaudeCodeExecutable: call.command,
          spawnClaudeCodeProcess: spawnAgent,
          canUseTool,
          settingSources: SETTING_SOURCES,
          systemPrompt: CLAUDE_CODE_PROMPT,
          ...(call.resume === '' ? {} : { resume: call.resume }),
          ...(call.allowed.length === 0 ? {} : { allowedTools: [...call.allowed] }),
        },
      })
      for await (const message of messages) offer(JSON.stringify(message))
    } catch (cause) {
      thrown = cause instanceof Error ? cause.message : String(cause)
    }
    standing.ended = true
    for (const answer of waiting.values()) answer({ behavior: 'deny', message: NOT_ANSWERED })
    waiting.clear()
    await standing.exited

    const failure = standing.failure
    if (failure !== null) {
      return {
        state: failure.code === 'ENOENT' ? 'unavailable' : 'failed',
        sessionId: '',
        code: null,
        said: failure.message,
        result: '',
        denials: [],
      }
    }
    // What the process said on stderr first, and what the SDK threw where it said nothing.
    const said = standing.stderr.trim()
    return outcomeOf(events, {
      code: standing.code,
      cancelled: standing.cancelled,
      said: said === '' && !standing.cancelled ? thrown : said,
    })
  })()

  return {
    cancel() {
      if (standing.ended) return
      standing.cancelled = true
      abort.abort()
      standing.child?.kill()
    },
    finished,
    get events() {
      return events
    },
    write(line) {
      const answered = answeredBy(line)
      const answer = permissionIn(line)
      if (answered === null || answer === null) return false
      const waitingOn = waiting.get(answered.requestId)
      if (waitingOn === undefined) return false
      waiting.delete(answered.requestId)
      waitingOn(answer)
      return true
    },
  }
}
