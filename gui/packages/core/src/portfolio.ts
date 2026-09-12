import type { RecordedProject } from './catalogue'
import type { EnginesPayload } from './engines'
import type { GateHealth } from './gate'
import type { Unreadable } from './limits'
import type { Declared, PickPayload, StatsPayload } from './payloads'

/**
 * One row per project, and what it is allowed to hold.
 *
 * Seventeen governed checkouts are seventeen terminals today, and the count each one holds
 * is unreachable from any one place. This is the row that fixes that, and the discipline
 * is in what it refuses.
 *
 * **Every number on a row came off a payload.** Nothing is computed *across* projects: a
 * total open count over seventeen backlogs is a number no single repository could
 * reproduce, so nobody could audit it and nobody should trust it. `tally` below counts
 * rows, which is a fact about this screen rather than a claim about anybody's backlog.
 *
 * **A project still being read is pending, never a row of zeroes.** Zero open tasks and
 * not-yet-known look identical on a screen and mean opposite things, and the one that gets
 * believed is the wrong one. So every payload field is null until it arrives.
 *
 * Sorting and grouping are the view's, and are the only things here derived rather than
 * read. The name is the folder's own, which is a fact about a path and not a field this
 * app composed.
 */

export type RowState =
  /** Being read. Every payload field is still null. */
  | 'pending'
  /** Read. What arrived is on the row; what was not asked for is still null. */
  | 'read'
  /** The read did not come back, and the row says why. */
  | 'unreadable'

/** What `stats` printed, kept per project and never added up across them. */
export interface RowCounts {
  readonly total: number
  readonly markers: Readonly<Record<string, number>>
  readonly startable: number
  readonly waiting: number
  /** Marker-bearing lines the count could not read. Above zero the row is narrower than the file. */
  readonly uncounted: number
}

export interface RowNext {
  readonly id: string | null
  readonly symptom: string
  readonly block: string
  readonly status: string
  /** Which of roadkeep's three tiers answered. Its word, carried and never interpreted. */
  readonly tier: string
  readonly ready: number
  readonly blocked: number
}

/**
 * The gate is not a read this screen makes. It is the last verdict on record, dated, and
 * `unknown` until something has actually run — see `gate.ts` for why clean has to be
 * earned rather than assumed.
 */
export type RowGate = GateHealth

export interface RowEngine {
  readonly version: string
  readonly home: string
  readonly verdict: string
  /** The answers are a working tree's, which `lint` says out loud and a row repeats. */
  readonly modified: boolean
  readonly agree: boolean
}

export interface ProjectRow {
  readonly path: string
  /** The folder's own name. A fact about the path, not a field this app made up. */
  readonly name: string
  /**
   * One emoji the project declared to stand for itself, or empty (RG200).
   *
   * **Text and never parsed**: no grapheme splitting, no codepoint arithmetic, no attempt to
   * decide whether a ZWJ sequence counts as one emoji. What the file said is what is drawn,
   * and a project declaring nothing keeps the folder glyph.
   */
  readonly icon: string
  /**
   * What the project says it is for, or empty (RG201).
   *
   * Drawn as it was given: the limit is the engine's, declared in `[limits]` and refused
   * where the description is written — a screen that silently shortens prose is a screen
   * that disagrees with the file it is reading.
   */
  readonly description: string
  readonly aliases: readonly string[]
  readonly commonDir: string | null
  readonly state: RowState
  readonly counts: RowCounts | null
  readonly next: RowNext | null
  readonly gate: RowGate | null
  readonly engine: RowEngine | null
  readonly unreadable: Unreadable | null
}

/** The last segment of a path, whichever separator it uses. */
export function folderName(path: string): string {
  const parts = path.split(/[/\\]/).filter((part) => part !== '')
  return parts.at(-1) ?? path
}

/**
 * What to call a project: what it declares, or its folder (RG202).
 *
 * One function, because five screens each recomputed the folder name and so agreed with
 * each other and with nothing else — and the disagreement landed on navigation, where a
 * label's whole job is to say where the back arrow goes. `folderName` stays: it is still
 * the fallback, still correct about paths, and still the only thing that can answer for a
 * folder nothing has read.
 */
export function nameOf(declares: Declared | null | undefined, path: string): string {
  return declares?.name || folderName(path)
}

function shell(project: RecordedProject): Omit<ProjectRow, 'state'> {
  return {
    path: project.path,
    name: folderName(project.path),
    icon: '',
    description: '',
    aliases: project.aliases,
    commonDir: project.commonDir,
    counts: null,
    next: null,
    gate: null,
    engine: null,
    unreadable: null,
  }
}

/** A project on the list and not yet read. Draw it as waiting, never as empty. */
export function pendingRow(project: RecordedProject): ProjectRow {
  return { ...shell(project), state: 'pending' }
}

export function unreadableRow(project: RecordedProject, unreadable: Unreadable): ProjectRow {
  return { ...shell(project), state: 'unreadable', unreadable }
}

/** What a row can be filled from. Each is optional: a read that has not happened is null. */
export interface RowReads {
  readonly stats?: StatsPayload | null
  readonly pick?: PickPayload | null
  readonly engines?: EnginesPayload | null
  /**
   * What the project declares about itself (RG198). The name is the one fact a folder gets
   * wrong: two worktrees of one product are `2026.3` and `2026.2`, and neither says which
   * product.
   */
  readonly declares?: Declared | null
  /**
   * Not a read. The gate's last verdict comes off the ledger, because running `lint`
   * seventeen times to draw a list is the cost this whole arrangement avoids.
   */
  readonly gate?: GateHealth | null
}

