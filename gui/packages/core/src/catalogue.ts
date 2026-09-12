import type { ProjectFamily } from './families'
import {
  aString,
  listOf,
  aNumber,
  orMissing,
  orNull,
  record,
  type Parsed,
  type Reader,
} from './reading'
import type { KeyOf, ScanRoot } from './roots'

/**
 * The project list, kept between launches.
 *
 * A scan is a statement about one machine and it changes rarely. Walking the whole tree
 * again before drawing anything means the first screen is empty for as long as the disk
 * takes, every time, to rediscover a list the person already approved. So the record is
 * drawn immediately and the rescan happens behind it — which makes a rescan a diff rather
 * than a rebuild, and makes the diff the thing worth getting right.
 *
 * **A project the rescan no longer finds is marked missing and kept.** Deleted and
 * not-mounted look identical from here and only one of them is a removal, so this app does
 * not get to decide which happened. `confirmed` stops moving for a missing project, which
 * is what lets a screen say *last seen on Tuesday* instead of implying it is still there.
 *
 * **The order is the record's**, with new projects appended. A list that reordered itself
 * on every launch would be worse than a slow one: the thing somebody clicked yesterday
 * would be somewhere else today, for no reason they could see.
 *
 * "No store of its own" bounds this and does not forbid it. What that refuses is a second
 * copy of roadkeep's data — a backlog cached here would be one, and this app reads those
 * files every time instead. Which folders on this machine hold a governed checkout is not
 * roadkeep's fact and no repository could hold it; it is the same kind of thing as the
 * roots, which this app owns rather than reads.
 */

export interface RecordedProject {
  readonly path: string
  /** Other names for the same folder — a junction, a symlink. */
  readonly aliases: readonly string[]
  /** The git directory its family shares, or null where it is not a worktree. */
  readonly commonDir: string | null
  /**
   * Which branch this checkout is on (RG199), a short sha where detached, empty where it is
   * not a checkout at all. Recorded so a row can say which member of a family it is —
   * a declared name is one word for a whole repository.
   */
  readonly branch: string
  /** The root it was found under. */
  readonly root: string
  /** When a scan last actually saw it. Stops moving once it goes missing. */
  readonly confirmed: string
  readonly presence: 'present' | 'missing'
}

export interface ProjectCatalogue {
  /** A version on the record itself, so an older shape is refused rather than misread. */
  readonly version: number
  /** The roots that produced this list. */
  readonly roots: readonly ScanRoot[]
  readonly projects: readonly RecordedProject[]
}

export const CATALOGUE_VERSION = 1

export const EMPTY_CATALOGUE: ProjectCatalogue = {
  version: CATALOGUE_VERSION,
  roots: [],
  projects: [],
}

export type ChangeKind =
  /** Not in the record at all. */
  | 'added'
  /** In the record as missing, and found again. */
  | 'returned'
  /** In the record as present, and not found. */
  | 'missing'

export interface CatalogueChange {
  readonly kind: ChangeKind
  readonly path: string
}

export interface Reconciled {
  readonly catalogue: ProjectCatalogue
  /** What the rescan actually changed. Empty means the record was already right. */
  readonly changes: readonly CatalogueChange[]
}

/** Flatten the families a scan produced into the rows a record holds. */
export function rowsFrom(
  families: readonly ProjectFamily[],
  rootOf: (path: string) => string,
  now: string,
): RecordedProject[] {
  return families.flatMap((family) =>
    family.members.map((member) => ({
      path: member.path,
      aliases: member.aliases,
      commonDir: family.commonDir,
      branch: member.branch,
      root: rootOf(member.path),
      confirmed: now,
      presence: 'present' as const,
    })),
  )
}

/**
 * Fold a fresh scan into the record.
 *
 * @param now an ISO timestamp, passed in rather than read, so a test can say when.
 */
export function reconcile(
  previous: ProjectCatalogue,
  roots: readonly ScanRoot[],
  scanned: readonly RecordedProject[],
  keyOf: KeyOf,
  now: string,
): Reconciled {
  const fresh = new Map(scanned.map((project) => [keyOf(project.path), project]))
  const changes: CatalogueChange[] = []
  const projects: RecordedProject[] = []
  const kept = new Set<string>()

  for (const held of previous.projects) {
    const key = keyOf(held.path)
    kept.add(key)
    const found = fresh.get(key)

    if (found === undefined) {
      if (held.presence === 'present') changes.push({ kind: 'missing', path: held.path })
      // `confirmed` is deliberately not moved: it is when this was last actually seen.
      projects.push({ ...held, presence: 'missing' })
      continue
    }

    if (held.presence === 'missing') changes.push({ kind: 'returned', path: found.path })
    projects.push({ ...found, confirmed: now })
  }

  for (const [key, found] of fresh) {
    if (kept.has(key)) continue
    changes.push({ kind: 'added', path: found.path })
    projects.push({ ...found, confirmed: now })
  }

  return { catalogue: { version: CATALOGUE_VERSION, roots, projects }, changes }
}

/** The projects worth reading right now. The missing ones are still on the list. */
export function present(catalogue: ProjectCatalogue): RecordedProject[] {
  return catalogue.projects.filter((project) => project.presence === 'present')
}

const readRecordedProject: Reader<RecordedProject> = record<RecordedProject>({
  path: aString,
  aliases: orMissing(listOf(aString), []),
  commonDir: orMissing(orNull(aString), null),
  // Missing on a catalogue written before this was recorded, which is a project whose
  // branch is simply not known yet rather than one with none.
  branch: orMissing(aString, ''),
  root: orMissing(aString, ''),
  confirmed: orMissing(aString, ''),
  presence: (value, path) =>
    value === 'present' || value === 'missing'
      ? { ok: true, value }
      : { ok: false, failure: { path, expected: 'present or missing', got: String(value) } },
})

export const readCatalogue: Reader<ProjectCatalogue> = record<ProjectCatalogue>({
  version: aNumber,
  roots: listOf(record<ScanRoot>({ path: aString, depth: aNumber })),
  projects: listOf(readRecordedProject),
})

/**
 * Read a record back, or answer nothing.
 *
 * A record this app cannot read is not an error worth showing anybody: it is a list that
 * will be rebuilt by the scan already running behind it. What must not happen is reading
 * one of a shape this build does not understand and drawing it as though it were current.
 */
export function catalogueFrom(text: string): ProjectCatalogue | null {
  let source: unknown
  try {
    source = JSON.parse(text)
  } catch {
    return null
  }

  const parsed: Parsed<ProjectCatalogue> = readCatalogue(source, '')
  if (!parsed.ok) return null
  if (parsed.value.version !== CATALOGUE_VERSION) return null
  return parsed.value
}
