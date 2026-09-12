import {
  aBoolean,
  aNumber,
  aString,
  dictionaryOf,
  listOf,
  oneOrMany,
  literalTrue,
  orMissing,
  orNull,
  record,
  whenFlagged,
  type Reader,
} from './reading'
import { offerable, readDoor, readRemedy, type Door, type Remedy } from './refusals'

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
  /**
   * How long a paused line has stood, in commits over the governed files, and the reason
   * it was set aside with — both from a `--stale` listing and absent from every other
   * (RG28).
   *
   * **Null is not zero.** The engine answers null where it cannot count the commits — a
   * store whose pauses predate the history it can see — and zero would say *set aside just
   * now*, which is the opposite. Found against the live engine, which answers null for a
   * fixture built in one commit.
   */
  readonly since: number | null
  readonly reason: string
  /**
   * What is holding this line up, in the engine's own word (RG170).
   *
   * Read here rather than resolved per row: the listing already classifies every open line
   * to produce its own `startable` count, and a `deps` call per row was eight hundred reads
   * to draw one screen of a large backlog.
   *
   * **Empty is a build that does not answer it**, which is a state and not a failure: the
   * field arrived in roadkeep 0.2.466, and a project on an older copy draws no column rather
   * than a wrong one. Never derived here — block D's second criterion — so a row with nothing
   * to read shows nothing.
   */
  readonly readiness: string
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
  since: orMissing(orNull(aNumber), null),
  reason: orMissing(aString, ''),
  readiness: orMissing(aString, ''),
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

/** One block as `block list` stands it: its standing, and the heading's own title (RG148). */
export interface BlockStanding extends Standing {
  /** The heading after the label, as the file writes it. Empty where it has none. */
  readonly title: string
}

export interface BlockListPayload {
  readonly file: string
  /** Every block the roadmap declares, in heading order. */
  readonly blocks: readonly BlockStanding[]
}

export const readBlockListPayload: Reader<BlockListPayload> = record<BlockListPayload>({
  file: orMissing(aString, ''),
  blocks: orMissing(
    listOf(
      record<BlockStanding>({
        block: aString,
        state: orMissing(aString, ''),
        sentence: orMissing(aString, ''),
        open: orMissing(aNumber, 0),
        recorded: orMissing(aNumber, 0),
        paused: orMissing(aNumber, 0),
        title: orMissing(aString, ''),
      }),
    ),
    [],
  ),
})

/**
 * One entry in the claim registry (RG153).
 *
 * **Held, expired and stale are the engine's words and the whole of the reading**: an expired
 * entry was stepped over and the line is offered again, and a stale one is a marker that moved
 * out from under a claim nothing reads any more. A claim names nobody where nobody named
 * themselves, which is why `by` can be empty on an entry that is certainly somebody's.
 */
export interface ClaimEntry {
  readonly id: string
  /** Held, expired or stale — the registry's own word, never one worked out here. */
  readonly state: string
  /** Where the line is now: open, shipped, gone. The engine's word again. */
  readonly where: string
  /** How long it has stood, as the engine prints it. A number of seconds is `age`. */
  readonly since: string
  readonly age: number
  readonly marker: string
  readonly block: string
  /** What the claim declared it would touch. Empty is the ordinary case. */
  readonly paths: readonly string[]
  /** Who holds it, where the registry knows. A claim names nobody by default. */
  readonly by: string
}

export const readClaimEntry: Reader<ClaimEntry> = record<ClaimEntry>({
  id: aString,
  state: orMissing(aString, ''),
  where: orMissing(aString, ''),
  since: orMissing(aString, ''),
  age: orMissing(aNumber, 0),
  marker: orMissing(aString, ''),
  block: orMissing(aString, ''),
  paths: orMissing(listOf(aString), []),
  by: orMissing(aString, ''),
})

export interface ClaimsPayload {
  /** How long a claim stands, in minutes, as this project declares it. */
  readonly window: number
  /** Where the registry lives, which is a file outside the repository. */
  readonly registry: string
  /** How many are held right now. The engine's count, not this list's length. */
  readonly held: number
  readonly claims: readonly ClaimEntry[]
}

