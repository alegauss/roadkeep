import { stat } from 'node:fs/promises'
import path from 'node:path'

import type { ScanRoot } from '@rk/core'

import { probing } from './probing'

/**
 * The half of a root that needs a platform.
 *
 * `core` has neither a filesystem nor a platform in scope, so which two paths are the same
 * folder — and whether one contains another — is answered here and handed in. Windows is
 * the reason it cannot be answered anywhere else: `D:\Git` and `d:/git` are one folder
 * there and two everywhere else.
 */

/** Whether two spellings differing only in case name one file here. Stated once, used twice. */
export const CASE_INSENSITIVE = process.platform === 'win32' || process.platform === 'darwin'

/**
 * The string two roots are compared on. Resolved to absolute, separators normalised, and
 * lower-cased where the platform says case does not distinguish a folder.
 */
export function rootKey(candidate: string): string {
  const resolved = path.resolve(candidate)
  return CASE_INSENSITIVE ? resolved.toLowerCase() : resolved
}

/**
 * A path resolved against a root, or null where it lands outside it (RG153, RG244).
 *
 * The one inside test the side with the disk keeps: a governed file's path comes from the
 * project's config and an edited file's from a session's call, and neither is statted where it
 * leads out of the project. Compared as `rootKey` compares, so `d:\git\x\a.ts` is under
 * `D:\Git\x` on the platforms where it is the same file.
 */
export function withinRoot(root: string, spelled: string): string | null {
  const inside = path.resolve(root)
  const full = path.resolve(inside, spelled)
  const key = (one: string): string => (CASE_INSENSITIVE ? one.toLowerCase() : one)
  const prefix = inside.endsWith(path.sep) ? inside : `${inside}${path.sep}`
  return key(full) === key(inside) || key(full).startsWith(key(prefix)) ? full : null
}

/**
 * Whether the folder is there now. Anything that is not a directory is not a root.
 *
 * Asynchronous and bounded since RG102: this is asked once per declared root, in the
 * process the window's IPC goes through, and a sleeping drive answering a `statSync` is
 * that window not repainting.
 */
export async function rootExists(candidate: string): Promise<boolean> {
  return probing(async () => {
    try {
      return (await stat(path.resolve(candidate))).isDirectory()
    } catch {
      return false
    }
  })
}

/**
 * Whether `inner` sits inside `outer` within its declared depth.
 *
 * The depth is what makes this a question about the root rather than about the two paths:
 * a folder six levels down is not covered by a root that only looks two.
 */
export function rootContains(outer: ScanRoot, inner: string): boolean {
  const from = rootKey(outer.path)
  const to = rootKey(inner)
  if (from === to) return true

  const relative = path.relative(from, to)
  if (relative === '' || relative.startsWith('..') || path.isAbsolute(relative)) return false

  return relative.split(path.sep).length <= outer.depth
}
