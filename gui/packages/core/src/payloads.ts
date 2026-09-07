import {
  aBoolean,
  aNumber,
  anything,
  aString,
  dictionaryOf,
  listOf,
  orMissing,
  orNull,
  record,
  type Reader,
} from './reading'
import { readRemedy, type Remedy } from './refusals'

/**
 * The shapes this app reads, written by hand from the payloads themselves.
 *
 * By hand deliberately. There is no schema to generate from, and inventing one would be a
 * second declaration of roadkeep's format living outside roadkeep — which is the thing the
 * non-goals refuse. The safety comes from the other end instead: RG4's contract test runs
 * the real command and holds these shapes against what it prints, so a type that drifts
 * fails in this project's suite rather than in somebody's window.
 *
 * Each shape declares only what this app reads. Every payload carries more, and a reader
 * that refused the extra would break on the first release that added a key.
 *
 * Two readings are easy to get wrong and are called out where they appear. **Optional is
 * the default**: `standing`, `over` and `section` come back null in ordinary answers, so a
 * shape demanding them is a shape that fails on a normal day. And **the same key is not
 * the same type across verbs** — `uncounted` is a list of lines under `list` and a count
 * under `stats`, which is exactly the drift a single shared shape would have hidden.
 */

export interface TaskLine {
  readonly id: string
  readonly status: string
  readonly block: string
  readonly symptom: string
  readonly why: string
  readonly deps: readonly string[]
  /**
   * The pointer to this line's rationale. **Null in the ledger**, where a shipped line's
   * section has been deleted and there is nothing left to point at — found by RG4's
   * contract test against a real changelog, which is where a shape written as `string`
   * would otherwise have failed on somebody's screen.
   */
  readonly ref: string | null
  readonly line: number
  /** The rendered length, against the project's own line limit. */
  readonly length: number
}

export const readTaskLine: Reader<TaskLine> = record<TaskLine>({
  id: aString,
  status: aString,
  block: aString,
  symptom: aString,
  why: aString,
  deps: listOf(aString),
  ref: orMissing(orNull(aString), null),
  line: aNumber,
  length: aNumber,
})

/** How a block stands, as a sentence the engine composed and this app never rewrites. */
export interface Standing {
  readonly block: string
  readonly state: string
  readonly sentence: string
  readonly open: number
  readonly recorded: number
  readonly paused: number
}

export const readStanding: Reader<Standing> = record<Standing>({
  block: aString,
  state: aString,
  sentence: aString,
  open: aNumber,
  recorded: aNumber,
  paused: aNumber,
})

export interface AbsentRequirement {
  readonly requirement: string
  readonly lines: number
}

export interface Startable {
  readonly open: number
  readonly startable: number
  readonly waiting: number
  readonly absent: readonly AbsentRequirement[]
}

export const readStartable: Reader<Startable> = record<Startable>({
  open: aNumber,
  startable: aNumber,
  waiting: aNumber,
  absent: listOf(record<AbsentRequirement>({ requirement: aString, lines: aNumber })),
})

export interface ListPayload {
  readonly file: string
  readonly total: number
  /**
   * Marker-bearing lines the grammar did not accept. A list, not a count — and non-empty
   * means this answer is narrower than the file, which a screen has to say out loud.
   */
  readonly uncounted: readonly unknown[]
  readonly standing: Standing | null
  readonly startable: Startable | null
  readonly over: unknown
  readonly tasks: readonly TaskLine[]
}

export const readListPayload: Reader<ListPayload> = record<ListPayload>({
  file: aString,
  total: aNumber,
  uncounted: listOf(anything),
  standing: orMissing(orNull(readStanding), null),
  startable: orMissing(orNull(readStartable), null),
  over: orMissing(anything, null),
  tasks: listOf(readTaskLine),
})

export interface BlockCount {
  readonly block: string
  readonly counted: number
  readonly uncounted: number
  readonly markers: Record<string, number>
}

