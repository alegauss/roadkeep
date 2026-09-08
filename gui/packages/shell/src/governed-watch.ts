import { watch, type FSWatcher } from 'node:fs'
import path from 'node:path'

import type { Clock, Watcher } from '@rk/core'

/**
 * The half of watching that needs a filesystem.
 *
 * `core` says what watching means — which files, how a burst is held, who is told — and
 * this opens the handles. The seam is the transport's again: a fake `Watcher` drives the
 * whole policy in a test without a disk.
 *
 * **A governed file that is not there is still watched**, by watching the directory it
 * would be in. A project whose deferred store has never been written is the ordinary case,
 * and the moment `defer` creates it is exactly the moment a screen needs telling.
 *
 * **Nothing here decides what a change means.** It reports that something under the watched
 * set moved; whether that matters is answered by re-reading, and the cache is keyed on a
 * stamp of the same files.
 */

/**
 * The clock `core` states and cannot implement, because it has no timer in scope.
 *
 * `unref` so a held burst never keeps the process alive: a window closing while a redraw
 * was pending should close.
 */
export const REAL_CLOCK: Clock = {
  after(ms, run) {
    const handle = setTimeout(run, ms)
    handle.unref?.()
    return () => {
      clearTimeout(handle)
    }
  },
}

interface Held {
  readonly watchers: readonly FSWatcher[]
}

export function createGovernedWatcher(): Watcher {
  const held = new Map<string, Held>()

  return {
    start(root, files, moved) {
      const watchers: FSWatcher[] = []
      // Directories rather than files: a file that does not exist yet cannot be watched,
      // and an editor that writes by rename replaces the inode a file watch was holding.
      const directories = new Set(
        files.map((file) => path.dirname(path.resolve(root, file))),
      )
      const wanted = new Set(files.map((file) => path.basename(file)))

      for (const directory of directories) {
        try {
          const watcher = watch(directory, { persistent: false }, (_event, name) => {
            // `name` can be null on some platforms; a change we cannot attribute is still
            // a change, and the cost of announcing it is one read.
            if (name === null || wanted.has(path.basename(String(name)))) moved()
          })
          watcher.on('error', () => {
            // A directory that goes away takes its watch with it. Not a crash: the project
            // is simply no longer watchable, and the next read says so.
          })
          watchers.push(watcher)
        } catch {
          // A directory that is not there yet. The project is watched by whatever other
          // directories resolved, and a read is what finds the rest.
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
