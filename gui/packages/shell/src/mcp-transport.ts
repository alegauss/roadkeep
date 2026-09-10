import { spawn, type ChildProcess } from 'node:child_process'

import { EngineCallFailed, type EngineRequest, type EngineResult, type Transport } from '@rk/core'

/**
 * The third transport: one engine process per project, kept, spoken to over stdio (RG101).
 *
 * A spawned call against this repository costs about a second and a half and almost all of
 * it is Python starting. `roadkeep mcp` starts once and answers JSON-RPC on stdin and
 * stdout, so a read costs what an in-process read costs — the live suite makes six hundred
 * calls and spends most of ten minutes on interpreter starts alone.
 *
 * **It reads the tool call and never the argv.** Every tool has a schema, so what a call
 * takes is an object with the names that schema publishes. `EngineRequest` carries both
 * spellings for exactly this reason (`tools.ts`), and a request that carries no tool call
 * goes to the fallback — which is what a door's own command line is: an argv the engine
 * composed, that nothing here turned into a tool.
 *
 * **The answer is the same document.** `tools/call` returns the payload as text, and it is
 * what `--json` prints apart from the newline `print` adds — which is what makes this a
 * transport swap rather than a second reader. An answer that is not clean is not translated
 * at all: the CLI splits a refused document from a sentence about the call across two
 * streams and this surface has one field for both, so the call is made again where that
 * distinction survives.
 *
 * **It serves fewer verbs than the CLI, and falls back for the rest.** `stats` and
 * `commands` are reads the tool set does not publish. Asked at the handshake and remembered,
 * so a verb this surface cannot answer goes to the transport that spawns rather than coming
 * back as a refusal the caller cannot act on.
 *
 * **And fewer arguments, which the handshake cannot tell it.** A tool publishes a schema and
 * the schema is narrower than the flags: `brief` takes no `claim` — withheld on purpose,
 * since a read that writes is one a caller stops making freely — and `brief --claim` is the
 * one read this app makes that writes. Nothing at the handshake says so; what says so is the
 * server refusing the call, which is why a refusal is a fall-through and not an answer.
 *
 * **One process per root and no `-C`.** The MCP surface takes no project argument: the
 * server answers about the directory it was started in. So this holds a process per root,
 * starts it on the first call and never on a call it will not serve.
 *
 * **A process that dies is a process that restarts.** It is state this app owns, which is
 * the cost of keeping it; what that buys is that a crash costs one call rather than the
 * session, and every waiting call is failed with the reason rather than left hanging.
 *
 * **A process that merely missed its deadline is not one of those.** A read that ran out is
 * a read that ran out: the server is alive, still holds this project, and answers the next
 * call. Dropping it for that would leave an engine running with nothing holding it and
 * start a second one beside it — measured as two Pythons per project against a one
 * millisecond ceiling, which is what a screen that redrew looks like.
 *
 * **And a handshake that never answers is this surface being absent, not the read failing**
 * (RG122). An engine too old to have `mcp`, or one whose interpreter cannot start, exits
 * before it says anything; every read then goes to the transport that spawns, which is the
 * app working slowly rather than the app not working. Remembered per root, so the cost of
 * learning it is one process start and not one per read.
 */

/** What a server answers with, of which this reads two shapes. */
interface Frame {
  id?: number
  result?: {
    content?: { type?: string; text?: string }[]
    isError?: boolean
    tools?: { name?: string }[]
  }
  error?: { code?: number; message?: string }
}

interface Waiting {
  readonly settle: (frame: Frame) => void
  readonly fail: (cause: Error) => void
  readonly timer: ReturnType<typeof setTimeout> | null
}

export interface McpTransportOptions {
  /** How to start the engine: the command and the arguments before `mcp`. */
  readonly engine: readonly string[]
  /** The transport a request with no tool call goes to. */
  readonly fallback: Transport
  /** How long to wait for a call, when the caller names none. */
  readonly timeoutMs?: number
}

export interface McpTransport extends Transport {
  /**
   * Stop every held process, and wait for each to be gone.
   *
   * Awaited rather than fired off, because a server's working directory is the project: on
   * Windows a killed-but-not-yet-exited process still holds that directory, and the caller
   * after this is often the one removing it. Measured — a fixture teardown a millisecond
   * after `kill` fails with `EPERM`.
   */
  close(): Promise<void>
  /** How many engines are held, which is one per root that has been read. */
  readonly held: number
}

const PROTOCOL = '2024-11-05'

/** One server, its process, and the calls waiting on it. */
class Held {
  private readonly child: ChildProcess
  private readonly waiting = new Map<number, Waiting>()
  private readonly published = new Set<string>()
  private buffer = ''
  private nextId = 0
  private readonly ready: Promise<void>
  private ended: Error | null = null