export interface StatsPayload {
  readonly file: string
  readonly total: number
  /** A count here, where `list` gives a list. Two verbs, one key name, two types. */
  readonly uncounted: number
  /** Keyed by the marker set the project declares, so the keys cannot be written down. */
  readonly markers: Record<string, number>
  readonly startable: Startable | null
  readonly blocks: readonly BlockCount[]
}

export const readStatsPayload: Reader<StatsPayload> = record<StatsPayload>({
  file: aString,
  total: aNumber,
  uncounted: aNumber,
  markers: dictionaryOf(aNumber),
  startable: orMissing(orNull(readStartable), null),
  blocks: orMissing(
    listOf(
      record<BlockCount>({
        block: aString,
        counted: aNumber,
        uncounted: aNumber,
        markers: dictionaryOf(aNumber),
      }),
    ),
    [],
  ),
})

export interface RationaleSection {
  readonly anchor: string
  readonly title: string
  readonly level: number
  readonly file: string
  readonly first: number
  readonly last: number
  readonly words: number
  /**
   * The prose, or **null where it was not asked for**: `show --no-body` keeps the section
   * and where it lives and drops what it says. Null and empty are different answers, so
   * this is not flattened to a string — a section that exists and is empty is a defect,
   * and one that was not requested is not.
   */
  readonly body: string | null
}

export const readSection: Reader<RationaleSection> = record<RationaleSection>({
  anchor: aString,
  title: aString,
  level: aNumber,
  file: aString,
  first: aNumber,
  last: aNumber,
  words: aNumber,
  body: orMissing(orNull(aString), null),
})

export interface ShowPayload {
  readonly id: string
  readonly status: string
  readonly block: string
  readonly shipped: boolean
  readonly file: string
  readonly line: number
  readonly rendered: string
  readonly symptom: string
  readonly why: string
  readonly deps: readonly string[]
  readonly requires: readonly string[]
  readonly ref: string
  /** Null for a line whose pointer resolves to nothing, which is a state and not an error. */
  readonly section: RationaleSection | null
  /** What the engine says about that absence, in its own words. */
  readonly sectionAbsence: string
}

export const readShowPayload: Reader<ShowPayload> = record<ShowPayload>(
  {
    id: aString,
    status: aString,
    block: aString,
    shipped: orMissing(aBoolean, false),
    file: aString,
    line: aNumber,
    rendered: aString,
    symptom: aString,
    why: aString,
    deps: listOf(aString),
    requires: orMissing(listOf(aString), []),
    ref: aString,
    section: orMissing(orNull(readSection), null),
    sectionAbsence: orMissing(aString, ''),
  },
  { sectionAbsence: 'section_absence' },
)

/** What shipping this line would unblock, and how much of that the answer left out. */
export interface Unblocks {
  readonly count: number
  /** Out of how many lines in the backlog. */
  readonly of: number
  readonly transitive: readonly string[]
  /** Ids the answer did not list. Above zero, `transitive` is a sample and not the set. */
  readonly transitiveElided: number
}

export const readUnblocks: Reader<Unblocks> = record<Unblocks>(
  {
    count: aNumber,
    of: aNumber,
    transitive: orMissing(listOf(aString), []),
    transitiveElided: orMissing(aNumber, 0),
  },
  { transitiveElided: 'transitive_elided' },
)

export interface BriefPayload {
  readonly id: string
  readonly status: string
  readonly block: string
  readonly symptom: string
  readonly why: string
  readonly deps: readonly string[]
  readonly ref: string
  readonly section: RationaleSection | null
  /** Whether the line is ready, waiting or blocked, in the engine's own word. */
  readonly readiness: string
  /** Why this line was chosen. Empty when the caller named an id. */
  readonly picked: string
  readonly unblocks: Unblocks | null
  readonly nonGoals: readonly string[]
  readonly nonGoalsElided: number
  readonly doneWhen: readonly string[]
  readonly doneWhenElided: number
}