export const readClaimsPayload: Reader<ClaimsPayload> = record<ClaimsPayload>({
  window: orMissing(aNumber, 0),
  registry: orMissing(aString, ''),
  held: orMissing(aNumber, 0),
  claims: orMissing(listOf(readClaimEntry), []),
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

/** One block's share of a listing that was not printed, so a narrowing can be offered. */
export interface OverBlock {
  /** The heading's label, which is what a `--block` door takes. */
  readonly label: string
  /** The heading as written, for a screen that shows more than a letter. */
  readonly name: string
  readonly counted: number
}

export const readOverBlock: Reader<OverBlock> = record<OverBlock>({
  label: aString,
  name: orMissing(aString, ''),
  counted: orMissing(aNumber, 0),
})

/**
 * The bound a listing did not fit under, and what to ask for instead.
 *
 * Present only where the project declares `[reads] list` **and** this answer went past it.
 * A key that appears on nothing else is one a caller has to have met before to check for,
 * which is why `over` is `null` rather than absent when no bound applied at all.
 */
export interface Over {
  /** What the answer would have cost, in the engine's own unit. */
  readonly characters: number
  readonly limit: number
  /** Every block and how many lines it holds — the counts that came instead of the lines. */
  readonly blocks: readonly OverBlock[]
  /** Whether the call was already narrowed to one block and went past the bound anyway. */
  readonly scoped: boolean
  /**
   * The block whose listing is the largest that would fit, or the empty string where none
   * would. Empty is an answer — *there is no narrowing* — and not a missing key.
   */
  readonly narrows: string
  /** The call to make instead, already split. Empty where nothing smaller would fit. */
  readonly doors: readonly Door[]
}

export const readOver: Reader<Over> = record<Over>({
  characters: orMissing(aNumber, 0),
  limit: orMissing(aNumber, 0),
  blocks: orMissing(listOf(readOverBlock), []),
  scoped: orMissing(aBoolean, false),
  narrows: orMissing(aString, ''),
  doors: orMissing(listOf(readDoor), []),
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
  readonly over: Over | null
  /**
   * **Null is not the empty list.** A project declaring `[reads] list` answers a listing
   * past that bound with its blocks and counts and withdraws the lines, and `null` is how
   * it says *not listed* where `[]` says *none selected*. A shape demanding an array here
   * reported *this app is behind the engine* for a project that is merely large and said
   * so — read off a real bounded payload, since inventing one would be this app's idea of
   * the format rather than roadkeep's.
   */
  readonly tasks: readonly TaskLine[] | null
  /**
   * The order the engine put the lines in, where it chose one (RG28). `--stale` answers
   * `oldest first`; an ordinary listing says nothing and this is empty, which is the file's
   * own order. Carried as the engine's word rather than as a flag, so a new order is drawn
   * and not refused.
   */
  readonly order: string
}

export const readListPayload: Reader<ListPayload> = record<ListPayload>({
  file: aString,
  total: aNumber,
  uncounted: listOf(readRefusedLine),
  standing: orMissing(orNull(readStanding), null),
  startable: orMissing(orNull(readStartable), null),
  over: orMissing(orNull(readOver), null),
  tasks: orNull(listOf(readTaskLine)),
  order: orMissing(aString, ''),
})

/**
 * Whether a listing saw the whole file, which is what makes its absences mean anything.
 *
 * Two ways it did not, and they are one question. A project declaring `[reads] list`
 * answers a listing past the bound with its counts and no lines, which arrives as `over`.
 * And a marker-bearing line the grammar could not accept is in `uncounted` rather than in
 * `tasks`, which is the older and quieter case.
 *
 * Here rather than at each reader, because three of them derive it and the third — RG100's
 * — is about an *absence*: an id found in no listing is unfiled where the listings were
 * whole and unknown where any of them was not, and two spellings of that would be two
 * answers to it.
 */
export function sawEverything(payload: ListPayload): boolean {
  return payload.uncounted.length === 0 && payload.over === null
}

/** The lines a listing actually carried. Empty for one the bound withdrew. */
export function listedTasks(payload: ListPayload): readonly TaskLine[] {
  return payload.tasks ?? []
}

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
  /** What is actually available, where something binds before the limit does. */
  readonly allowed: number
  /** What to compose towards, which is lower than the limit on purpose. */
  readonly aim: number
  readonly taken: number
  readonly left: number
  /** What is left against the aim rather than the limit. */
  readonly room: number
  /** The count including everything under this heading. */
  readonly subtree: number
  /** How far past the limit it already is. Above zero, the gate is what says so. */
  readonly over: number
}

export const readSectionBudget: Reader<SectionBudget> = record<SectionBudget>({
  anchor: orMissing(aString, ''),
  role: orMissing(aString, ''),
  written: orMissing(aBoolean, false),
  unit: orMissing(aString, ''),
  limit: orMissing(aNumber, 0),
  allowed: orMissing(aNumber, 0),
  aim: orMissing(aNumber, 0),
  taken: orMissing(aNumber, 0),
  left: orMissing(aNumber, 0),
  room: orMissing(aNumber, 0),
  subtree: orMissing(aNumber, 0),
  over: orMissing(aNumber, 0),
})

/**
 * What one prose field has left.
 *
 * **`allowed` and not `limit` is what a counter counts down from.** `[limits] why` is 200
 * and the rendered line's 320 binds first, so on a line carrying deps the why has less —
 * and `boundByLine` says which of the two was the binding one. A screen counting against
 * the limit would promise room the write is going to refuse.
 */
export interface FieldBudget {
  readonly field: string
  /** What the project declares for this field on its own. */
  readonly limit: number
  /** What is actually available here, once the line's own budget is counted. */
  readonly allowed: number
  /** What to compose towards. Lower than the limit deliberately. */
  readonly aim: number
  readonly taken: number
  readonly left: number
  /** Above zero, a draft is past the limit. */
  readonly over: number
  /** What is left against the aim rather than the limit. */
  readonly room: number
  /** Whether a draft was measured, or this is the allowance of an empty field. */
  readonly drafted: boolean
  /** Whether the field already holds something this would replace. */
  readonly replaced: boolean
  readonly sentences: number
  /** Whether the draft ends in a stop, which the why is held to. */
  readonly terminated: boolean
  /** Characters or words — the engine says which, since they are not the same field. */
  readonly unit: string
  /** True where the rendered line bound before the field's own limit did. */
  readonly boundByLine: boolean
  /** Where the number comes from, as an address in the project's config. */
  readonly source: string
}

export const readFieldBudget: Reader<FieldBudget> = record<FieldBudget>(
  {
    field: aString,
    limit: orMissing(aNumber, 0),
    allowed: orMissing(aNumber, 0),
    aim: orMissing(aNumber, 0),
    taken: orMissing(aNumber, 0),
    left: orMissing(aNumber, 0),
    over: orMissing(aNumber, 0),
    room: orMissing(aNumber, 0),
    drafted: orMissing(aBoolean, false),
    replaced: orMissing(aBoolean, false),
    sentences: orMissing(aNumber, 0),
    terminated: orMissing(aBoolean, false),
    unit: orMissing(aString, ''),
    boundByLine: orMissing(aBoolean, false),
    source: orMissing(aString, ''),
  },
  { boundByLine: 'bound_by_line' },
)

export interface BudgetPayload {
  /** The line this is about — the next id where the call was about one not yet written. */
  readonly id: string
  readonly status: string
  readonly deps: readonly string[]
  /** Whether the line is open, which changes what the structure costs. */
  readonly openLine: boolean
  /** The whole line's ceiling, which the prose fields share. */
  readonly lineMax: number
  /** What the line's own shape costs before any prose: the marker, the deps, the pointer. */
  readonly structure: number
  /** What is left of the line for prose, across all its fields. */
  readonly prose: number
  /**
   * The pointer the line would carry, and **null where it would carry none** — the ship
   * form prices a line whose pointer is about to go with its design.
   */
  readonly ref: string | null
  /** True where no pointer was named and the widest on file was assumed. */
  readonly refAssumed: boolean
  readonly fields: readonly FieldBudget[]
  readonly section: SectionBudget | null
}

export const readBudgetPayload: Reader<BudgetPayload> = record<BudgetPayload>(
  {
    id: orMissing(aString, ''),
    status: orMissing(aString, ''),
    deps: orMissing(listOf(aString), []),
    openLine: orMissing(aBoolean, false),
    lineMax: orMissing(aNumber, 0),
    structure: orMissing(aNumber, 0),
    prose: orMissing(aNumber, 0),
    ref: orMissing(orNull(aString), null),
    refAssumed: orMissing(aBoolean, false),
    fields: orMissing(listOf(readFieldBudget), []),
    section: orMissing(orNull(readSectionBudget), null),
  },
  { openLine: 'open_line', lineMax: 'line_max', refAssumed: 'ref_assumed' },
)

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
  /**
   * Whether the line has left for the ledger.
   *
   * Carried rather than worked out from the marker: a shipped id still briefs, and this is
   * the engine saying which side of the ledger it is on.
   */
  readonly shipped: boolean
  readonly block: string
  /**
   * The line as the file writes it, marker and pointer included (RG150). Empty from an engine
   * that did not send it. What Copy the brief hands on, since it is the file's own text.
   */
  readonly rendered: string
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
  /**
   * The routes from this line outward, **already resolved by the read that opened it**.
   *
   * The same shape `deps` sends and one field narrower: a brief spells `path`, `end` and
   * `detail` and leaves `via` out, which `readDepChain` defaults. Declaring the key is what
   * stops a screen paying for a second subprocess to be told what this one already said.
   */
  readonly chains: readonly DepChain[]
  readonly unblocks: Unblocks | null
  readonly nonGoals: readonly string[]
  readonly nonGoalsElided: number
  /**
   * The non-goal leads this line's design quotes, in the engine's measurement (RG150). A
   * quoted lead is one the design already reasoned about, which is why the task screen lists
   * those first. Empty where there is no design, and from an engine that did not send it.
   */
  readonly quotes: readonly string[]
  readonly doneWhen: readonly string[]
  readonly doneWhenElided: number
  /**
   * The criteria this line carries itself, apart from its block's (RG174).
   *
   * **Kept apart because the engine keeps them apart.** These are the ones `ship --checked`
   * names, and a lead nobody names at the ship reads in the ledger as unchecked — so a
   * caller merging the two would assert the block's finish line about this one line.
   */
  readonly doneWhenOwn: readonly string[]
  readonly doneWhenOwnElided: number
  /** For an own lead that came from another line, the id it came from. */
  readonly doneWhenFolded: Readonly<Record<string, string>>
  /** Workers holding this line right now. Empty is the ordinary case. */
  readonly held: readonly HeldClaim[]
  /** Ledger entries citing this id — what already shipped against it. */
  readonly landed: readonly string[]
  /** What the line's fields and its section have left. Null once the design is gone. */
  readonly budget: BriefBudget | null
  /**
   * What `--claim` did to the marker, and **null on a brief that only read**.
   *
   * A different fact from `held`: this says what this call did, `held` says who is on the
   * line. Neither is a proxy for the other.
   */
  readonly claimed: Claimed | null
}

/** What taking a line did to its marker. */
export interface Claimed {
  /** False where the line already carried the working marker and nothing moved. */
  readonly taken: boolean
  readonly from: string
  readonly to: string
}

export const readClaimed: Reader<Claimed> = record<Claimed>({
  taken: orMissing(aBoolean, false),
  from: orMissing(aString, ''),
  to: orMissing(aString, ''),
})

export const readBriefPayload: Reader<BriefPayload> = record<BriefPayload>(
  {
    id: aString,
    status: aString,
    shipped: orMissing(aBoolean, false),
    block: aString,
    rendered: orMissing(aString, ''),
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
    chains: orMissing(listOf(readDepChain), []),
    unblocks: orMissing(orNull(readUnblocks), null),
    nonGoals: orMissing(listOf(aString), []),
    nonGoalsElided: orMissing(aNumber, 0),
    quotes: orMissing(listOf(aString), []),
    doneWhen: orMissing(listOf(aString), []),
    doneWhenElided: orMissing(aNumber, 0),
    doneWhenOwn: orMissing(listOf(aString), []),
    doneWhenOwnElided: orMissing(aNumber, 0),
    doneWhenFolded: orMissing(dictionaryOf(aString), {}),
    held: orMissing(listOf(readHeldClaim), []),
    landed: orMissing(listOf(aString), []),
    budget: orMissing(orNull(readBriefBudget), null),
    claimed: orMissing(orNull(readClaimed), null),
  },
  {
    sectionAbsence: 'section_absence',
    depsResolved: 'deps_resolved',
    nonGoals: 'non_goals',
    nonGoalsElided: 'non_goals_elided',
    doneWhen: 'done_when',
    doneWhenElided: 'done_when_elided',
    doneWhenOwn: 'done_when_own',
    doneWhenOwnElided: 'done_when_own_elided',
    doneWhenFolded: 'done_when_folded',
  },
)

/** A line that would be ready, and what this caller lacks to be offered it. */
export interface LackingLine {
  readonly id: string
  readonly missing: readonly string[]
}

/**
 * What `brief` with no id answers when there is nothing to hand over (RG142).
 *
 * Not a brief with its fields left empty: a different shape — `brief: null` beside
 * `empty: true` — carrying why nothing was chosen and what each line that would be ready is
 * waiting on this caller for. A reader holding `id` to a string called it unreadable, and the
 * sentence that produced blamed this app's version for the most ordinary state a finished or
 * blocked backlog is in.
 */
export interface EmptyBrief {
  readonly empty: true
  /** Why nothing was chosen, in the engine's words. */
  readonly reason: string
  readonly lacking: readonly LackingLine[]
}

export const readEmptyBrief: Reader<EmptyBrief> = record<EmptyBrief>({
  empty: literalTrue,
  reason: orMissing(aString, ''),
  lacking: orMissing(
    listOf(record<LackingLine>({ id: aString, missing: orMissing(listOf(aString), []) })),
    [],
  ),
})

/**
 * A brief's answer: the line, or nothing to hand over.
 *
 * Two shapes rather than one looser one, so a caller cannot read an empty answer as a line
 * whose id is the empty string — it has to say what nothing looks like before it compiles.
 * Only a brief with no id can be the second; one naming its id answers the line or refuses.
 */
export type BriefAnswer = BriefPayload | EmptyBrief

export const readBriefAnswer: Reader<BriefAnswer> = whenFlagged(
  'empty',
  readEmptyBrief,
  readBriefPayload,
)

/** The line a brief answered, or null where the backlog had nothing to hand over. */
export function lineOf(answer: BriefAnswer): BriefPayload | null {
  return 'empty' in answer ? null : answer
}

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
  /**
   * Whether this is an open line rather than a delivery (RG182). `--open` ranks both corpora
   * in one answer, and which it is decides what a reader does about it: an open line near
   * the proposal is the line to read, a shipped one is the work already done.
   */
  readonly open: boolean
}

