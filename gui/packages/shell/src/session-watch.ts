import { statSync, watch, type FSWatcher } from 'node:fs'
import path from 'node:path'

import type { MoveSeen } from '@rk/core'

/**
 * The handle half of watching what a session's run changes on disk (RG247).
 *
 * `core` says which moves count, how they fold and how many are kept; this opens one recursive
 * watch on the session's root and reports paths and times. Nothing is read: a name and a clock,
 * never a byte of a file.
 *
 * **Recursive, which is the whole point.** A formatter run through Bash writes anywhere under
 * the project, so a watch per directory would be a walk this app does not do. Recursive
 * `fs.watch` holds on Windows and macOS, and on Linux from the Node this repo requires.
 *
 * **A root that cannot be watched is not a failure.** The section is simply empty: the files an
 * edit call named are still listed, and nothing else about the session changes.
 */

/**
 * The path as a screen reads one: relative to the root, forward slashes, no `./` in front.
 *
 * Here and not in `core`, which has no platform and is held to it (RG65, RG98): a watcher
 * answers in the platform's own spelling, and one spelling is what the policy folds on.
 */
export function spelledMove(name: string): string {
  return name.replaceAll('\\', '/').replace(/^(?:\.\/)+/, '')
}

/** What one stat answered: the three facts a move is read from, in one call. */
interface Stat extends MoveSeen {
  /**
   * Whether this move is a folder's own entry rather than a file's.
   *
   * Writing a file changes its directory too, and a watch reports both — so a list drawn from
   * the raw events names `src` beside `src/a.ts`, which is one fact written twice. A path that
   * is no longer there is not a folder: a deletion is a move, and the file it happened to is
   * what a reader wants named.
   */
  readonly folder: boolean
}

/**
 * One stat per event, answering all three (RG281): folder, still there, and when it was born.
 *
 * It was made already, for the folder question alone. A birth time of zero is a filesystem that
 * keeps none, and is answered as none rather than as the epoch — which would read as a file born
 * long before every session.
 */
function statOf(root: string, spelled: string): Stat {
  try {
    const found = statSync(path.resolve(root, spelled))
    return {
      folder: found.isDirectory(),
      present: true,
      born: found.birthtimeMs > 0 ? found.birthtime.toISOString() : '',
    }
  } catch {
    // Not there: deleted, or renamed away. Both are a move to the file that is gone.
    return { folder: false, present: false, born: '' }
  }
}

export interface SessionWatch {
  /** Give the handle back. Safe to call twice. */
  stop(): void
}

/**
 * Told that something under the root moved: the path as the platform spelled it, when, and what
 * the stat behind it saw (RG281).
 */
export type OnMoved = (path: string, at: string, seen: MoveSeen) => void

export function watchSessionRoot(
  root: string,
  moved: OnMoved,
  now: () => Date = () => new Date(),
): SessionWatch {
  let watcher: FSWatcher | null = null
  try {
    watcher = watch(root, { recursive: true, persistent: false }, (_event, name) => {
      // A change this process cannot attribute to a path is one it cannot list, and there is
      // nothing to re-read: the whole answer here is which path moved.
      if (name === null) return
      const spelled = spelledMove(name)
      const seen = statOf(root, spelled)
      if (seen.folder) return
      moved(spelled, now().toISOString(), { present: seen.present, born: seen.born })
    })
    watcher.on('error', () => {
      // The root went away, or the platform gave the watch up. Whatever was seen stands.
    })
  } catch {
    // No recursive watch here, or no root to watch. Neither stops the session.
  }

  return {
    stop() {
      watcher?.close()
      watcher = null
    },
  }
}
