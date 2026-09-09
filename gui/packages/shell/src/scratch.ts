import { rmSync } from 'node:fs'

/**
 * Removing a directory this suite made, on a filesystem that may not be ready to (RG104).
 *
 * Forty-one live files ran and one reported failure: every test in it passed and its
 * `afterAll` threw `EPERM` removing the temp directory its fixture built. The next run of
 * the same file was green and nothing in it had changed.
 *
 * **`force` does not cover this.** It forgives a path that is not there — not one Windows
 * will not let go of yet. A directory a process had as its working directory a moment ago,
 * or one an indexer has just opened, is still held when the last test returns, and a
 * removal that would have worked a second later throws instead.
 *
 * **Retrying is the fix and swallowing is not.** Catching the error instead would trade a
 * red run for temp directories nothing removes, which is a leak nobody sees rather than a
 * failure somebody does.
 *
 * **And the retry is here rather than `rmSync`'s own.** Node documents `maxRetries` and
 * `retryDelay` as the answer to `EBUSY`, `ENOTEMPTY` and `EPERM`, and passing them was the
 * first thing tried — measured against a child process standing in the directory, it threw
 * in twenty-four milliseconds without waiting once. So the loop is written out, where it
 * can be seen and where `scratch-live.test.ts` can hold it against a real lock.
 *
 * A second's worth of attempts: long enough for a handle the operating system is already
 * closing, short enough that a directory genuinely held still fails the run rather than
 * hanging it.
 */

/** How many times, and how long between. Ten tries a hundred milliseconds apart. */
export const REMOVE_TRIES = 10
export const REMOVE_WAIT_MS = 100

/** The three ways Windows says *not yet*, as against the ways it says *never*. */
const NOT_YET = /EPERM|EBUSY|ENOTEMPTY/

function heldStill(cause: unknown): boolean {
  const code = (cause as { code?: unknown } | null)?.code
  if (typeof code === 'string' && NOT_YET.test(code)) return true
  // Node's own rimraf throws `EPERM, Permission denied: <path>` with no `code` on it, which
  // is the shape this was measured against.
  return cause instanceof Error && NOT_YET.test(cause.message)
}

/**
 * Wait without yielding.
 *
 * A teardown is synchronous and so is `rmSync`, so a timer would not fire until after the
 * work that is waiting for it. `Atomics.wait` on a buffer nobody notifies is the sleep that
 * blocks, which is what is wanted here and almost nowhere else.
 */
function pause(ms: number): void {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

export function removeTree(target: string): void {
  for (let attempt = 0; ; attempt += 1) {
    try {
      rmSync(target, { recursive: true, force: true })
      return
    } catch (cause) {
      if (attempt >= REMOVE_TRIES || !heldStill(cause)) throw cause
      pause(REMOVE_WAIT_MS)
    }
  }
}