export const readDeliveredEntry: Reader<DeliveredEntry> = record<DeliveredEntry>(
  {
    id: aString,
    marker: orMissing(aString, ''),
    symptom: orMissing(aString, ''),
    line: orMissing(aNumber, 0),
    undoneBy: orMissing(orNull(aString), null),
    rank: orMissing(aNumber, 0),
    open: orMissing(aBoolean, false),
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

/** What this project says it is not building, and the sentence that argues each one. */
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
  /**
   * Lead → the sentence that argues it (RG77), and **null where the engine answering
   * publishes no reasons**. An engine from before the key sent leads alone, and an empty
   * map in its place would read as a list whose every reason is blank.
   */
  readonly nonGoalsWhy: Record<string, string> | null
}

export const readNonGoalsPayload: Reader<NonGoalsPayload> = record<NonGoalsPayload>(
  {
    file: orMissing(aString, ''),
    governed: orMissing(aBoolean, false),
    nonGoals: orMissing(listOf(aString), []),
    nonGoalsElided: orMissing(aNumber, 0),
    nonGoalsQuoted: orMissing(dictionaryOf(listOf(aString)), {}),
    nonGoalsWhy: orMissing(orNull(dictionaryOf(aString)), null),
  },
  {
    nonGoals: 'non_goals',
    nonGoalsElided: 'non_goals_elided',
    nonGoalsQuoted: 'non_goals_quoted',
    nonGoalsWhy: 'non_goals_why',
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

/** A line written into a file, with where it landed. */
export interface WroteLine {
  readonly file: string
  readonly line: number
  readonly rendered: string
}

const readWroteLine: Reader<WroteLine> = record<WroteLine>({
  file: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  rendered: orMissing(aString, ''),
})

/** A line taken out of a file, with the line number it was on. */
export interface RemovedLine {
  readonly file: string
  readonly removed: number
}

const readRemovedLine: Reader<RemovedLine> = record<RemovedLine>({
  file: orMissing(aString, ''),
  removed: orMissing(aNumber, 0),
})

/** The section a ship deleted, and where it had been. */
export interface DroppedSection {
  readonly anchor: string
  readonly title: string
  readonly first: number
  readonly last: number
}

/**
 * What a ship did to the roadmap, which is **two different things under one key**.
 *
 * A ship that closes the line reports the line it removed. A `--part` ship records the
 * half that landed and *leaves the line there*, reporting where it still is and the marker
 * it now carries — so a shape reading only `removed` sees a partial ship as a closure.
 */
export interface ShipRoadmap {
  readonly file: string
  /** The line taken out. Zero on a partial, which removed nothing. */
  readonly removed: number
  /** Where the line still is, on a ship that left it open. */
  readonly line: number
  /** The marker it now carries, where it stayed. */
  readonly status: string
  /** True where the line is still a task. The engine's word for it, not a comparison. */
  readonly open: boolean
}

const readShipRoadmap: Reader<ShipRoadmap> = record<ShipRoadmap>({
  file: orMissing(aString, ''),
  removed: orMissing(aNumber, 0),
  line: orMissing(aNumber, 0),
  status: orMissing(aString, ''),
  open: orMissing(aBoolean, false),
})

export interface ShipPayload {
  readonly id: string
  /** The half that landed, where this was a partial. Empty on an ordinary ship. */
  readonly part: string
  /** What is still left, which becomes the open line's why. */
  readonly remainder: string
  /** The ledger entry written. Null where this call only closed an already-recorded line. */
  readonly changelog: WroteLine | null
  readonly roadmap: ShipRoadmap | null
  /** What became of the prose file: the section dropped, and where its durable half went. */
  readonly improvements: {
    readonly file: string
    readonly dropped: DroppedSection | null
    readonly recordedIn: string | null
    readonly superseded: string | null
  } | null
  /** Ids whose dep annotations were re-derived because this one closed. */
  readonly refreshed: readonly string[]
  /** Criteria of this task that were named as verified. */
  readonly checked: readonly string[]
  /** Criteria nobody named, which read as unchecked. */
  readonly unmet: readonly string[]
  /** The decision this ship filed, where `--decides` named one. */
  readonly decisions: WroteLine | null
}

export const readShipPayload: Reader<ShipPayload> = record<ShipPayload>({
  id: aString,
  part: orMissing(aString, ''),
  remainder: orMissing(aString, ''),
  changelog: orMissing(orNull(readWroteLine), null),
  roadmap: orMissing(orNull(readShipRoadmap), null),
  improvements: orMissing(
    orNull(
      record<NonNullable<ShipPayload['improvements']>>(
        {
          file: orMissing(aString, ''),
          dropped: orMissing(
            orNull(
              record<DroppedSection>({
                anchor: orMissing(aString, ''),
                title: orMissing(aString, ''),
                first: orMissing(aNumber, 0),
                last: orMissing(aNumber, 0),
              }),
            ),
            null,
          ),
          recordedIn: orMissing(orNull(aString), null),
          superseded: orMissing(orNull(aString), null),
        },
        { recordedIn: 'recorded_in' },
      ),
    ),
    null,
  ),
  refreshed: orMissing(listOf(aString), []),
  checked: orMissing(listOf(aString), []),
  unmet: orMissing(listOf(aString), []),
  decisions: orMissing(orNull(readWroteLine), null),
})

export interface RetirePayload {
  readonly id: string
  readonly marker: string
  /** The id taking the work over, or null where the line was simply abandoned. */
  readonly supersededBy: string | null
  /** The open line that absorbed it, where one did. Empty is the ordinary case. */
  readonly folded: string
  readonly changelog: WroteLine | null
  readonly roadmap: RemovedLine | null
  /** The section anchor dropped with it, or the empty string. */
  readonly dropped: string
  /** Lines still naming this id, which a retirement leaves pointing at nothing. */
  readonly dependents: readonly string[]
  readonly refreshed: readonly string[]
}

export const readRetirePayload: Reader<RetirePayload> = record<RetirePayload>(
  {
    id: aString,
    marker: orMissing(aString, ''),
    supersededBy: orMissing(orNull(aString), null),
    folded: orMissing(aString, ''),
    changelog: orMissing(orNull(readWroteLine), null),
    roadmap: orMissing(orNull(readRemovedLine), null),
    dropped: orMissing(aString, ''),
    dependents: orMissing(listOf(aString), []),
    refreshed: orMissing(listOf(aString), []),
  },
  { supersededBy: 'superseded_by' },
)

export interface DeferPayload {
  readonly id: string
  readonly marker: string
  readonly deferred: WroteLine | null
  readonly roadmap: RemovedLine | null
  /** The section carried across with the line, rather than dropped. */
  readonly carried: {
    readonly anchor: string
    readonly role: string
    readonly file: string
    readonly absence: string | null
  } | null
  readonly dependents: readonly string[]
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
}

export const readDeferPayload: Reader<DeferPayload> = record<DeferPayload>({
  id: aString,
  marker: orMissing(aString, ''),
  deferred: orMissing(orNull(readWroteLine), null),
  roadmap: orMissing(orNull(readRemovedLine), null),
  carried: orMissing(
    orNull(
      record<NonNullable<DeferPayload['carried']>>({
        anchor: orMissing(aString, ''),
        role: orMissing(aString, ''),
        file: orMissing(aString, ''),
        absence: orMissing(orNull(aString), null),
      }),
    ),
    null,
  ),
  dependents: orMissing(listOf(aString), []),
  refreshed: orMissing(listOf(aString), []),
  wrote: orMissing(listOf(aString), []),
})

export interface ResumePayload {
  readonly id: string
  /** The open marker it came back with. */
  readonly marker: string
  readonly roadmap: WroteLine | null
  readonly deferred: RemovedLine | null
  /**
   * The reason it stood on, **unwrapped**. The one place a pause's own sentence is
   * published apart from the design's why it was wrapped around.
   */
  readonly was: string
  /** Whether the line coming back had to be reconciled with something that moved. */
  readonly reconciled: boolean
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
}

export const readResumePayload: Reader<ResumePayload> = record<ResumePayload>({
  id: aString,
  marker: orMissing(aString, ''),
  roadmap: orMissing(orNull(readWroteLine), null),
  deferred: orMissing(orNull(readRemovedLine), null),
  was: orMissing(aString, ''),
  reconciled: orMissing(aBoolean, false),
  refreshed: orMissing(listOf(aString), []),
  wrote: orMissing(listOf(aString), []),
})

/**
 * What a section write answered with: the section as it now stands.
 *
 * The same shape both verbs answer in, plus what the amend changed. The counts are the
 * file's own — the number deciding whether a design needs splitting has to be the one the
 * gate will read, not one measured on a draft in memory.
 */
export interface SectionWritten {
  readonly anchor: string
  readonly title: string
  readonly level: number
  readonly file: string
  readonly first: number
  readonly last: number
  readonly words: number
  readonly ownWords: number
  /** Which parts an amend touched — `body`, `title`. Empty for an add. */
  readonly changed: readonly string[]
  /** Whether the prose came from stdin rather than an argument. */
  readonly readBody: boolean
  readonly wrote: readonly string[]
}

export const readSectionWritten: Reader<SectionWritten> = record<SectionWritten>(
  {
    anchor: aString,
    title: orMissing(aString, ''),
    level: orMissing(aNumber, 0),
    file: orMissing(aString, ''),
    first: orMissing(aNumber, 0),
    last: orMissing(aNumber, 0),
    words: orMissing(aNumber, 0),
    ownWords: orMissing(aNumber, 0),
    changed: orMissing(listOf(aString), []),
    readBody: orMissing(aBoolean, false),
    wrote: orMissing(listOf(aString), []),
  },
  { ownWords: 'own_words', readBody: 'read_body' },
)

export interface AmendPayload {
  readonly id: string
  readonly file: string
  readonly line: number
  /** Which fields it touched: `why`, `deps`, `ref`. */
  readonly changed: readonly string[]
  readonly rendered: string
  /**
   * What each changed field held before, keyed by field name.
   *
   * **A map here and a string on `restate`.** One key, two types, one verb apart — so the
   * two are read as two shapes and never with one reader.
   *
   * **And a value that is a list where the field is one** (RG179): amending `--requires` or
   * a dep answers `was.requires` as the array it was, and a reader declaring a string refused
   * a write the engine had already made. Nothing is joined on the way through — a sentence
   * built here would be this app composing a field — so a caller drawing *what it was before*
   * handles both, which it has to anyway.
   */
  readonly was: Record<string, string | readonly string[]>
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
}

export const readAmendPayload: Reader<AmendPayload> = record<AmendPayload>({
  id: aString,
  file: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  changed: orMissing(listOf(aString), []),
  rendered: orMissing(aString, ''),
  was: orMissing(dictionaryOf(oneOrMany(aString)), {}),
  refreshed: orMissing(listOf(aString), []),
  wrote: orMissing(listOf(aString), []),
})

/**
 * What a restate did not do, and names for somebody else to decide about.
 *
 * The why and the design were written from the claim that was replaced, and whether they
 * still hold is a judgement. The verb names the follow-ups and leaves them.
 */
export interface RestatedPremise {
  /** The section anchor still holding prose written from the old claim. */
  readonly design: string
  readonly role: string
  /** The commands that would correct the rest, in the engine's own words. */
  readonly next: readonly string[]
}

export interface RestatePayload {
  readonly id: string
  readonly file: string
  readonly line: number
  /** The symptom before. **A string here, where `amend` sends a map.** */
  readonly was: string
  readonly now: string
  readonly changed: boolean
  /** True where this was a slip of the pen rather than a false premise. */
  readonly typo: boolean
  readonly premise: RestatedPremise | null
  readonly rendered: string
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
}

export const readRestatePayload: Reader<RestatePayload> = record<RestatePayload>({
  id: aString,
  file: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  was: orMissing(aString, ''),
  now: orMissing(aString, ''),
  changed: orMissing(aBoolean, false),
  typo: orMissing(aBoolean, false),
  premise: orMissing(
    orNull(
      record<RestatedPremise>({
        design: orMissing(aString, ''),
        role: orMissing(aString, ''),
        next: orMissing(listOf(aString), []),
      }),
    ),
    null,
  ),
  rendered: orMissing(aString, ''),
  refreshed: orMissing(listOf(aString), []),
  wrote: orMissing(listOf(aString), []),
})

export interface RenumberPayload {
  readonly id: string
  readonly to: string
  readonly role: string
  readonly file: string
  readonly line: number
  readonly rendered: string
  /** The section that moved with it, re-anchored to the new id. */
  readonly section: RationaleSection | null
  /** Subsections carried under it. */
  readonly subsections: readonly string[]
  /** Whether the line's own criteria moved too. */
  readonly criteria: boolean
  /** Lines whose deps were rewritten to the new id. */
  readonly moved: readonly string[]
  readonly refreshed: readonly string[]
  readonly files: readonly string[]
  readonly wrote: readonly string[]
}

export const readRenumberPayload: Reader<RenumberPayload> = record<RenumberPayload>({
  id: aString,
  to: orMissing(aString, ''),
  role: orMissing(aString, ''),
  file: orMissing(aString, ''),
  line: orMissing(aNumber, 0),
  rendered: orMissing(aString, ''),
  section: orMissing(orNull(readSection), null),
  subsections: orMissing(listOf(aString), []),
  criteria: orMissing(aBoolean, false),
  moved: orMissing(listOf(aString), []),
  refreshed: orMissing(listOf(aString), []),
  files: orMissing(listOf(aString), []),
  wrote: orMissing(listOf(aString), []),
})

export interface LintFinding {
  readonly code: string
  readonly file: string
  readonly line: number | null
  /** Where on the line, where the gate can say. Null for a finding about the whole line. */
  readonly column: number | null
  readonly id: string | null
  readonly message: string
  /**
   * Every finding names the command that closes it, in the same shape `explain` publishes
   * for a refusal's code. One reader for both: a refusal and a gate finding are the same
   * thing at two moments, and offering the door in one place only is how they drift.
   */
  readonly remedy: Remedy | null
}

export const readFinding: Reader<LintFinding> = record<LintFinding>({
  code: aString,
  file: orMissing(aString, ''),
  line: orMissing(orNull(aNumber), null),
  column: orMissing(orNull(aNumber), null),
  id: orMissing(orNull(aString), null),
  message: aString,
  remedy: orMissing(orNull(readRemedy), null),
})

/**
 * One finding as a repair pass reports it, which is the same thing addressed differently.
 *
 * `where` is the file and line already joined, because a repair's report is about a place
 * rather than about a file with a line in it. Everything else is the finding's own.
 */
export interface RepairLeft {
  readonly code: string
  readonly where: string
  readonly message: string
  readonly remedy: Remedy | null
}

const readRepairLeft: Reader<RepairLeft> = record<RepairLeft>({
  code: aString,
  where: orMissing(aString, ''),
  message: orMissing(aString, ''),
  remedy: orMissing(orNull(readRemedy), null),
})

/** One move a repair pass made, or would have made under a dry run. */
export interface RepairStep {
  readonly code: string
  readonly argv: readonly string[]
  readonly what: string
  /** Whether it ran. False for every step of a dry run. */
  readonly ran: boolean
}

const readRepairStep: Reader<RepairStep> = record<RepairStep>({
  code: orMissing(aString, ''),
  argv: orMissing(listOf(aString), []),
  what: orMissing(aString, ''),
  ran: orMissing(aBoolean, false),
})

export interface RepairPayload {
  readonly root: string
  readonly clean: boolean
  /** Whether this printed the commands and ran none of them. */
  readonly dryRun: boolean
  readonly passes: number
  /** True where the passes stopped because they stopped helping, not because it is clean. */
  readonly exhausted: boolean
  readonly steps: readonly RepairStep[]
  /** What the passes could not close. The report after, in a finding's own shape. */
  readonly left: readonly RepairLeft[]
}

export const readRepairPayload: Reader<RepairPayload> = record<RepairPayload>(
  {
    root: orMissing(aString, ''),
    clean: orMissing(aBoolean, false),
    dryRun: orMissing(aBoolean, false),
    passes: orMissing(aNumber, 0),
    exhausted: orMissing(aBoolean, false),
    steps: orMissing(listOf(readRepairStep), []),
    left: orMissing(listOf(readRepairLeft), []),
  },
  { dryRun: 'dry_run' },
)

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
  /**
   * Which of the three tiers answered: in progress, the priority queue, or lowest ready id —
   * and **null where none did**. A backlog whose open lines all wait on something answers
   * `pick: null` and `tier: null` together, and a reader holding this to a string drew that
   * project as unreadable in the portfolio (RG141).
   */
  readonly tier: string | null
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
  tier: orMissing(orNull(aString), null),
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
  /**
   * What this build uses when nothing declares it, spelled the same way.
   *
   * Carried because an undeclared key is not an absent one: `markers.working` is undeclared
   * in most projects and every one of them still has a working marker.
   */
  readonly fallback: string | null
}

export interface ConfigPayload {
  readonly version: string
  /**
   * The file the configuration came from, and **null where nothing governs the folder**.
   * Held to a string until RG13, so the one answer that says "not a project" read as a
   * payload this app could not parse — and a folder was rejected by a read failing.
   */
  readonly source: string | null
  /**
   * Whether a roadkeep project governs the folder asked about (RK1631). An engine from
   * before it did not say, and its null `source` is the same answer, so that is what this
   * falls back to — only a null, and never a key that is merely absent.
   */
  readonly governed: boolean
  /** The project root the engine resolved the folder to, in the engine's spelling. */
  readonly root: string
  readonly keys: readonly ConfigKey[]
}

interface ConfigAsPrinted extends Omit<ConfigPayload, 'governed'> {
  readonly governed: boolean | null
}

const readConfigAsPrinted: Reader<ConfigAsPrinted> = record<ConfigAsPrinted>({
  version: aString,
  source: orMissing(orNull(aString), ''),
  governed: orMissing(orNull(aBoolean), null),
  root: orMissing(aString, ''),
  keys: listOf(
    record<ConfigKey>(
      {
        table: orMissing(aString, ''),
        key: aString,
        address: orMissing(aString, ''),
        declared: orMissing(aBoolean, false),
        set: orMissing(orNull(aString), null),
        fallback: orMissing(orNull(aString), null),
      },
      // The engine spells it `default`, which is a reserved word here and a poor field
      // name besides. The rename is this reader's and goes no further.
      { fallback: 'default' },
    ),
  ),
})

export const readConfigPayload: Reader<ConfigPayload> = (value, path) => {
  const printed = readConfigAsPrinted(value, path)
  if (!printed.ok) return printed
  const { governed, ...rest } = printed.value
  return { ok: true, value: { ...rest, governed: governed ?? rest.source !== null } }
}

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
  const reasons: string[] = []
  if (payload.uncounted.length > 0) {
    reasons.push(
      `${String(payload.uncounted.length)} marker-bearing line(s) the grammar did not accept, reported beside this answer`,
    )
  }
  // The strongest case of "smaller than the file": no lines at all, and the counts in
  // their place. It belongs here and not in a failure — the project set the bound and the
  // engine applied it, which is a narrower answer and not an answer this app cannot read.
  if (payload.over !== null) {
    const bound = payload.over
    reasons.push(
      `${String(payload.total)} line(s) withheld: this listing is ${String(bound.characters)} ` +
        `characters against the ${String(bound.limit)} this project declares for a read`,
    )
  }
  return { complete: reasons.length === 0, reasons }
}

/**
 * The narrower call to make, where the engine named one.
 *
 * A bound with no door is a real state: `list --block A` that is still too large has
 * nothing smaller to offer, and saying so is better than offering a call that answers the
 * same way. The argv is the engine's own and is handed to a transport, never to a shell.
 */
export function insteadOf(payload: ListPayload): readonly Door[] {
  return payload.over === null ? [] : offerable(payload.over.doors)
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
