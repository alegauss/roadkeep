import { createLimiter } from './limiting'
import {
  EngineCallFailed,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from './transport'

/**
 * A fixed number of calls in flight, and no more.
 *
 * A portfolio read fans out over every project on the machine, and each call is a Python
 * interpreter. A hundred candidates must never become a hundred processes: that is not
 * slow, it is a machine that stops responding. So the calls go through a pool, and the
 * width is a setting because four cores and thirty-two are different machines.
 *
 * It is a transport wrapping a transport, like the cache, so nothing above knows it is
 * there. The counting is `limiting.ts`'s, which a scan needs for the same reason against a
 * different resource; what is here is the one thing that is a transport's — a call
 * cancelled while it waited must not become a process.
 */

export interface PoolOptions {
  readonly width: number
}

export function createPooledTransport(inner: Transport, options: PoolOptions): Transport {
  const limiter = createLimiter(options.width)

  return {
    run(request: EngineRequest): Promise<EngineResult> {
      return limiter.hold(() => {
        // Checked after the wait, not before it. A call cancelled while queued should
        // never start a process, and by the time a slot frees the screen that asked may
        // have redrawn twice.
        if (request.signal?.aborted === true) {
          return Promise.reject(
            new EngineCallFailed(
              'aborted',
              'the caller cancelled the call while it was waiting for a slot',
              0,
            ),
          )
        }
        return inner.run(request)
      })
    },
  }
}
