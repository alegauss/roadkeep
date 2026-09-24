/**
 * How many of something may be happening at once.
 *
 * Two things in this package fan out over a machine and both need the same answer. A
 * portfolio read starts a Python interpreter per project, and a hundred candidates must
 * never become a hundred processes. A scan reads a directory per node, and a hundred open
 * handles against a network share is the same failure with a different resource.
 *
 * So the counting is here and the thing being counted is the caller's. First in, first
 * out: a caller that asked for twenty things gets them in the order it asked, which is the
 * order it is drawing them.
 */

/** Take a slot, and the function that gives it back. Always release, whatever happened. */
export interface Limiter {
  hold<T>(work: () => Promise<T>): Promise<T>
}

export function createLimiter(width: number): Limiter {
  const most = Math.max(1, Math.floor(width))
  const waiting: (() => void)[] = []
  let running = 0

  function acquire(): Promise<void> {
    if (running < most) {
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
    async hold<T>(work: () => Promise<T>): Promise<T> {
      await acquire()
      try {
        return await work()
      } finally {
        release()
      }
    },
  }
}