  constructor(
    engine: readonly string[],
    private readonly root: string,
  ) {
    const [command, ...before] = engine
    this.child = spawn(command ?? '', [...before, 'mcp'], {
      cwd: root,
      stdio: ['pipe', 'pipe', 'pipe'],
      // A server started from an editor terminal inherits `ELECTRON_RUN_AS_NODE`, which is
      // nothing to do with Python — but the engine is resolved the same way everywhere and
      // an environment this app did not choose is one it should not pass on unexamined.
      env: { ...process.env },
    })

    this.child.stdout?.setEncoding('utf8')
    this.child.stdout?.on('data', (chunk: string) => {
      this.take(chunk)
    })
    this.child.on('error', (cause) => {
      this.die(cause)
    })
    this.child.on('exit', (code) => {
      this.die(new Error(`the engine held for ${this.root} exited with ${String(code)}`))
    })

    this.ready = this.handshake()
    // A handshake nobody is waiting on still rejects — a server stopped before its first
    // call, an engine that has no `mcp` — and an unhandled rejection in the main process is
    // the whole app going down for a process that was given back on purpose. The rejection
    // still reaches whoever awaits `ready`; this only says it is expected.
    this.ready.catch(() => {})
  }

  /** Whether the process is gone, as against a call that merely ran out of time. */
  get gone(): boolean {
    return this.ended !== null
  }

  /**
   * The two calls before any tool call: the protocol's own, and the one that says what this
   * server can be asked for.
   *
   * The second is not politeness. The CLI runs verbs this surface does not publish —
   * `stats` and `commands` among the reads — so a transport that assumed otherwise would
   * turn two working reads into refusals for a reason no caller could see. Asked once, at
   * the start, and remembered: the tool set does not change while a process lives.
   */
  private async handshake(): Promise<void> {
    await this.send(
      'initialize',
      {
        protocolVersion: PROTOCOL,
        capabilities: {},
        clientInfo: { name: 'roadkeep-gui', version: '0' },
      },
      30000,
    )
    const listed = await this.send('tools/list', {}, 30000)
    for (const tool of listed.result?.tools ?? []) {
      if (typeof tool.name === 'string') this.published.add(tool.name)
    }
  }

  /** Whether this server publishes a tool, once the handshake has answered. */
  async publishes(tool: string): Promise<boolean> {
    await this.ready
    return this.published.has(tool)
  }

  /** Newline-delimited JSON, which is what the server writes and what it reads. */
  private take(chunk: string): void {
    this.buffer += chunk
    let at = this.buffer.indexOf('\n')
    while (at !== -1) {
      const line = this.buffer.slice(0, at).trim()
      this.buffer = this.buffer.slice(at + 1)
      if (line !== '') this.deliver(line)
      at = this.buffer.indexOf('\n')
    }
  }

  private deliver(line: string): void {
    let frame: Frame
    try {
      frame = JSON.parse(line) as Frame
    } catch {
      // A line that is not a frame is the server saying something to a terminal. Not an
      // answer to anything, and not this transport's to interpret.
      return
    }
    if (frame.id === undefined) return

    const held = this.waiting.get(frame.id)
    if (held === undefined) return
    this.waiting.delete(frame.id)
    if (held.timer !== null) clearTimeout(held.timer)
    held.settle(frame)
  }

  /** Fail every call in flight with the same reason, and refuse the ones after it. */
  private die(cause: Error): void {
    this.ended ??= cause
    for (const held of this.waiting.values()) {
      if (held.timer !== null) clearTimeout(held.timer)
      held.fail(cause)
    }
    this.waiting.clear()
  }

