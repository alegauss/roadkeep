import { watch, type FSWatcher } from 'node:fs'
import path from 'node:path'

import type { Watcher } from '@rk/core'

/**
 * Watching source trees, for the dev run that has to rebuild them.
 *
 * A second `Watcher` and not a second watching *policy*: holding a burst and fanning out
 * once is `createWatching`'s, already written and already tested, and a dev loop with its
 * own debounce would be the same rule in two places. What differs is only what a handle
 * covers — the governed watcher opens the directories that hold named files, and this
 * opens whole trees.
 *
 * **Recursive, because a source tree is directories.** `tsc -b` reads everything under
 * `src`, so a change three folders down is a change the build sees and the watch must too.
 * Node supports recursive watches on Windows and macOS natively and on Linux since 20.
 *
 * **Anything under the tree counts.** Filtering to `.ts` would be this file deciding what
 * the compiler reads, and a `tsconfig.json` or a `.json` fixture is a change that matters.
 * The cost of a spurious rebuild is one build; the cost of a missed one is a developer
 * looking at output that does not match their source.
 */

/**
 * How long to hold a burst before rebuilding, in milliseconds.
 *
 * Longer than the governed watcher's, and for a different reason: `tsc -b` writes several
 * files per build, an editor's format-on-save can be two events, and a rebuild costs a
 * second where a redraw costs nothing. Short enough to feel immediate.
 */
export const REBUILD_QUIET_MS = 250

interface Held {
  readonly watchers: readonly FSWatcher[]
}

export function createSourceWatcher(): Watcher {
  const held = new Map<string, Held>()

  return {
    start(root, files, moved) {
      const watchers: FSWatcher[] = []

      for (const tree of new Set(files.map((file) => path.resolve(root, file)))) {
        try {
          const watcher = watch(tree, { persistent: false, recursive: true }, () => {
            moved()
          })
          watcher.on('error', () => {
            // A tree that went away takes its watch with it. Not a crash: the dev run keeps
            // going with whatever else resolved, which is more use than exiting.
          })
          watchers.push(watcher)
        } catch {
          // A directory that is not there. The run watches whatever else resolved.
        }
      }

      held.set(root, { watchers })
    },

    stop(root) {
      const entry = held.get(root)
      if (entry === undefined) return
      held.delete(root)
      for (const watcher of entry.watchers) watcher.close()
    },
  }
}