export const readBriefPayload: Reader<BriefPayload> = record<BriefPayload>(
  {
    id: aString,
    status: aString,
    block: aString,
    symptom: aString,
    why: aString,
    deps: listOf(aString),
    ref: aString,
    section: orMissing(orNull(readSection), null),
    readiness: orMissing(aString, ''),
    picked: orMissing(aString, ''),
    unblocks: orMissing(orNull(readUnblocks), null),
    nonGoals: orMissing(listOf(aString), []),
    nonGoalsElided: orMissing(aNumber, 0),
    doneWhen: orMissing(listOf(aString), []),
    doneWhenElided: orMissing(aNumber, 0),
  },
  {
    nonGoals: 'non_goals',
    nonGoalsElided: 'non_goals_elided',
    doneWhen: 'done_when',
    doneWhenElided: 'done_when_elided',
  },
)

export interface LintFinding {
  readonly code: string
  readonly file: string
  readonly line: number | null
  readonly id: string | null
  readonly message: string
  /**
   * Every finding names the command that closes it, in the same shape `explain` publishes
   * for a refusal's code. One reader for both: a refusal and a gate finding are the same
   * thing at two moments, and offering the door in one place only is how they drift.
   */
  readonly remedy: Remedy | null
}

const readFinding: Reader<LintFinding> = record<LintFinding>({
  code: aString,
  file: orMissing(aString, ''),
  line: orMissing(orNull(aNumber), null),
  id: orMissing(orNull(aString), null),
  message: aString,
  remedy: orMissing(orNull(readRemedy), null),
})

export interface LintPayload {
  readonly root: string
  readonly clean: boolean
  readonly checked: readonly string[]
  readonly lines: number
  readonly sections: number
  readonly problems: number
  readonly codes: Record<string, number>
  readonly findings: readonly LintFinding[]
  /** Not violations: things the gate says without failing for them. */
  readonly notes: readonly LintFinding[]
}

export const readLintPayload: Reader<LintPayload> = record<LintPayload>({
  root: aString,
  clean: aBoolean,
  checked: listOf(aString),
  lines: aNumber,
  sections: aNumber,
  problems: aNumber,
  codes: orMissing(dictionaryOf(aNumber), {}),
  findings: listOf(readFinding),
  notes: orMissing(listOf(readFinding), []),
})

/**
 * What a payload says about its own completeness.
 *
 * A narrowed answer rendered as a complete one shows less than there is and says nothing
 * about it, which is worse than showing nothing: the reader has no way to know. Every
 * signal here is one the payload carries itself — nothing is inferred.
 */
export interface Narrowing {
  readonly complete: boolean
  readonly reasons: readonly string[]
}

export function narrowingOfList(payload: ListPayload): Narrowing {
  const reasons =
    payload.uncounted.length > 0
      ? [
          `${String(payload.uncounted.length)} marker-bearing line(s) the grammar did not accept, reported beside this answer`,
        ]
      : []
  return { complete: reasons.length === 0, reasons }
}

export function narrowingOfStats(payload: StatsPayload): Narrowing {
  const reasons =
    payload.uncounted > 0
      ? [`${String(payload.uncounted)} marker-bearing line(s) this count could not read`]
      : []
  return { complete: reasons.length === 0, reasons }
}

/**
 * A brief elides rather than truncating silently, and the counts are how it says so. A
 * screen that drew the listed non-goals as the whole list would be showing a constraint
 * set that is missing exactly the entries nobody thought to look for.
 */
export function narrowingOfBrief(payload: BriefPayload): Narrowing {
  const reasons: string[] = []
  if (payload.nonGoalsElided > 0) {
    reasons.push(`${String(payload.nonGoalsElided)} non-goal(s) this brief did not list`)
  }
  if (payload.doneWhenElided > 0) {
    reasons.push(`${String(payload.doneWhenElided)} criterion or criteria this brief did not list`)
  }
  const elidedUnblocks = payload.unblocks?.transitiveElided ?? 0
  if (elidedUnblocks > 0) {
    reasons.push(`${String(elidedUnblocks)} id(s) this line unblocks that were not listed`)
  }
  return { complete: reasons.length === 0, reasons }
}
