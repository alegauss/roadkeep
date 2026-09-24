/**
 * What a dev run does when a source file moves.
 *
 * The renderer hot-reloads and the main process does not, so an edit under `shell` is on
 * screen only after the run is killed and started again. Closing that gap is a rebuild and
 * a restart — and the whole of the difficulty is *when not to do them*.
 *
 * **Never restart into a build that failed.** A broken compile that replaced the running
 * app would swap a readable error for a window that will not open, which is the one outcome
 * worse than the wait this removes.
 *
 * **Never build twice at once.** `tsc -b` writing while another `tsc -b` reads is a build
 * that fails for a reason nobody edited.
 *
 * **Never lose a save.** A file changed while a build was running is a change that build did
 * not see, so it is remembered and the next one starts as soon as this one is done.
 *
 * The policy is here and has no timer, no filesystem and no process in it: the debounce is
 * the watcher's and the building is the shell's. What this owns is the order.
 */

/** Where a run is between one change and the app being back. */
export type ReloadState =
  /** Nothing pending. */
  | 'idle'
  /** A build is running. */
  | 'building'
  /** A build is running and something changed since it started. */
  | 'queued'

export interface ReloadHooks {
  /** Compile. Resolves true where the build succeeded and the app may be replaced. */
  build(): Promise<boolean>
  /** Replace the running app with the one just built. */
  restart(): void
  /** Say what is happening, for whoever is watching the terminal. */
  report?(said: string): void
}

export interface Reloading {
  /** Something under the watched trees moved. Already debounced by the caller. */
  changed(): void
  /** What it is doing, for a test and for anybody who asks. */
  readonly state: ReloadState
  /** How many restarts this run has done, which is the useful thing to print. */
  readonly restarts: number
}

/** What is said on each outcome, in one place so a test asserts the words and not a shape. */
export const REBUILDING = 'a source file changed, rebuilding'
export const RESTARTING = 'build succeeded, restarting the app'
export const HELD = 'build failed, leaving the running app alone'
export const AGAIN = 'something changed while that build ran, going round again'

export function createReloading(hooks: ReloadHooks): Reloading {
  let state: ReloadState = 'idle'
  let restarts = 0

  const say = (said: string) => {
    hooks.report?.(said)
  }

  const run = () => {
    state = 'building'
    say(REBUILDING)

    void hooks.build().then(
      (built) => {
        if (built) {
          restarts += 1
          say(RESTARTING)
          hooks.restart()
        } else {
          // The running app is the last one that compiled, which is more use than a window
          // that will not open.
          say(HELD)
        }
        settle()
      },
      () => {
        // A build that threw rather than exiting non-zero is still a build that failed, and
        // a dev loop that died here would be a dev loop that needs restarting by hand.
        say(HELD)
        settle()
      },
    )
  }

  const settle = () => {
    const queued = state === 'queued'
    state = 'idle'
    if (queued) {
      say(AGAIN)
      run()
    }
  }

  return {
    changed() {
      // A save during a build is remembered rather than dropped or run concurrently.
      if (state === 'idle') run()
      else state = 'queued'
    },
    get state() {
      return state
    },
    get restarts() {
      return restarts
    },
  }
}
