import path from 'node:path'

import type { EditedFile } from '@rk/core'

import { REAL_STAT, type StatAt } from './governed-at'
import { withinRoot } from './root-paths'

/**
 * The files a session's calls say it edited, as the disk has them now (RG244).
 *
 * **Which paths is the session's answer**, read off its own calls by the window; this only asks
 * the filesystem about the ones it was handed, and only under the session's root. The root is
 * the one main started the session in, never a page's, so what a page can have statted is a
 * path inside a project it handed a line from.
 *
 * **A path outside the root is named and never touched.** An agent may write a memory file or
 * a sibling checkout: it comes back as outside, spelled as the call spelled it, with nothing
 * asked of the disk there. The inside test is `withinRoot`, the one `governedAt` keeps.
 *
 * **Shortened here, drawn as answered.** A path under the root comes back relative to it with
 * forward slashes, because which spellings name one file is this platform's question and not a
 * screen's.
 */

/**
 * How many paths one call is answered for. Past it the rest are left out rather than statted: a
 * page names the paths, and a list without a ceiling is as many stats as a page cares to send.
 */
export const EDITED_CEILING = 1000

/** The path under the root, as a screen draws one: relative, with forward slashes. */
function shownUnder(root: string, full: string): string {
  const inside = path.resolve(root)
  return full
    .slice(inside.length)
    .replace(/^[\\/]+/, '')
    .replaceAll('\\', '/')
}

export function editedAt(
  root: string,
  paths: readonly string[],
  stat: StatAt = REAL_STAT,
): EditedFile[] {
  return paths.slice(0, EDITED_CEILING).map((spelled) => {
    const full = withinRoot(root, spelled)
    if (full === null) {
      return { path: spelled, shown: spelled, inside: false, present: false, changed: '' }
    }
    const found = stat(full)
    return {
      path: spelled,
      shown: shownUnder(root, full),
      inside: true,
      present: found !== null,
      changed: found === null ? '' : found.mtime.toISOString(),
    }
  })
}
