import type { RecordedProject } from './catalogue'
import type { EnginesPayload } from './engines'
import type { Unreadable } from './limits'
import type { LintPayload, PickPayload, StatsPayload } from './payloads'

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
  readonly tier: string
  readonly ready: number
  readonly blocked: number
}

export interface RowGate {
  readonly clean: boolean
  readonly problems: number
}

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
  return parts[parts.length - 1] ?? path
}

function shell(project: RecordedProject): Omit<ProjectRow, 'state'> {
  return {
    path: project.path,
    name: folderName(project.path),
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
  readonly lint?: LintPayload | null
  readonly engines?: EnginesPayload | null
}

export function readRow(project: RecordedProject, reads: RowReads): ProjectRow {
  return {
    ...shell(project),
    state: 'read',
    counts: reads.stats ? countsFrom(reads.stats) : null,
    next: reads.pick ? nextFrom(reads.pick) : null,
    gate: reads.lint ? { clean: reads.lint.clean, problems: reads.lint.problems } : null,
    engine: reads.engines ? engineFrom(reads.engines) : null,
  }
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
    tier: pick.tier,
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
