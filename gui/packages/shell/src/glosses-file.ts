import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { glossesFrom, NOTHING_GLOSSED, type KeptGlosses } from '@rk/core'

/**
 * Where the glosses a machine keeps live (RG287), and how they are written.
 *
 * `readings-file`'s arrangement, beside it and for its reasons: `core` says what a kept gloss is
 * and when it still stands, and this puts them somewhere and gets them back. A file that does
 * not read is nothing kept, never an error — the window asks Claude Code again, which is what it
 * did before anything was kept.
 *
 * **Its own file and not `settings.json`**, whose header says it holds no cached answer: this is
 * a cache, bounded and thrown away without anybody minding. Nothing goes in the project's tree
 * either — a gloss is about somebody's window and not about the backlog.
 *
 * **Written by rename**, as the settings and the record are, so a quit mid-write leaves what was
 * there rather than half of the next one.
 */

export const GLOSSES_FILE = 'glosses.json'

export function glossesPath(userData: string): string {
  return path.join(userData, GLOSSES_FILE)
}

/** What this machine last wrote, or nothing kept. */
export function loadGlosses(userData: string): KeptGlosses {
  let text: string
  try {
    text = readFileSync(glossesPath(userData), 'utf8')
  } catch {
    return NOTHING_GLOSSED
  }
  return glossesFrom(text) ?? NOTHING_GLOSSED
}

/**
 * Write what is kept, answering whether it landed.
 *
 * A write that fails costs the next opening the question it was going to ask anyway, which is
 * why nothing above this treats it as a failure worth saying.
 */
export function saveGlosses(userData: string, glosses: KeptGlosses): boolean {
  const target = glossesPath(userData)
  const temporary = `${target}.writing`
  try {
    mkdirSync(userData, { recursive: true })
    writeFileSync(temporary, `${JSON.stringify(glosses, null, 2)}\n`, 'utf8')
    renameSync(temporary, target)
    return true
  } catch {
    return false
  }
}
