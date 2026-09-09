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
 * transport swap rather than a second reader. An error answer becomes a non-zero exit with
 * the message on stderr, because that is how the CLI says the same thing.
 *
 * **It serves fewer verbs than the CLI, and falls back for the rest.** `stats` and
 * `commands` are reads the tool set does not publish. Asked at the handshake and remembered,
 * so a verb this surface cannot answer goes to the transport that spawns rather than coming
 * back as a refusal the caller cannot act on.
 *
 * **One process per root and no `-C`.** The MCP surface takes no project argument: the
 * server answers about the directory it was started in. So this holds a process per root,
 * starts it on the first call and never on a call it will not serve.
 *
 * **A process that dies is a process that restarts.** It is state this app owns, which is
 * the cost of keeping it; what that buys is that a crash costs one call rather than the
 * session, and every waiting call is failed with the reason rather than left hanging.
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
  private gone: Error | null = null

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
    this.gone ??= cause
    for (const held of this.waiting.values()) {
      if (held.timer !== null) clearTimeout(held.timer)
      held.fail(cause)
    }
    this.waiting.clear()
  }

  private send(method: string, params: unknown, timeoutMs: number): Promise<Frame> {
    if (this.gone !== null) return Promise.reject(this.gone)

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
  const ceiling = options.timeoutMs ?? 60000

  const engineFor = (root: string): Held => {
    const held = engines.get(root) ?? new Held(options.engine, root)
    engines.set(root, held)
    return held
  }

  return {
    async run(request: EngineRequest): Promise<EngineResult> {
      // A door's own command line, or anything else nobody composed a tool for.
      if (request.call === undefined) return options.fallback.run(request)

      // And a verb this surface does not publish. `stats` and `commands` are two of the
      // reads the CLI runs and the tool set does not carry, so refusing them here would
      // turn a working read into an error for a reason no caller could see.
      const held = engineFor(request.root)
      if (!(await held.publishes(request.call.tool))) return options.fallback.run(request)

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
        // The process is gone, so the next call starts a new one. What this call gets is
        // the failure, named — not a silent retry, which would hide an engine that cannot
        // start at all behind a loop.
        engines.delete(request.root)
        const said = cause instanceof Error ? cause.message : String(cause)
        throw new EngineCallFailed(
          said.includes('within') ? 'timeout' : 'unspawnable',
          said,
          elapsed(),
        )
      }

      // A protocol error is the server refusing the call itself — an unknown tool, or
      // arguments its schema would not take. The CLI says that with a non-zero exit and a
      // sentence on stderr, and so does this, because the client above reads the answer.
      if (frame.error !== undefined) {
        return {
          code: 2,
          stdout: '',
          stderr: frame.error.message ?? 'the engine refused the call',
          durationMs: elapsed(),
        }
      }

      // `isError` is the tool's own refusal, which the CLI prints on stderr and exits
      // non-zero for. The text is the engine's whole sentence either way.
      const text = textOf(frame)
      return frame.result?.isError === true
        ? { code: 1, stdout: '', stderr: text, durationMs: elapsed() }
        : { code: 0, stdout: text, stderr: '', durationMs: elapsed() }
    },

    async close() {
      const stopping = [...engines.values()].map((held) => held.stop())
      engines.clear()
      await Promise.all(stopping)
    },

    get held() {
      return engines.size
    },
  }
}
