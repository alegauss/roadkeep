import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { NOTHING_WALKED, walkthroughsFrom, type KeptWalkthroughs } from '@rk/core'

/**
 * Where the walkthroughs a machine keeps live (RG292), and how they are written.
 *
 * `glosses-file`'s arrangement, beside it and for its reasons: `core` says what a kept
 * walkthrough is and when it still stands, and this puts them somewhere and gets them back. A
 * file that does not read is nothing kept, never an error — the window asks Claude Code again,
 * which is what it did before anything was kept.
 *
 * **Its own file and not the glosses'.** Two questions with different keys, different staleness
 * and different bounds; one file would make the bound on either of them a number about both.
 *
 * **Written by rename**, as the glosses and the settings are, so a quit mid-write leaves what was
 * there rather than half of the next one.
 */

export const WALKTHROUGHS_FILE = 'walkthroughs.json'

export function walkthroughsPath(userData: string): string {
  return path.join(userData, WALKTHROUGHS_FILE)
}

/** What this machine last wrote, or nothing kept. */
export function loadWalkthroughs(userData: string): KeptWalkthroughs {
  let text: string
  try {
    text = readFileSync(walkthroughsPath(userData), 'utf8')
  } catch {
    return NOTHING_WALKED
  }
  return walkthroughsFrom(text) ?? NOTHING_WALKED
}

/**
 * Write what is kept, answering whether it landed.
 *
 * A write that fails costs the next opening the question it was going to ask anyway, which is
 * why nothing above this treats it as a failure worth saying.
 */
export function saveWalkthroughs(userData: string, walkthroughs: KeptWalkthroughs): boolean {
  const target = walkthroughsPath(userData)
  const temporary = `${target}.writing`
  try {
    mkdirSync(userData, { recursive: true })
    writeFileSync(temporary, `${JSON.stringify(walkthroughs, null, 2)}\n`, 'utf8')
    renameSync(temporary, target)
    return true
  } catch {
    return false
  }
}
