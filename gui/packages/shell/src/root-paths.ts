import { statSync } from 'node:fs'
import path from 'node:path'

import type { ScanRoot } from '@rk/core'

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

/** Whether the folder is there now. Anything that is not a directory is not a root. */
export function rootExists(candidate: string): boolean {
  try {
    return statSync(path.resolve(candidate)).isDirectory()
  } catch {
    return false
  }
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
