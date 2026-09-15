import type { RecordedProject } from './catalogue'
import { readEnginesPayload, type EnginesPayload } from './engines'
import {
  DECLARES_NOTHING,
  readPickPayload,
  readStatsPayload,
  type Declared,
  type PickPayload,
  type StatsPayload,
} from './payloads'
import { readRow, type ProjectRow } from './portfolio'
import { aString, listOf, orMissing, orNull, record, type Parsed, type Reader } from './reading'

/**
 * What a verb printed about a project, kept between launches (RG251).
 *
 * **What is remembered is a payload and never a row.** The numbers a screen draws are the
 * ones `stats` and `pick` printed, and keeping the row instead would be this app composing a
 * fact and then persisting it. A row is rebuilt from these by `readRow`, the same function a
 * fresh read goes through, so `Every number on this screen is one a verb printed` holds of a
 * launch that has asked nothing yet.
 *
 * **A cache and never the truth about a backlog.** The repository is the store; this is an
 * answer somebody already paid three hundred milliseconds of process start for. What makes it
 * safe is that every entry carries the stamp of the files it came off — the same stamp the
 * held transport's cache is keyed on — so an entry whose files have moved is not offered.
 *
 * **Versioned, and refused wholesale where the shape moved.** `catalogueFrom`'s rule: a file
 * this build cannot read is a launch that reads its projects the way it always did, not an
 * error anybody has to see.
 */

/** The shape this build writes and reads. A file at any other version is not read. */
export const READINGS_VERSION = 1

export interface ProjectReading {
  /** The project's root, as the catalogue spells it. */
  readonly root: string
  /**
   * The stamp over the governed files when these answers were read.
   *
   * Empty where nothing stamped them, which is an entry nothing will offer: an answer whose
   * files cannot be checked is an answer that has to be read again.
   */
  readonly stamp: string
  /** When it was read, as an ISO time. What a screen says about how old a row is. */
  readonly read: string
  /** The files `config` named, so the next launch stamps the same set. */
  readonly governed: readonly string[]
  readonly stats: StatsPayload | null
  readonly pick: PickPayload | null
  readonly engines: EnginesPayload | null
  readonly declares: Declared | null
}

export interface RememberedReadings {
  readonly version: number
  readonly projects: readonly ProjectReading[]
}

export const NOTHING_REMEMBERED: RememberedReadings = {
  version: READINGS_VERSION,
  projects: [],
}

export const readProjectReading: Reader<ProjectReading> = record<ProjectReading>({
  root: aString,
  stamp: orMissing(aString, ''),
  read: orMissing(aString, ''),
  governed: orMissing(listOf(aString), []),
  stats: orMissing(orNull(readStatsPayload), null),
  pick: orMissing(orNull(readPickPayload), null),
  engines: orMissing(orNull(readEnginesPayload), null),
  declares: orMissing(
    orNull(
      record<Declared>({
        name: orMissing(aString, ''),
        description: orMissing(aString, ''),
        icon: orMissing(aString, ''),
        logo: orMissing(aString, ''),
      }),
    ),
    null,
  ),
})

export const readReadings: Reader<RememberedReadings> = record<RememberedReadings>({
  version: (value, path) =>
    typeof value === 'number'
      ? { ok: true, value }
      : { ok: false, failure: { path, expected: 'a number', got: String(value) } },
  projects: listOf(readProjectReading),
})

/**
 * Read a file of remembered readings back, or answer nothing.
 *
 * `catalogueFrom`'s shape and its reason: what must not happen is reading one written by
 * another build and drawing it as though this one had asked.
 */
export function readingsFrom(text: string): RememberedReadings | null {
  let source: unknown
  try {
    source = JSON.parse(text)
  } catch {
    return null
  }

  const parsed: Parsed<RememberedReadings> = readReadings(source, '')
  if (!parsed.ok) return null
  if (parsed.value.version !== READINGS_VERSION) return null
  return parsed.value
}

/** One project's remembered answers, by the key the caller compares roots on. */
export function readingOf(
  readings: RememberedReadings,
  root: string,
  keyOf: (path: string) => string = (path) => path,
): ProjectReading | null {
  const wanted = keyOf(root)
  return readings.projects.find((one) => keyOf(one.root) === wanted) ?? null
}

/**
 * Fold one project's answers into what is remembered, replacing whatever it held.
 *
 * Per project and not per read: `stats` and `pick` arrive separately, so an entry keeps what
 * it had for the half that did not arrive this time. An entry with a new stamp drops both,
 * because they were read off files that have since moved.
 */
export function remembering(
  readings: RememberedReadings,
  reading: ProjectReading,
  keyOf: (path: string) => string = (path) => path,
): RememberedReadings {
  const wanted = keyOf(reading.root)
  const was = readings.projects.find((one) => keyOf(one.root) === wanted) ?? null
  const kept = was === null || was.stamp !== reading.stamp ? null : was
  const folded: ProjectReading = {
    ...reading,
    stats: reading.stats ?? kept?.stats ?? null,
    pick: reading.pick ?? kept?.pick ?? null,
    engines: reading.engines ?? kept?.engines ?? null,
    declares: reading.declares ?? kept?.declares ?? null,
  }
  return {
    version: READINGS_VERSION,
    projects: [...readings.projects.filter((one) => keyOf(one.root) !== wanted), folded],
  }
}

/**
 * The row a remembered reading draws (RG251).
 *
 * `readRow`'s answer with the state moved: every field on it is one a verb printed, and what
 * the row says about itself is that these numbers are the ones a launch found rather than the
 * ones it just asked for. The cold start running behind it replaces it in place (RG248).
 */
export function rememberedRow(project: RecordedProject, reading: ProjectReading): ProjectRow {
  const row = readRow(project, {
    stats: reading.stats,
    pick: reading.pick,
    engines: reading.engines,
    declares: reading.declares ?? DECLARES_NOTHING,
  })
  return { ...row, state: 'remembered', read: reading.read }
}
