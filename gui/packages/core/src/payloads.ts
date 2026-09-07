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
import { readDoor, readRemedy, type Door, type Remedy } from './refusals'

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

/**
 * A marker-bearing line the grammar did not accept.
 *
 * Typed rather than carried as `unknown`, because these are the half of a listing a
 * person most needs to see: a line with a marker on it that no verb can read is a line
 * that is invisible to every count and every pick, and it is sitting in the file looking
 * exactly like the ones that work.
 */
export interface RefusedLine {
  readonly line: number
  /** The block it appeared under, empty where the grammar could not tell. */
  readonly block: string
  /** Why it was not accepted, in the engine's words. */
  readonly reason: string
  /** The line exactly as the file spells it. */
  readonly raw: string
}

export const readRefusedLine: Reader<RefusedLine> = record<RefusedLine>({
  line: orMissing(aNumber, 0),
  block: orMissing(aString, ''),
  reason: orMissing(aString, ''),
  raw: orMissing(aString, ''),
})

export interface ListPayload {
  readonly file: string
  readonly total: number
  /**
   * Marker-bearing lines the grammar did not accept. A list, not a count — and non-empty
   * means this answer is narrower than the file, which a screen has to say out loud.
   */
  readonly uncounted: readonly RefusedLine[]
  readonly standing: Standing | null
  readonly startable: Startable | null
  readonly over: unknown
  readonly tasks: readonly TaskLine[]
}

