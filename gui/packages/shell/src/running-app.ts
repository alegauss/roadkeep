import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { setTimeout as after } from 'node:timers/promises'

import type { ChildProcess } from 'node:child_process'

import { spawnElectron } from './launch'

import { removeTree } from './scratch'

/**
 * The app, running, with a way to ask it questions.
 *
 * The suite asserts the navigation policy as pure functions and the renderer against a
 * stubbed bridge. Neither starts Electron, so neither catches the failures that live in the
 * wiring — a preload path that stopped resolving, `sandbox` dropped from `webPreferences`,
 * a handler on a channel the preload no longer invokes. Every one of those leaves the rest
 * of the suite green.
 *
 * So this starts the built app with a debugging port and talks to the page over the
 * DevTools protocol, which is the only vantage point from which those questions have real
 * answers: `window.roadkeep` is what the preload actually exposed, and `require` is
 * undefined because the sandbox is on and not because a constant says so.
 *
 * **A throwaway profile, and the port it chose.** `--remote-debugging-port=0` lets the
 * runtime pick a free one and write it into `DevToolsActivePort` under the user data
 * directory — which is also why that directory is a fresh temporary one: a test must not
 * read, or leave anything in, the profile a person's own app uses.
 *
 * **Nothing here is shipped.** It is a test's instrument, and it is in `shell` because
 * starting a process is what this package is for.
 */

/** Where the runtime writes the port it chose, under the user data directory. */
const PORT_FILE = 'DevToolsActivePort'

/** How long to wait for the app to open a page and start answering. */
const READY_MS = 30000
const POLL_MS = 100
/** How long to let the app close before giving up on it and on tidying its profile. */
const GOODBYE_MS = 5000

export interface RunningApp {
  /**
   * Evaluate an expression in the page and hand back its value.
   *
   * A thrown expression comes back as a rejection carrying what the page said, because a
   * test that read `undefined` for both *false* and *this threw* would assert nothing.
   */
  evaluate<T>(expression: string): Promise<T>
  /** Everything the renderer printed, which is where a policy violation is reported. */
  readonly console: readonly string[]
  close(): Promise<void>
}

interface Target {
  readonly type: string
  readonly url: string
  readonly webSocketDebuggerUrl?: string
}

/**
 * Wait for the runtime to write the port it bound, or say it never did — and say what it
 * printed on the way (RG114).
 *
 * The refusal is the whole account. A runtime that cannot start says why on stderr — a
 * sandbox it could not enter, a library it could not load — and this is piped, so nothing
 * else is watching that stream. Thrown without it, the sentence below reports thirty
 * seconds of silence from a machine the reader does not have, which is how a Linux-only
 * failure cost a CI cycle before it could even be named.
 */
async function portOf(
  userDataDir: string,
  until: number,
  printed: readonly string[],
): Promise<number> {
  while (Date.now() < until) {
    try {
      // The first line is the port; the second is a path this does not need.
      const first = readFileSync(path.join(userDataDir, PORT_FILE), 'utf8').split('\n')[0] ?? ''
      const port = Number(first.trim())
      if (Number.isInteger(port) && port > 0) return port
    } catch {
      // Not written yet. The app is still starting.
    }
    await after(POLL_MS)
  }
  const said = printed.join('').trim()
  throw new Error(
    `the app never wrote ${PORT_FILE}: it did not start, or it exited first` +
      (said === '' ? ', and it printed nothing' : `. It printed:\n${said}`),
  )
}

/** Wait for a page target with a debugger URL, which is the window's own contents. */
async function pageOf(port: number, until: number): Promise<Target> {
  let last = 'nothing answered'
  while (Date.now() < until) {
    try {
      const answer = await fetch(`http://127.0.0.1:${String(port)}/json/list`)
      const targets = (await answer.json()) as Target[]
      const page = targets.find(
        (target) => target.type === 'page' && target.webSocketDebuggerUrl !== undefined,
      )
      if (page) return page
      last = `${String(targets.length)} target(s), none of them a page`
    } catch (cause) {
      last = cause instanceof Error ? cause.message : String(cause)
    }
    await after(POLL_MS)
  }
  throw new Error(`no page to attach to on port ${String(port)}: ${last}`)
}

interface Frame {
  id?: number
  method?: string
  params?: unknown
  result?: {
    result?: { value?: unknown }
    exceptionDetails?: { exception?: { description?: string }; text?: string }
  }
  error?: { message?: string }
}

/**
 * Start the built app and attach to its page.
 *
 * @param extraEnv variables this run adds. A test that wants the development policy sets
 *   the renderer URL here, exactly as the dev script does.
 * @param seed writes into the throwaway profile before the app starts — a settings file
 *   naming a root, so the window has a project to open (RG143).
 */
