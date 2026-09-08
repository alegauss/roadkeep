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
 * there. Order is first in, first out — a screen that asked for twenty projects gets them
 * in the order it asked, which is the order it is drawing them.
 */

export interface PoolOptions {
  readonly width: number
}

export function createPooledTransport(inner: Transport, options: PoolOptions): Transport {
  const width = Math.max(1, Math.floor(options.width))
  const waiting: (() => void)[] = []
  let running = 0

  function acquire(): Promise<void> {
    if (running < width) {
      running += 1
      return Promise.resolve()
    }
    return new Promise<void>((admit) => {
      waiting.push(() => {
        running += 1
        admit()
      })
    })
  }

  function release(): void {
    running -= 1
    waiting.shift()?.()
  }

  return {
    async run(request: EngineRequest): Promise<EngineResult> {
      await acquire()
      try {
        // Checked after the wait, not before it. A call cancelled while queued should
        // never start a process, and by the time a slot frees the screen that asked may
        // have redrawn twice.
        if (request.signal?.aborted === true) {
          throw new EngineCallFailed(
            'aborted',
            'the caller cancelled the call while it was waiting for a slot',
            0,
          )
        }
        return await inner.run(request)
      } finally {
        release()
      }
    },
  }
}
