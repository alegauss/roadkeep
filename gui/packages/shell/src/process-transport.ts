import { spawn } from 'node:child_process'

import {
  EngineCallFailed,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from '@rk/core'

/**
 * The transport that is a process, which is the only kind this app has today.
 *
 * It is in `shell` and not in `core` because it is the piece a web service throws away:
 * `core` states the interface, this implements it with a spawn, and a second
 * implementation over HTTP would sit beside it and change nothing above.
 *
 * Four properties here are not preferences.
 *
 * **No shell.** `shell: false` with argv as an array, because this app puts prose a person
 * typed into those elements and a shell is where quoting defects live. An argument holding
 * `&&`, a quote or a `$(...)` reaches the engine as those characters and never as syntax.
 *
 * **The root is the working directory.** The client also passes `-C`, so an answer is
 * about the project on screen twice over.
 *
 * **Every call is cancellable and bounded.** A screen redraws while reads are in flight,
 * and a portfolio fans out far enough that one engine eventually hangs.
 *
 * **The two streams stay apart.** They are collected into separate buffers and never
 * interleaved, because the engine reports a line it could not accept on stderr with the
 * count — merged, a client cannot tell an answer from a warning about that answer.
 */

export interface ProcessTransportOptions {
  /**
   * The engine, named by the caller. Nothing here reads PATH: which roadkeep answers is a
   * question about provenance, it is RG2's, and a transport that guessed would make the
   * answer depend on the machine.
   */
  readonly command: string
  /** Arguments before the engine's own, e.g. the launcher script a python install needs. */
  readonly prefixArgs?: readonly string[]
}

export function createProcessTransport(options: ProcessTransportOptions): Transport {
  const prefix = options.prefixArgs ?? []

  return {
    run(request: EngineRequest): Promise<EngineResult> {
      return new Promise<EngineResult>((resolve, reject) => {
        const startedAt = Date.now()
        const elapsed = () => Date.now() - startedAt

        const child = spawn(options.command, [...prefix, ...request.argv], {
          cwd: request.root,
          shell: false,
          windowsHide: true,
        })

        const out: Buffer[] = []
        const err: Buffer[] = []
        child.stdout.on('data', (chunk: Buffer) => out.push(chunk))
        child.stderr.on('data', (chunk: Buffer) => err.push(chunk))

        let settled = false
        /** Kill and reject once. Node still emits `close` afterwards; this ignores it. */
        const abandon = (reason: 'timeout' | 'aborted', message: string) => {
          if (settled) return
          settled = true
          cleanUp()
          child.kill()
          reject(new EngineCallFailed(reason, message, elapsed()))
        }

        const timer =
          request.timeoutMs === undefined
            ? undefined
            : setTimeout(
                () => abandon('timeout', `the engine ran past ${String(request.timeoutMs)}ms`),
                request.timeoutMs,
              )

        const onAbort = () => abandon('aborted', 'the caller cancelled the call')

        function cleanUp() {
          if (timer !== undefined) clearTimeout(timer)
          request.signal?.removeEventListener('abort', onAbort)
        }

        if (request.signal?.aborted === true) {
          // Already cancelled before the spawn finished starting. Killing an unstarted
          // child is a no-op, so this has to answer rather than wait for an event that
          // has already been and gone.
          onAbort()
          return
        }
        request.signal?.addEventListener('abort', onAbort)

        child.on('error', (cause: Error) => {
          if (settled) return
          settled = true
          cleanUp()
          reject(
            new EngineCallFailed(
              'unspawnable',
              `${options.command} could not be started: ${cause.message}`,
              elapsed(),
            ),
          )
        })

        child.on('close', (code) => {
          if (settled) return
          settled = true
          cleanUp()
          resolve({
            // A process killed by a signal reports a null code. Nothing killed it here —
            // the two paths that do reject above — so this is the engine ending oddly, and
            // reporting it as 0 would read as success.
            code: code ?? -1,
            stdout: Buffer.concat(out).toString('utf8'),
            stderr: Buffer.concat(err).toString('utf8'),
            durationMs: elapsed(),
          })
        })
      })
    },
  }
}