  private send(method: string, params: unknown, timeoutMs: number): Promise<Frame> {
    if (this.ended !== null) return Promise.reject(this.ended)

    const id = (this.nextId += 1)
    return new Promise<Frame>((resolve, reject) => {
      const timer =
        timeoutMs > 0
          ? setTimeout(() => {
              this.waiting.delete(id)
              reject(new Error(`the engine did not answer ${method} within ${String(timeoutMs)}ms`))
            }, timeoutMs)
          : null

      this.waiting.set(id, { settle: resolve, fail: reject, timer })
      this.child.stdin?.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`)
    })
  }

  async call(tool: string, args: Readonly<Record<string, unknown>>, timeoutMs: number) {
    await this.ready
    return this.send('tools/call', { name: tool, arguments: args }, timeoutMs)
  }

  /**
   * Kill it, and answer when the operating system says it is gone.
   *
   * **The tree and not the process, on Windows.** The launcher `execv`s the engine on POSIX,
   * so there is one process and `kill` reaches it. Windows has no image to replace: the
   * launcher spawns the engine and waits, so killing what was spawned here leaves the engine
   * running — with the project as its working directory, which on Windows means the
   * directory cannot be removed. Measured as an `EPERM` in a fixture teardown a moment after
   * a clean `kill`.
   */
  stop(): Promise<void> {
    this.die(new Error('the engine was stopped'))
    if (this.child.exitCode !== null || this.child.signalCode !== null) return Promise.resolve()

    return new Promise<void>((done) => {
      this.child.once('exit', () => {
        done()
      })

      if (process.platform === 'win32' && this.child.pid !== undefined) {
        spawn('taskkill', ['/pid', String(this.child.pid), '/T', '/F'], { stdio: 'ignore' })
        return
      }
      this.child.kill()
    })
  }
}

/** The text a `tools/call` answered with, which is the payload the CLI would have printed. */
function textOf(frame: Frame): string {
  return (frame.result?.content ?? [])
    .filter((part) => part.type === undefined || part.type === 'text')
    .map((part) => part.text ?? '')
    .join('')
}

export function createMcpTransport(options: McpTransportOptions): McpTransport {
  const engines = new Map<string, Held>()
  /** Roots whose engine never got through the handshake. Asked once, not once a read. */
  const unheldable = new Set<string>()
  const ceiling = options.timeoutMs ?? 60000

  const engineFor = (root: string): Held => {
    const held = engines.get(root) ?? new Held(options.engine, root)
    engines.set(root, held)
    return held
  }

  /** The server for this root once it has said it publishes the tool, or null to spawn. */
  const speaking = async (root: string, tool: string): Promise<Held | null> => {
    if (unheldable.has(root)) return null

    const held = engineFor(root)
    try {
      return (await held.publishes(tool)) ? held : null
    } catch {
      // The handshake did not answer, so there is no surface here to speak to — an engine
      // with no `mcp`, an interpreter that could not start, a server that wrote something
      // else. Given back, remembered, and every read for this root spawns from now on.
      engines.delete(root)
      unheldable.add(root)
      await held.stop()
      return null
    }
  }

  return {
    async run(request: EngineRequest): Promise<EngineResult> {
      // A door's own command line, or anything else nobody composed a tool for.
      if (request.call === undefined) return options.fallback.run(request)

      // And a verb this surface does not publish. `stats` and `commands` are two of the
      // reads the CLI runs and the tool set does not carry, so refusing them here would
      // turn a working read into an error for a reason no caller could see.
      const held = await speaking(request.root, request.call.tool)
      if (held === null) return options.fallback.run(request)

      const startedAt = Date.now()
      const elapsed = () => Date.now() - startedAt

      let frame: Frame
      try {
        frame = await held.call(
          request.call.tool,
          request.call.arguments,
          request.timeoutMs ?? ceiling,
        )
      } catch (cause) {
        // A process that is gone is dropped, so the next call starts a new one. One that is
        // still alive is kept: a call that ran past its ceiling is a call that ran past its
        // ceiling, and forgetting the server for it would leave it running with nothing
        // holding it. Either way this call gets the failure, named — not a silent retry,
        // which would hide an engine that cannot start at all behind a loop.
        if (held.gone) engines.delete(request.root)
        const said = cause instanceof Error ? cause.message : String(cause)
        throw new EngineCallFailed(
          said.includes('within') ? 'timeout' : 'unspawnable',
          said,
          elapsed(),
        )
      }

      // **Anything that is not a clean answer is the CLI's.** A protocol error is the server
      // refusing the call — an unknown tool, or an argument its schema does not publish —
      // and `isError` is the tool refusing what the call asked for. Both were reported here
      // as a non-zero exit with the text on stderr, and both then arrived at a reader that
      // could make nothing of them: the CLI keeps a refused *document* on stdout and a
      // sentence about the call on stderr, and this surface has one field for the two.
      //
      // Measured on the one read that writes. `brief --claim` takes the line; the tool
      // publishes `id`, `block`, `designed` and `have`, and answers `claim is declared by
      // this verb and withheld from this surface` — a working read arriving as unreadable.
      // Falling back costs a spawn on the unhappy path and gets the answer every reader in
      // this app was written against, which is the trade this makes deliberately.
      if (frame.error !== undefined || frame.result?.isError === true) {
        return options.fallback.run(request)
      }

      return { code: 0, stdout: textOf(frame), stderr: '', durationMs: elapsed() }
    },

    async close() {
      const stopping = [...engines.values()].map((held) => held.stop())
      engines.clear()
      // A root that could not be held is a fact about a process that no longer exists, so a
      // transport closed and read again asks the engine rather than the last answer.
      unheldable.clear()
      await Promise.all(stopping)
    },

    get held() {
      return engines.size
    },
  }
}
