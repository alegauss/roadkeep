import { statSync } from 'node:fs'
import path from 'node:path'

import type { GovernedFile } from '@rk/core'

/**
 * When each governed file last changed, as the disk says (RG153).
 *
 * **Which files are governed is the project's answer**, read off the opening and never a name
 * written here; this only asks the filesystem about the paths it was handed. A path is
 * resolved against the root because a config spells them relative to it, and one that resolves
 * outside the root is refused: the roles come from the project's own config, and a config that
 * pointed elsewhere would have this process stat a path nobody in the window chose.
 *
 * A file that is not there is a state and not an error — a project has a role before anything
 * has written it — so it comes back present-false with no time rather than dropped.
 */

/** What the disk is asked, so a test answers without one. */
export type StatAt = (file: string) => { readonly mtime: Date } | null

export const REAL_STAT: StatAt = (file) => {
  try {
    return statSync(file)
  } catch {
    // Missing, or a path this process may not read. Both are "not there to a reader".
    return null
  }
}

export function governedAt(
  root: string,
  governed: Readonly<Record<string, string>>,
  stat: StatAt = REAL_STAT,
): GovernedFile[] {
  const inside = path.resolve(root)

  return Object.entries(governed).map(([role, spelled]) => {
    const full = path.resolve(inside, spelled)
    const within = full === inside || full.startsWith(`${inside}${path.sep}`)
    const found = within ? stat(full) : null
    return {
      role,
      path: spelled,
      changed: found === null ? '' : found.mtime.toISOString(),
      present: found !== null,
    }
  })
}