export function readRow(project: RecordedProject, reads: RowReads): ProjectRow {
  return fillRow({ ...shell(project), state: 'read' }, reads)
}

/**
 * The same row with whatever has since been read put onto it.
 *
 * A row is filled in more than one moment (RG73): the counts are what a list is scanned
 * for and the next line arrives after, so what a screen already drew has to survive the
 * second pass. A read that has not happened leaves the field it would have filled exactly
 * as it was, which is what makes it safe to call twice.
 */
export function fillRow(row: ProjectRow, reads: RowReads): ProjectRow {
  return {
    ...row,
    state: 'read',
    // A declared name replaces the folder's; nothing declared leaves what was there, which
    // is the folder — so this is safe to call twice, like every other field here.
    name: reads.declares?.name || row.name,
    icon: reads.declares?.icon || row.icon,
    description: reads.declares?.description || row.description,
    counts: reads.stats ? countsFrom(reads.stats) : row.counts,
    next: reads.pick ? nextFrom(reads.pick) : row.next,
    gate: reads.gate ?? row.gate,
    engine: reads.engines ? engineFrom(reads.engines) : row.engine,
  }
}

/**
 * Put the verdicts on record onto the rows they belong to (RG152).
 *
 * Applied to every list a screen draws rather than once, because the reads that fill a row
 * land at their own pace and a merge done once would be undone by the next stage to finish.
 * A row no verdict names keeps the one it had, which is `null` — and a row drawn with `null`
 * says unknown, never clean.
 *
 * The paths are compared as they are given: both sides of this got theirs from the same
 * catalogue, and a key this side made up would be this side deciding a platform's path rules.
 */
export function gatedRows(
  rows: readonly ProjectRow[],
  verdicts: readonly { readonly root: string; readonly health: GateHealth }[],
): readonly ProjectRow[] {
  if (verdicts.length === 0) return rows
  const byRoot = new Map(verdicts.map((one) => [one.root, one.health]))
  return rows.map((row) => {
    const health = byRoot.get(row.path)
    return health === undefined ? row : { ...row, gate: health }
  })
}

function countsFrom(stats: StatsPayload): RowCounts {
  return {
    total: stats.total,
    markers: stats.markers,
    startable: stats.startable?.startable ?? 0,
    waiting: stats.startable?.waiting ?? 0,
    uncounted: stats.uncounted,
  }
}

function nextFrom(pick: PickPayload): RowNext {
  return {
    id: pick.pick?.id ?? null,
    symptom: pick.pick?.symptom ?? '',
    block: pick.pick?.block ?? '',
    status: pick.pick?.status ?? '',
    // Null beside a null pick, and a row with no next line has no tier to show either.
    tier: pick.tier ?? '',
    ready: pick.ready,
    blocked: pick.blocked,
  }
}

function engineFrom(engines: EnginesPayload): RowEngine {
  return {
    version: engines.writing.version,
    home: engines.writing.home,
    verdict: engines.verdict,
    modified: engines.writing.revision.includes('modified'),
    agree: engines.agree && !engines.split && !engines.swapped,
  }
}

/**
 * How the screen stands, counted in rows.
 *
 * Deliberately only rows. There is no open-task total here and there must not be one: it
 * would be the one number on the screen that no `roadkeep` command could print, which is
 * exactly the number somebody would quote in a meeting.
 */
export interface PortfolioTally {
  readonly projects: number
  readonly read: number
  readonly pending: number
  readonly unreadable: number
}

export function tally(rows: readonly ProjectRow[]): PortfolioTally {
  return {
    projects: rows.length,
    read: rows.filter((row) => row.state === 'read').length,
    pending: rows.filter((row) => row.state === 'pending').length,
    unreadable: rows.filter((row) => row.state === 'unreadable').length,
  }
}

/**
 * The narrowings the portfolio offers (RG145), each a question about rows already read.
 *
 * Nothing here asks a project anything: a chip narrows what is loaded, and what it counts is
 * rows — the same kind of fact `tally` keeps, and never a sum across backlogs. A row that has
 * not answered yet matches none of the three, since not knowing is not drifting.
 */
export type RowFilter = 'all' | 'drifted' | 'disagrees' | 'unreadable'

/** The chips, in the order the screen draws them. */
export const ROW_FILTERS: readonly RowFilter[] = ['all', 'drifted', 'disagrees', 'unreadable']

export function matchesFilter(row: ProjectRow, filter: RowFilter): boolean {
  if (filter === 'drifted') return row.gate?.verdict === 'drifted'
  if (filter === 'disagrees') return row.engine !== null && !row.engine.agree
  if (filter === 'unreadable') return row.state === 'unreadable'
  return true
}

/** How many rows each chip would leave, which is the number drawn on it. */
export function filterCounts(rows: readonly ProjectRow[]): Readonly<Record<RowFilter, number>> {
  const count = (filter: RowFilter) => rows.filter((row) => matchesFilter(row, filter)).length
  return {
    all: rows.length,
    drifted: count('drifted'),
    disagrees: count('disagrees'),
    unreadable: count('unreadable'),
  }
}
