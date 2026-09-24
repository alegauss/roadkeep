import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { NOTHING_REMEMBERED, readingsFrom, type RememberedReadings } from '@rk/core'

/**
 * Where what a verb printed is kept between launches (RG251), and how it is written.
 *
 * `catalogue-file`'s arrangement, beside it and for the same reasons: `core` says what a
 * remembered reading *is* and refuses a shape this build does not know, and this puts it
 * somewhere and gets it back. A file that does not read is nothing remembered, never an
 * error — the launch behind it reads every project the way it always did.
 *
 * **Written by rename**, as the settings and the record are, so a quit mid-write leaves what
 * was there rather than half of the next one.
 */

export const READINGS_FILE = 'readings.json'

export function readingsPath(userData: string): string {
  return path.join(userData, READINGS_FILE)
}

/** What this machine last wrote, or nothing remembered. */
export function loadReadings(userData: string): RememberedReadings {
  let text: string
  try {
    text = readFileSync(readingsPath(userData), 'utf8')
  } catch {
    return NOTHING_REMEMBERED
  }
  return readingsFrom(text) ?? NOTHING_REMEMBERED
}

/**
 * Write what is remembered, answering whether it landed.
 *
 * A write that fails costs the next launch the reads it was going to make anyway, which is
 * why nothing above this treats it as a failure worth saying.
 */
export function saveReadings(userData: string, readings: RememberedReadings): boolean {
  const target = readingsPath(userData)
  const temporary = `${target}.writing`
  try {
    mkdirSync(userData, { recursive: true })
    writeFileSync(temporary, `${JSON.stringify(readings, null, 2)}\n`, 'utf8')
    renameSync(temporary, target)
    return true
  } catch {
    return false
  }
}