export const readListPayload: Reader<ListPayload> = record<ListPayload>({
  file: aString,
  total: aNumber,
  uncounted: listOf(readRefusedLine),
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
   * What this heading says on its own, where `words` counts the subtree under it. Equal
   * for a section with no subsections, which is every rationale in this project today —
   * and reading both is what keeps a screen honest on the first one that has children.
   */
  readonly ownWords: number
  /**
   * The prose, or **null where it was not asked for**: `show --no-body` keeps the section
   * and where it lives and drops what it says. Null and empty are different answers, so
   * this is not flattened to a string — a section that exists and is empty is a defect,
   * and one that was not requested is not.
   */
  readonly body: string | null
}

export const readSection: Reader<RationaleSection> = record<RationaleSection>(
  {
    anchor: aString,
    title: aString,
    level: aNumber,
    file: aString,
    first: aNumber,
    last: aNumber,
    words: aNumber,
    ownWords: orMissing(aNumber, 0),
    body: orMissing(orNull(aString), null),
  },
  { ownWords: 'own_words' },
)

/**
 * What a section's prose may still say, in the engine's own numbers.
 *
 * Every one of these is carried and none is worked out here. `limit` is the project's
 * `[limits] section` and writing 250 into this app would be exactly the literal the
 * non-goals refuse; `unit` is the engine saying it counts words rather than characters,
 * which is not the same answer for every field it prices.
 */
export interface SectionBudget {
  readonly anchor: string
  /** Which prose file it is priced against — improvements and decisions differ. */
  readonly role: string
  /** False where the pointer has no section yet, which is a state and not an error. */
  readonly written: boolean
  readonly unit: string
  readonly limit: number
  readonly taken: number
  readonly left: number
  /** How far past the limit it already is. Above zero, the gate is what says so. */
  readonly over: number
}

export const readSectionBudget: Reader<SectionBudget> = record<SectionBudget>({
  anchor: orMissing(aString, ''),
  role: orMissing(aString, ''),
  written: orMissing(aBoolean, false),
  unit: orMissing(aString, ''),
  limit: orMissing(aNumber, 0),
  taken: orMissing(aNumber, 0),
  left: orMissing(aNumber, 0),
  over: orMissing(aNumber, 0),
})

/**
 * The pricing a brief carries, of which this app reads the section's half.
 *
 * **Null for a shipped line**: there is nothing left to price once the design has been
 * deleted, and a shape demanding the object fails on every id in the ledger.
 */
export interface BriefBudget {
  readonly section: SectionBudget | null
}

export const readBriefBudget: Reader<BriefBudget> = record<BriefBudget>({
  section: orMissing(orNull(readSectionBudget), null),
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

/**
 * What shipping this line would unblock, and how much of that the answer left out.
 *
 * One shape over two verbs, because here the keys agree: `brief` samples and reports what
 * it left out, `deps` names the one-hop set as well and elides nothing. Each verb's own
 * half defaults to empty rather than being demanded, so neither reader fails on the other.
 */
export interface Unblocks {
  readonly count: number
  /** Out of how many lines in the backlog. */
  readonly of: number
  /** Freed by shipping this line itself. `deps` only — a brief does not separate them. */
  readonly direct: readonly string[]
  /** Everything freed downstream, the direct ones included. */
  readonly transitive: readonly string[]
  /** Ids the answer did not list. Above zero, `transitive` is a sample and not the set. */
  readonly transitiveElided: number
}

export const readUnblocks: Reader<Unblocks> = record<Unblocks>(
  {
    count: aNumber,
    of: aNumber,
    direct: orMissing(listOf(aString), []),
    transitive: orMissing(listOf(aString), []),
    transitiveElided: orMissing(aNumber, 0),
  },
  { transitiveElided: 'transitive_elided' },
)

/** One dep, and what the engine found when it went looking. */
export interface ResolvedDep {
  readonly dep: string
  /** What kind of thing it is: a task here, a block, work outside this backlog. */
  readonly kind: string
  /** Shipped, open, retired — the engine's word, never one worked out here. */
  readonly status: string
  /** Where it was found, in the engine's words. */
  readonly detail: string
}

export const readResolvedDep: Reader<ResolvedDep> = record<ResolvedDep>({
  dep: aString,
  kind: orMissing(aString, ''),
  status: orMissing(aString, ''),
  detail: orMissing(aString, ''),
})

/**
 * One route from a line to something it is waiting on, spelled from that line outward.
 *
 * `path` is the ids in order with this task at its head; `via` is the dep that made each
 * hop, which is not the same list — a dep naming a block or a range expands to the
 * members behind it, and `via` is what the file actually says.
 */
export interface DepChain {
  readonly path: readonly string[]
  readonly via: readonly string[]
  /** What the far end turned out to be, in the engine's word. */
  readonly end: string
  readonly detail: string
}

export const readDepChain: Reader<DepChain> = record<DepChain>({
  path: orMissing(listOf(aString), []),
  via: orMissing(listOf(aString), []),
  end: orMissing(aString, ''),
  detail: orMissing(aString, ''),
})

/**
 * One task's edges, resolved by the engine that owns the graph.
 *
 * The whole payload is a graph already computed — the chains are spelled out, the
 * blockers are named, and a cycle arrives as the ids caught in it. Nothing that reads
 * this walks it again.
 */
export interface DepsPayload {
  readonly id: string
  /** Ready, blocked, blocked-outside — the engine's word, and never one derived here. */
  readonly readiness: string
  readonly deps: readonly ResolvedDep[]
  /** The deps inside this backlog that are holding it, which shipping clears. */
  readonly blockers: readonly string[]
  readonly chains: readonly DepChain[]
  readonly unblocks: Unblocks | null
  /** Ids in a cycle with this one. Non-empty means nothing in the group can start. */
  readonly cycle: readonly string[]
}

export const readDepsPayload: Reader<DepsPayload> = record<DepsPayload>({
  id: aString,
  readiness: orMissing(aString, ''),
  deps: orMissing(listOf(readResolvedDep), []),
  blockers: orMissing(listOf(aString), []),
  chains: orMissing(listOf(readDepChain), []),
  unblocks: orMissing(orNull(readUnblocks), null),
  cycle: orMissing(listOf(aString), []),
})

/** A worker holding this line, so two sessions do not start on one id. */
export interface HeldClaim {
  readonly by: string
  readonly since: string
  readonly state: string
  readonly paths: readonly string[]
}

export const readHeldClaim: Reader<HeldClaim> = record<HeldClaim>({
  by: orMissing(aString, ''),
  since: orMissing(aString, ''),
  state: orMissing(aString, ''),
  paths: orMissing(listOf(aString), []),
})

export interface BriefPayload {
  readonly id: string
  readonly status: string
  readonly block: string
  readonly symptom: string
  readonly why: string
  readonly deps: readonly string[]
  /** What has to be present to finish this. Not a dep: hardware, an account, somebody's time. */
  readonly requires: readonly string[]
  readonly ref: string | null
  readonly section: RationaleSection | null
  /** What the engine says about a pointer that resolves to nothing. */
  readonly sectionAbsence: string
  /**
   * Ready, waiting or blocked — **in the engine's own word**. Block D's criterion is that
   * readiness is never derived in this app, and carrying the string is how that holds:
   * there is no rule here that could disagree with the resolver.
   */
  readonly readiness: string
  /**
   * Why this line was chosen, and **null when the caller named an id** — there was no
   * choosing to explain. Found by RG4's contract test against a real brief, where a shape
   * expecting an empty string failed on every id this app looks up by name.
   */
  readonly picked: string | null
  /** Each dep with what resolves it, so a blocker is a state and not an id to go and look up. */
  readonly depsResolved: readonly ResolvedDep[]
  readonly unblocks: Unblocks | null
  readonly nonGoals: readonly string[]
  readonly nonGoalsElided: number
  readonly doneWhen: readonly string[]
  readonly doneWhenElided: number
  /** Workers holding this line right now. Empty is the ordinary case. */
  readonly held: readonly HeldClaim[]
  /** Ledger entries citing this id — what already shipped against it. */
  readonly landed: readonly string[]
  /** What the line's fields and its section have left. Null once the design is gone. */
  readonly budget: BriefBudget | null
}

export const readBriefPayload: Reader<BriefPayload> = record<BriefPayload>(
  {
    id: aString,
    status: aString,
    block: aString,
    symptom: aString,
    why: aString,
    deps: listOf(aString),
    requires: orMissing(listOf(aString), []),
    ref: orMissing(orNull(aString), null),
    section: orMissing(orNull(readSection), null),
    sectionAbsence: orMissing(aString, ''),
    readiness: orMissing(aString, ''),
    picked: orMissing(orNull(aString), null),
    depsResolved: orMissing(listOf(readResolvedDep), []),
    unblocks: orMissing(orNull(readUnblocks), null),
    nonGoals: orMissing(listOf(aString), []),
    nonGoalsElided: orMissing(aNumber, 0),
    doneWhen: orMissing(listOf(aString), []),
    doneWhenElided: orMissing(aNumber, 0),
    held: orMissing(listOf(readHeldClaim), []),
    landed: orMissing(listOf(aString), []),
    budget: orMissing(orNull(readBriefBudget), null),
  },
  {
    sectionAbsence: 'section_absence',
    depsResolved: 'deps_resolved',
    nonGoals: 'non_goals',
    nonGoalsElided: 'non_goals_elided',
    doneWhen: 'done_when',
    doneWhenElided: 'done_when_elided',
  },
)

/** One entry in the ledger: what a block delivered, and whether it held. */
export interface DeliveredEntry {
  readonly id: string
  readonly marker: string
  /** The claim the entry made, which is what a duplicate collides with. */
  readonly symptom: string
  readonly line: number
  /**
   * The entry that superseded this one, or null. **A revert is filed as a delivery**, so
   * an entry can say shipped and mean the work did not hold.
   */
  readonly undoneBy: string | null
  /**
   * Where it placed against the sentence `--near` asked about. Absent without it, and it
   * is a **position and never a score** — no threshold is published, because none exists.
   */
  readonly rank: number
}

export const readDeliveredEntry: Reader<DeliveredEntry> = record<DeliveredEntry>(
  {
    id: aString,
    marker: orMissing(aString, ''),
    symptom: orMissing(aString, ''),
    line: orMissing(aNumber, 0),
    undoneBy: orMissing(orNull(aString), null),
    rank: orMissing(aNumber, 0),
  },
  { undoneBy: 'undone_by' },
)

export interface DeliveredPayload {
  readonly file: string
  readonly block: string
  readonly standing: Standing | null
  readonly recorded: number
  /** The sentence the ranking answered, or null where the whole block was asked for. */
  readonly near: string | null
  readonly delivered: readonly DeliveredEntry[]
}

export const readDeliveredPayload: Reader<DeliveredPayload> = record<DeliveredPayload>({
  file: orMissing(aString, ''),
  block: orMissing(aString, ''),
  standing: orMissing(orNull(readStanding), null),
  recorded: orMissing(aNumber, 0),
  near: orMissing(orNull(aString), null),
  delivered: orMissing(listOf(readDeliveredEntry), []),
})

/** One decision the ledger already undid, and the entry that undid it. */
export interface ReversalEntry {
  readonly undone: string
  readonly by: string
  readonly line: number
  /** The superseding entry's own sentence — the argument a fresh proposal is against. */
  readonly why: string
}

export const readReversalEntry: Reader<ReversalEntry> = record<ReversalEntry>({
  undone: aString,
  by: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  why: orMissing(aString, ''),
})

export interface ReversalsPayload {
  readonly root: string
  /**
   * The id the caller asked about, **null where the question was the whole ledger**. It
   * is the question and not a fact of the file: a listing of one otherwise reads as a
   * ledger with one reversal in it.
   */
  readonly asked: string | null
  readonly reversed: readonly ReversalEntry[]
}

export const readReversalsPayload: Reader<ReversalsPayload> = record<ReversalsPayload>({
  root: orMissing(aString, ''),
  asked: orMissing(orNull(aString), null),
  reversed: orMissing(listOf(readReversalEntry), []),
})

/**
 * What this project says it is not building.
 *
 * Leads only. A non-goal's reason lives in the file and no read publishes it, so the
 * shape declares what arrives and never a key that would have to be filled in from
 * somewhere.
 */
export interface NonGoalsPayload {
  readonly file: string
  /**
   * Whether the project declares the list at all. **False is a state, not a failure**:
   * reading is never refused, so an ungoverned list arrives empty and says so.
   */
  readonly governed: boolean
  readonly nonGoals: readonly string[]
  readonly nonGoalsElided: number
  /**
   * Lead → the ids whose design quotes it. `non-goal.reaches` goes silent for those, so a
   * quoted lead is one somebody has answered in writing and a bare one is not.
   */
  readonly nonGoalsQuoted: Record<string, readonly string[]>
}

export const readNonGoalsPayload: Reader<NonGoalsPayload> = record<NonGoalsPayload>(
  {
    file: orMissing(aString, ''),
    governed: orMissing(aBoolean, false),
    nonGoals: orMissing(listOf(aString), []),
    nonGoalsElided: orMissing(aNumber, 0),
    nonGoalsQuoted: orMissing(dictionaryOf(listOf(aString)), {}),
  },
  {
    nonGoals: 'non_goals',
    nonGoalsElided: 'non_goals_elided',
    nonGoalsQuoted: 'non_goals_quoted',
  },
)

/** One thing that has to be true, and the address it is written at. */
export interface Criterion {
  /** What it is about: a block label, or a task id where a line carries its own. */
  readonly about: string
  readonly lead: string
  readonly why: string
  readonly line: number
  /** Whether the entry parsed as the two-part shape the format declares. */
  readonly shaped: boolean
}

export const readCriterion: Reader<Criterion> = record<Criterion>({
  about: orMissing(aString, ''),
  lead: aString,
  why: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  shaped: orMissing(aBoolean, false),
})

export interface CriteriaPayload {
  readonly file: string
  readonly governed: boolean
  /** Every block label the roadmap declares, which is what `--block` can narrow to. */
  readonly blocks: readonly string[]
  /**
   * Which kind of nothing this is, in the engine's word — ungoverned, unasked, all
   * dropped. **Null when the answer is not empty**, which is the ordinary case.
   */
  readonly empty: string | null
  readonly criteria: readonly Criterion[]
  /** What would open a list that is not there. The engine's own argv, offered not composed. */
  readonly doors: readonly Door[]
}

export const readCriteriaPayload: Reader<CriteriaPayload> = record<CriteriaPayload>({
  file: orMissing(aString, ''),
  governed: orMissing(aBoolean, false),
  blocks: orMissing(listOf(aString), []),
  empty: orMissing(orNull(aString), null),
  criteria: orMissing(listOf(readCriterion), []),
  doors: orMissing(listOf(readDoor), []),
})

/**
 * What `add` answers when a line lands.
 *
 * `near` is the same ranking `delivered --near` publishes, offered unasked: the entries
 * closest to the symptom just filed, so a duplicate is seen at the moment it is made
 * rather than found later. **An order and never a verdict**, exactly as it is there.
 */
export interface AddedPayload {
  readonly id: string
  readonly ref: string
  readonly file: string
  readonly line: number
  /** The line as the file now spells it, which is what a screen should show back. */
  readonly rendered: string
  readonly length: number
  /** The section written in the same transaction, or null where none was asked for. */
  readonly section: RationaleSection | null
  readonly near: readonly DeliveredEntry[]
  /** How many of the nearest were already delivered rather than open. */
  readonly nearRecorded: number
}

export const readAddedPayload: Reader<AddedPayload> = record<AddedPayload>(
  {
    id: aString,
    ref: orMissing(aString, ''),
    file: orMissing(aString, ''),
    line: orMissing(aNumber, 0),
    rendered: orMissing(aString, ''),
    length: orMissing(aNumber, 0),
    section: orMissing(orNull(readSection), null),
    near: orMissing(listOf(readDeliveredEntry), []),
    nearRecorded: orMissing(aNumber, 0),
  },
  { nearRecorded: 'near_recorded' },
)

/**
 * What a marker write did, and what went with it.
 *
 * `changed` false is an answer and not a failure: a line already carrying the marker asked
 * for still followed its claim and still has a standing to report.
 */
export interface StatusPayload {
  readonly id: string
  readonly from: string
  readonly to: string
  readonly changed: boolean
  readonly file: string
  readonly line: number
  readonly rendered: string
  /** Ids whose dep annotations were re-derived because this marker moved. */
  readonly refreshed: readonly string[]
  /**
   * What the write did to the claim on this line: `claimed`, `released`, or **null** where
   * it did neither. The engine's own word, and the reason a claim never has to be inferred
   * from the marker somebody just wrote.
   */
  readonly claim: string | null
  /** The governed files this write touched. */
  readonly wrote: readonly string[]
}

export const readStatusPayload: Reader<StatusPayload> = record<StatusPayload>({
  id: aString,
  from: orMissing(aString, ''),
  to: orMissing(aString, ''),
  changed: orMissing(aBoolean, false),
  file: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  rendered: orMissing(aString, ''),
  refreshed: orMissing(listOf(aString), []),
  claim: orMissing(orNull(aString), null),
  wrote: orMissing(listOf(aString), []),
})

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

/** The line `pick` chose, or null where the backlog has nothing to offer. */
export interface PickedLine {
  readonly id: string
  readonly block: string
  readonly status: string
  readonly symptom: string
  readonly ref: string | null
}

export interface PickPayload {
  readonly pick: PickedLine | null
  /** Which of the three tiers answered: in progress, the priority queue, or lowest ready id. */
  readonly tier: string
  /** Why this line and not another, in the engine's own words. */
  readonly reason: string
  readonly ready: number
  readonly blocked: number
  /** Blocked on something outside this backlog, which shipping here can never unblock. */
  readonly outside: number
  readonly paused: number
}

export const readPickPayload: Reader<PickPayload> = record<PickPayload>({
  pick: orMissing(
    orNull(
      record<PickedLine>({
        id: aString,
        block: orMissing(aString, ''),
        status: orMissing(aString, ''),
        symptom: orMissing(aString, ''),
        ref: orMissing(orNull(aString), null),
      }),
    ),
    null,
  ),
  tier: orMissing(aString, ''),
  reason: orMissing(aString, ''),
  ready: orMissing(aNumber, 0),
  blocked: orMissing(aNumber, 0),
  outside: orMissing(aNumber, 0),
  paused: orMissing(aNumber, 0),
})

export interface ConfigKey {
  /** The table it sits under, empty for a top-level key. `files` is the one this app reads. */
  readonly table: string
  readonly key: string
  readonly address: string
  readonly declared: boolean
  /** The value as the file spells it, quotes included, or null where nothing declares it. */
  readonly set: string | null
}

export interface ConfigPayload {
  readonly version: string
  readonly source: string
  readonly keys: readonly ConfigKey[]
}

export const readConfigPayload: Reader<ConfigPayload> = record<ConfigPayload>({
  version: aString,
  source: orMissing(aString, ''),
  keys: listOf(
    record<ConfigKey>({
      table: orMissing(aString, ''),
      key: aString,
      address: orMissing(aString, ''),
      declared: orMissing(aBoolean, false),
      set: orMissing(orNull(aString), null),
    }),
  ),
})

/**
 * The governed files this project declares, by role.
 *
 * Asked of the engine rather than read out of `roadkeep.toml`, because which files are
 * governed is a rule the tool owns — a TOML parser here would be a second reading of a
 * format this app has no business knowing. `set` arrives with the quotes the file spells,
 * so they come off here and nowhere else.
 */
export function governedFiles(payload: ConfigPayload): Record<string, string> {
  const files: Record<string, string> = {}
  for (const entry of payload.keys) {
    if (entry.table !== 'files' || !entry.declared || entry.set === null) continue
    const path = entry.set.replace(/^["']|["']$/g, '')
    if (path !== '') files[entry.key] = path
  }
  return files
}

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