export async function startApp(
  extraEnv: Record<string, string> = {},
  seed: (userDataDir: string) => void = () => undefined,
): Promise<RunningApp> {
  const userDataDir = mkdtempSync(path.join(tmpdir(), 'rk-app-'))
  seed(userDataDir)
  const printed: string[] = []

  // Piped rather than inherited: the renderer's console is where a content policy reports
  // a refusal, and `ELECTRON_ENABLE_LOGGING` is what puts it on this stream.
  const child: ChildProcess = spawnElectron(
    { ELECTRON_ENABLE_LOGGING: '1', ...extraEnv },
    ['--remote-debugging-port=0', `--user-data-dir=${userDataDir}`],
    'pipe',
  )
  child.stdout?.on('data', (chunk: Buffer) => printed.push(chunk.toString('utf8')))
  child.stderr?.on('data', (chunk: Buffer) => printed.push(chunk.toString('utf8')))

  /**
   * Stop the app and take its profile with it.
   *
   * The wait is not politeness: on Windows the runtime still holds files under the user
   * data directory at the moment it is killed, and removing it immediately fails with
   * `EPERM`. And a profile that could not be removed is a temporary directory left behind,
   * which is untidy and is not a reason to fail a test — so the removal is attempted, then
   * forgotten.
   */
  const dispose = async (): Promise<void> => {
    if (child.exitCode === null && child.signalCode === null) {
      const stopped = new Promise<void>((resolve) => {
        child.once('exit', () => resolve())
      })
      child.kill()
      await Promise.race([stopped, after(GOODBYE_MS)])
    }

    try {
      removeTree(userDataDir)
    } catch {
      // Still held, or already gone. Either way there is nothing useful to do about it.
    }
  }

  try {
    const until = Date.now() + READY_MS
    const port = await portOf(userDataDir, until, printed)
    const page = await pageOf(port, until)

    const socket = new WebSocket(page.webSocketDebuggerUrl ?? '')
    await new Promise<void>((resolve, reject) => {
      socket.addEventListener('open', () => resolve(), { once: true })
      socket.addEventListener('error', () => reject(new Error('the debugger refused a socket')), {
        once: true,
      })
    })

    let nextId = 0
    const waiting = new Map<number, (frame: Frame) => void>()
    socket.addEventListener('message', (event: MessageEvent) => {
      const frame = JSON.parse(String(event.data)) as Frame
      if (frame.id !== undefined) waiting.get(frame.id)?.(frame)
    })

    const send = (method: string, params: unknown): Promise<Frame> => {
      const id = (nextId += 1)
      return new Promise<Frame>((resolve) => {
        waiting.set(id, (frame) => {
          waiting.delete(id)
          resolve(frame)
        })
        socket.send(JSON.stringify({ id, method, params }))
      })
    }

    const app: RunningApp = {
      async evaluate<T>(expression: string): Promise<T> {
        const frame = await send('Runtime.evaluate', {
          expression,
          awaitPromise: true,
          returnByValue: true,
        })
        if (frame.error) throw new Error(`the debugger refused: ${frame.error.message ?? ''}`)
        const thrown = frame.result?.exceptionDetails
        if (thrown) {
          throw new Error(
            `the page threw: ${thrown.exception?.description ?? thrown.text ?? 'no detail'}`,
          )
        }
        return frame.result?.result?.value as T
      },
      get console() {
        return printed.join('').split('\n')
      },
      async close() {
        // Asked to quit before it is killed (RG143): the engines a window opened are the
        // carrier's, and quitting is what gives them back. A killed app leaves each one
        // standing in its project, which on Windows is a folder nobody can remove. Sent and
        // not awaited — the page that would answer is the one closing.
        if (child.exitCode === null && child.signalCode === null) {
          const quit = new Promise<void>((resolve) => {
            child.once('exit', () => resolve())
          })
          socket.send(
            JSON.stringify({
              id: (nextId += 1),
              method: 'Runtime.evaluate',
              params: { expression: 'window.close()' },
            }),
          )
          await Promise.race([quit, after(GOODBYE_MS)])
        }
        socket.close()
        await dispose()
      },
    }

    // The window is open before the bundle has run. Wait for the page to be the app rather
    // than for it to exist, or every question below races the first paint.
    const settled = Date.now() + READY_MS
    while (Date.now() < settled) {
      const ready = await app.evaluate<boolean>(
        "document.readyState === 'complete' && document.querySelector('#root')?.childElementCount > 0",
      )
      if (ready) return app
      await after(POLL_MS)
    }
    throw new Error('the page loaded but the renderer never drew anything into #root')
  } catch (cause) {
    await dispose()
    throw cause
  }
}
