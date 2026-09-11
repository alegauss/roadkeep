import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { catalogueFrom, EMPTY_CATALOGUE, type ProjectCatalogue } from '@rk/core'

/**
 * Where the record of what was found lives, and how it is written (RG164).
 *
 * The half that needs an operating system, as `settings-file` is for the settings: `core`
 * says what a record *is* — `reconcile` folds a walk into the one before, `catalogueFrom`
 * reads one back and refuses a shape this build does not know — and this puts it somewhere
 * and gets it back.
 *
 * **`No store of its own` bounds this and does not forbid it.** What this app holds about a
 * backlog is never the truth about it: the repository is. Which folders on this machine hold
 * a governed checkout is not roadkeep's fact at all, and it is the same kind of thing as the
 * roots — a statement about this machine, which this app already owns a file for.
 *
 * **A record that does not read is the empty one, never an error.** A missing file is the
 * first launch; an unreadable one is a list the walk behind it rebuilds. Neither is worth a
 * sentence on a screen, which is why nothing here answers what went wrong.
 *
 * **Written by rename**, as the settings are: a quit mid-write leaves the record that was
 * there rather than half of the next one, and the temporary file is beside the real one so
 * the rename stays on one filesystem.
 */

/** The file, inside whatever directory the caller says is this app's. */
export const CATALOGUE_FILE = 'catalogue.json'

export function cataloguePath(userData: string): string {
  return path.join(userData, CATALOGUE_FILE)
}

/** The record this machine last wrote, or the empty one. */
export function loadCatalogue(userData: string): ProjectCatalogue {
  let text: string
  try {
    text = readFileSync(cataloguePath(userData), 'utf8')
  } catch {
    return EMPTY_CATALOGUE
  }
  return catalogueFrom(text) ?? EMPTY_CATALOGUE
}

/**
 * Write the record.
 *
 * Creates the directory if it is not there — a first launch has neither — and answers
 * whether it landed, so a caller that cares can say; the carrier does not, since a record
 * that could not be written costs the next launch a walk it was going to do anyway.
 */
export function saveCatalogue(userData: string, catalogue: ProjectCatalogue): boolean {
  const target = cataloguePath(userData)
  const temporary = `${target}.writing`
  try {
    mkdirSync(userData, { recursive: true })
    writeFileSync(temporary, `${JSON.stringify(catalogue, null, 2)}\n`, 'utf8')
    renameSync(temporary, target)
    return true
  } catch {
    return false
  }
}
