import { createServer, type Server } from 'node:http'

import type { Transport } from '@rk/core'

/**
 * The other side of the HTTP transport: a handler that runs the argv it was given.
 *
 * This is what a service would be, reduced to the part the seam is about. It is not a
 * product surface and is not meant to become one — no authentication, no rate limit, and
 * it binds to the loopback address only. What it is for is proving that the client above
 * the transport does not care which of the two answered.
 *
 * **It runs whatever argv arrives, against whatever root arrives.** That is exactly the
 * power a real service would have to think hard about, and exactly why this one is a
 * test's: the thing being proved is the shape of the seam, not a deployment.
 */

export interface Handler {
  /** Where it is listening, ready to hand to the transport. */
  readonly url: string
  close(): Promise<void>
}

interface Wire {
  root?: unknown
  argv?: unknown
  timeoutMs?: unknown
}

/**
 * Start a handler in front of a transport.
 *
 * @param behind the transport that actually runs the command — the process one, so the
 *   two paths differ in how the call travels and in nothing else.
 */
export function serveEngine(behind: Transport, host = '127.0.0.1'): Promise<Handler> {
  const server: Server = createServer((request, response) => {
    const chunks: Buffer[] = []
    request.on('data', (chunk: Buffer) => chunks.push(chunk))
    request.on('end', () => {
      void (async () => {
        try {
          const wire = JSON.parse(Buffer.concat(chunks).toString('utf8')) as Wire
          const root = typeof wire.root === 'string' ? wire.root : ''
          const argv = Array.isArray(wire.argv)
            ? wire.argv.filter((one): one is string => typeof one === 'string')
            : []

          const result = await behind.run({
            root,
            argv,
            ...(typeof wire.timeoutMs === 'number' ? { timeoutMs: wire.timeoutMs } : {}),
          })

          response.writeHead(200, { 'content-type': 'application/json' })
          // Every field of the answer and nothing added: a handler that summarised would
          // be a handler the client above could tell apart from a process.
          response.end(JSON.stringify(result))
        } catch (cause) {
          response.writeHead(500, { 'content-type': 'application/json' })
          response.end(JSON.stringify({ said: cause instanceof Error ? cause.message : 'failed' }))
        }
      })()
    })
  })

  return new Promise<Handler>((resolve) => {
    server.listen(0, host, () => {
      const address = server.address()
      const port = typeof address === 'object' && address !== null ? address.port : 0
      resolve({
        url: `http://${host}:${String(port)}`,
        close: () =>
          new Promise<void>((done) => {
            server.close(() => {
              done()
            })
          }),
      })
    })
  })
}
