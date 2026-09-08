import { EngineCallFailed, type EngineRequest, type EngineResult, type Transport } from '@rk/core'

/**
 * The second transport, and the reason the service port is a claim that can fail.
 *
 * The client's transport is one interface, and an interface only one implementation ever
 * uses is one that has quietly grown a dependency on that implementation. This is the
 * other implementation: the same argv, carried over HTTP to a handler that runs it
 * somewhere else, and the same answer handed back.
 *
 * **Not a mock.** A mock returns what the test already decided, which is the one thing
 * that cannot catch a leak. This one really goes over a socket, so a path, a working
 * directory or an exit code that had come to travel by accident stops travelling.
 *
 * **The root goes as data.** A process transport can make it the child's working
 * directory; this one has no child and no directory, so a read that had come to depend on
 * `cwd` answers differently here. That difference is the whole point of running both.
 *
 * **The exit code comes back as a number and is never read as a failure.** `lint` exits 1
 * with an ordinary payload, and a transport treating that as an error would lose an answer
 * the other one keeps.
 */

export interface HttpTransportOptions {
  /** Where the handler is, e.g. `http://127.0.0.1:8791`. */
  readonly url: string
  /** How long to wait before abandoning a call, when the caller names none. */
  readonly timeoutMs?: number
}

/** The wire shape, which is `EngineRequest` and `EngineResult` and nothing added. */
interface WireResult {
  code: number
  stdout: string
  stderr: string
  durationMs: number
}

export function createHttpTransport(options: HttpTransportOptions): Transport {
  return {
    async run(request: EngineRequest): Promise<EngineResult> {
      const startedAt = Date.now()
      const elapsed = () => Date.now() - startedAt
      const ceiling = request.timeoutMs ?? options.timeoutMs ?? 60000

      const abort = new AbortController()
      const timer = setTimeout(() => {
        abort.abort()
      }, ceiling)
      // The caller's cancellation and the deadline are the same act to the socket.
      const stop = () => {
        abort.abort()
      }
      request.signal?.addEventListener('abort', stop)

      try {
        const answer = await fetch(options.url, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          // The root travels here rather than becoming anybody's working directory.
          body: JSON.stringify({ root: request.root, argv: request.argv, timeoutMs: ceiling }),
          signal: abort.signal,
        })

        if (!answer.ok) {
          throw new EngineCallFailed(
            'unspawnable',
            `the handler answered ${String(answer.status)}`,
            elapsed(),
          )
        }

        const wire = (await answer.json()) as WireResult
        return {
          code: wire.code,
          stdout: wire.stdout,
          stderr: wire.stderr,
          durationMs: wire.durationMs,
        }
      } catch (cause) {
        if (cause instanceof EngineCallFailed) throw cause
        const aborted = cause instanceof Error && cause.name === 'AbortError'
        throw new EngineCallFailed(
          aborted && request.signal?.aborted === true ? 'aborted' : aborted ? 'timeout' : 'unspawnable',
          cause instanceof Error ? cause.message : String(cause),
          elapsed(),
        )
      } finally {
        clearTimeout(timer)
        request.signal?.removeEventListener('abort', stop)
      }
    },
  }
}
