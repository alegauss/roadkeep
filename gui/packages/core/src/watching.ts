/**
 * What to watch, and who is told.
 *
 * The config declares every governed role, so what to watch is read and never guessed:
 * those files per project, plus the config itself — editing it changes *which* files are
 * governed, and a watch that missed that would be watching the wrong set.
 *
 * **One path to a redraw.** A write this app made is watched like one a terminal or an
 * agent made, so nothing calls the cache on its own behalf. A special case there is a case
 * that goes out of step, and the bug would only ever show up for somebody else's session.
 *
 * **A transaction is one change.** `ship` writes three files at once and an editor saves in
 * two events, so raw notifications are held for a quiet moment and fan out once.
 *
 * **A handle has a cost**, so interest is explicit: a project is watched while a screen
 * holds it or a session runs against it, and the handles close when the last interest goes.
 *
 * **What a change means is not decided here.** The event says which project moved; expiring
 * that project's cached reads is the caller's, and the cache is keyed on a stamp of these
 * same files — so a watch that fired spuriously costs a read and never a wrong answer.
 */

/**
 * The config file, watched alongside the governed set.
 *
 * The same constant the stamp uses and for the same reason: it decides which files are
 * governed, so a change to it changes the set itself.
 */
export const CONFIG_FILE = 'roadkeep.toml'

/**
 * What to watch for one project, given what `config` said it governs.
 *
 * Sorted and deduplicated so two callers asking the same question get the same list, and
 * the config is in it whether or not the engine named it among the roles.
 */
export function watchedFiles(governed: readonly string[]): string[] {
  return [...new Set([CONFIG_FILE, ...governed])].sort()
}

/** Told when a project's governed files move. */
export type OnChanged = (root: string) => void

/** One path that moved on disk while a session ran (RG247). */
export interface MovedPath {
  /**
   * Relative to the session's root, spelled the way a screen reads one. How a path is spelled
   * is the shell's (RG65, RG98): this keeps what it was handed and never folds a separator.
   */
  readonly path: string
  /** When it first moved, and the last time it did, as ISO times. */
  readonly first: string
  readonly last: string
  /** How many events were folded into it. */
  readonly moves: number
}

/**
 * Folders never counted as a session's work, whatever the settings say (RG247).
 *
 * `.git` writes on every command git runs, including the ones a person runs in another window,
 * and a list that reported it would be a list nobody reads.
 */
export const NEVER_MOVED: readonly string[] = ['.git']

/**
 * How many moved paths one session keeps.
 *
 * A generator or an install can touch thousands, and a list that long is neither read nor
 * carried across the bridge cheaply. Past it the count stands in for the rest, which is the
 * fact a reader needs: something wrote a great deal more.
 */
export const MOVED_CEILING = 500

export interface SessionMoves {
  /** Take one move, at one time. A path under a skipped folder is not a move. */
  moved(path: string, at: string): void
  /** The paths so far, in the order each first moved. */
  readonly paths: readonly MovedPath[]
  /** How many paths were left out at the ceiling. */
  readonly beyond: number
}

/**
 * What moved on disk while one session ran, folded by path (RG247).
 *
 * **The policy, not the handle.** Which moves count — the skip list the walk already uses,
 * `.git` always — how they fold, and the ceiling past which a count stands in for the rest.
 * The recursive watch itself is the shell's, so this is driven by a fake in a test.
 *
 * Paths and times only, never contents: what a session's run did, gone with the process.
 *
 * @param skip folder names to leave out, as the settings spell them for the walk
 */
export function sessionMoves(skip: readonly string[] = []): SessionMoves {
  const left = new Set([...NEVER_MOVED, ...skip].filter((name) => name !== ''))
  const byPath = new Map<string, MovedPath>()
  let beyond = 0

  return {
    moved(spelled, at) {
      // Segments as the side with the filesystem spelled them: which folder a path is under is
      // a question about names, and how a path is written is not this package's (RG65, RG98).
      if (spelled === '' || spelled.split('/').some((segment) => left.has(segment))) return
      const was = byPath.get(spelled)
      if (was === undefined && byPath.size >= MOVED_CEILING) {
        beyond += 1
        return
      }
      byPath.set(spelled, {
        path: spelled,
        first: was?.first ?? at,
        last: at,
        moves: (was?.moves ?? 0) + 1,
      })
    },

    get paths() {
      return [...byPath.values()]
    },

    get beyond() {
      return beyond
    },
  }
}

/** How long to hold a burst before fanning out, in milliseconds. */
export const QUIET_MS = 120

/**
 * How long a session's moved paths are held before they are told, in milliseconds (RG247).
 *
 * Longer than the governed set's: `npm run format` writes hundreds of files over a second or
 * two, and every event carries the whole folded list, so holding longer costs a reader nothing
 * and saves a window a redraw per file.
 */
export const MOVES_QUIET_MS = 400

export interface Interest {
  /** Give it up. Safe to call twice; the handles close when the last one goes. */
  release(): void
}

export interface Watching {
  /**
   * Watch a project while somebody is interested in it.
   *
   * Interest is counted, so two screens on one project share the handles and the second
   * release is what closes them.
   */
  hold(root: string, files: readonly string[]): Interest
  /** Be told when any watched project moves. Returns the way to stop being told. */
  onChanged(listener: OnChanged): () => void
  /** The projects held right now, for a screen that reports what it is watching. */
  readonly held: readonly string[]
}

/**
 * What a `Watching` needs from a filesystem, stated so `core` never has one.
 *
 * The same seam as the transport: this package says what watching means and `shell`
 * implements it, which is what lets the whole thing be driven by a fake in a test.
 */
export interface Watcher {
  /** Start watching these absolute-or-relative paths under `root`. */
  start(root: string, files: readonly string[], moved: () => void): void
  /** Stop watching one project and release its handles. */
  stop(root: string): void
}

/**
 * How the burst is held.
 *
 * An interface and not an implementation, for the reason the transport is: this package
 * has no timer in scope any more than it has a filesystem. `shell` supplies the real one
 * and a test supplies one it drives by hand, so nothing here waits on a clock.
 */
export interface Clock {
  /** Run after `ms`, returning the way to call it off. */
  after(ms: number, run: () => void): () => void
}

interface Watched {
  count: number
  cancel: (() => void) | null
}

export function createWatching(
  watcher: Watcher,
  clock: Clock,
  quietMs: number = QUIET_MS,
): Watching {
  const watched = new Map<string, Watched>()
  const listeners = new Set<OnChanged>()

  const announce = (root: string) => {
    const entry = watched.get(root)
    if (entry === undefined) return
    // Hold the burst: `ship` writes three files at once, and told per file a screen would
    // redraw three times and read a half-written backlog twice.
    entry.cancel?.()
    entry.cancel = clock.after(quietMs, () => {
      const still = watched.get(root)
      if (still === undefined) return
      still.cancel = null
      for (const listener of [...listeners]) listener(root)
    })
  }

  return {
    hold(root, files) {
      const entry = watched.get(root)
      if (entry === undefined) {
        watched.set(root, { count: 1, cancel: null })
        watcher.start(root, files, () => {
          announce(root)
        })
      } else {
        entry.count += 1
      }

      let released = false
      return {
        release() {
          if (released) return
          released = true
          const held = watched.get(root)
          if (held === undefined) return
          held.count -= 1
          if (held.count > 0) return
          held.cancel?.()
          watched.delete(root)
          watcher.stop(root)
        },
      }
    },

    onChanged(listener) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
      }
    },

    get held() {
      return [...watched.keys()]
    },
  }
}
