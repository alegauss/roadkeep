/**
 * A verb is data.
 *
 * The alternative — a function per verb — is what makes a client grow a second code path
 * every time the engine grows a flag, and roadkeep's own MCP server makes the same
 * argument about dispatching everything through one parser: two paths that both add a
 * task is the drift being removed. So a verb here is the argv it builds, nothing more, and
 * adding one is an entry in this table rather than a new call.
 *
 * Two rules hold for every entry. **`--json` is always asked for**: this app reads payloads
 * and never prose, and a screen that scraped human output would be a rule compiled into
 * the client. And **nothing here validates**: a limit, a marker set or a grammar belongs to
 * the engine, which refuses far better than a copy of its rules would.
 *
 * The set is deliberately small and read-only. Every entry was checked against
 * `roadkeep <verb> --help` rather than remembered, and the write verbs are absent because
 * they are their own block.
 */

/** What each verb takes. The key is the verb's own name on the command line. */
export interface VerbInputs {
  list: {
    block?: string
    /** Which governed file, default the roadmap. */
    role?: string
    marker?: string
    /** Requirements this caller has; an open line naming an undeclared one counts as waiting. */
    have?: readonly string[]
    /**
     * The deferred store, which this names without a `--role`. The ordering it adds —
     * how long each pause has stood — is printed for a terminal and is not in the
     * payload, so with `--json` this asks for the store and nothing more.
     */
    stale?: boolean
    /**
     * Only the lines nothing is holding up (RG170): every dep settled and no requirement
     * this caller has not declared. The engine's own narrowing, which is what keeps
     * "startable only" from being readiness derived in a client.
     */
    startable?: boolean
  }
  show: {
    id: string
    /** Keep the line and where the prose is, drop the prose. */
    noBody?: boolean
  }
  stats: {
    block?: string
    role?: string
    have?: readonly string[]
  }
  brief: {
    /** Omitted, the engine picks the line itself. */
    id?: string
    block?: string
    designed?: boolean
    have?: readonly string[]
    /**
     * Take the line as well as describing it: the marker moves in the same transaction.
     *
     * **A read that writes**, and the only one in this table. It sits here rather than in
     * the write table because it is the same call either way — a brief with a flag — and
     * splitting it would make the transaction two things a caller could get half of.
     */
    claim?: boolean
  }
  /**
   * One task's edges, resolved: the blockers, the chains from it outward, what shipping
   * it would free, and any cycle it is caught in.
   */
  deps: { id: string }
  /**
   * What one block already delivered — the read before an `add`. `near` bounds it to the
   * five entries nearest a sentence about to be proposed, in order and with no score.
   */
  delivered: {
    block: string
    near?: string
    /**
     * Rank the block's open lines beside its deliveries (RG182). A duplicate collides with
     * what was filed as readily as with what shipped, and only this says which each is.
     */
    open?: boolean
  }
  /** Every id the ledger undid, and the entry that undid it. `id` asks about one. */
  reversals: { id?: string }
  /**
   * What a line's fields have left, priced before any of them is written.
   *
   * Everything is optional because the interesting call is the one about a line that does
   * not exist yet: a block and a marker and a dep are enough to say what the symptom and
   * the why will have. The drafts are measured and never refused by this read.
   */
  budget: {
    /** An existing line. Omitted, the line an `add` would write next. */
    id?: string
    block?: string
    status?: string
    deps?: readonly string[]
    requires?: readonly string[]
    /** A draft, measured against its allowance rather than refused by it. */
    symptom?: string
    why?: string
    /** A section to price instead, by anchor, and which prose file it is against. */
    anchor?: string
    role?: string
    body?: string
    bodyFile?: string
    /** Price the sentence a `ship` writes, which is the ledger's limit and not the line's. */
    ship?: boolean
    /** Price the reason a `defer` writes: the store's limit, less what it carries forward. */
    defer?: boolean
    /** Price a retirement's reason. Bare is an abandonment. */
    retire?: boolean
    /** With `retire`: the id taking it over, which costs more of the field than a bare one. */
    supersededBy?: string
  }
  /** What this project says it is not building. Takes nothing: the list is the project's. */
  nonGoalList: Record<string, never>
  /** What would finish a block, or what one line carries of its own. */
  criterionList: {
    block?: string
    /** One task's own criteria, by id. Mutually exclusive with `block` at the engine. */
    task?: string
  }
  lint: {
    /** Report only what this tree added since a revision. */
    baseline?: string
  }
  /** Which copy of roadkeep writes for this project. Takes nothing; asked before anything else. */
  engines: Record<string, never>
  /** What one gate code means and which doors close it. Takes the code a refusal named. */
  explain: { code: string }
  /** Every verb this build publishes and every argument each takes. Asked once per project. */
  commands: Record<string, never>
  /** What the project declares, including which files are governed. */
  config: Record<string, never>
  /** What to work on next, and which of the three tiers answered. */
  pick: {
    block?: string
    designed?: boolean
    have?: readonly string[]
  }
  /**
   * Every block the roadmap declares, each with its heading's title and its standing — the
   * read a block chip is drawn from (RG148). `stats` counts per block and names none.
   */
  blockList: Record<string, never>
  /**
   * One section by its anchor, in whichever prose file the role names — a decision's
   * reasoning, a design's heading (RG149). The decisions role keeps its own sections, which
   * `brief` never joins because they outlive the line that wrote them.
   */
  sectionShow: {
    anchor: string
    role?: string
  }
  /**
   * The claim registry against the roadmap (RG153): who is on which line, which entries were
   * stepped over, and which are stale. Takes nothing — the registry is the project's.
   */
  claims: Record<string, never>
}

export type VerbName = keyof VerbInputs

type ArgvFor<K extends VerbName> = (input: VerbInputs[K]) => readonly string[]

/**
 * What a verb is called on the command line, where that is more than one word.
 *
 * Twenty-three of the eighty-nine entries `commands` publishes are not top-level verbs:
 * `section show`, `capture filed`, `non-goal list` arrive as single names with a space in
 * them, and the families behind them — `section`, `block`, `criterion`, `record` — are
 * exactly where the write path goes.
 *
 * So a verb's **key is a single identifier this app uses** and its **spelling is an
 * array**. Not a key with a space in it split back apart: argv is an array precisely so
 * that nothing here ever turns a command line into arguments, and a table that stored the
 * words joined would be one split away from undoing that. A verb absent from this map is
 * spelled by its own key, which is the ordinary case.
 */
export type Spelling = Readonly<Record<string, readonly string[]>>

export const VERB_WORDS: Spelling = {
  nonGoalList: ['non-goal', 'list'],
  criterionList: ['criterion', 'list'],
  blockList: ['block', 'list'],
  sectionShow: ['section', 'show'],
}

/**
 * The words one verb puts on the command line.
 *
 * Takes the map rather than closing over one, because reads and writes keep separate
 * tables on purpose and this is the single implementation both of them use.
 */
export function spell(verb: string, spelled: Spelling): readonly string[] {
  return spelled[verb] ?? [verb]
}

/** The name `commands` publishes for a verb, which is its words joined. */
export function publishedAs(verb: string, spelled: Spelling): string {
  return spell(verb, spelled).join(' ')
}

/** Repeat a flag once per value, which is how the engine spells a repeatable option. */
function repeated(flag: string, values: readonly string[] | undefined): string[] {
  return (values ?? []).flatMap((value) => [flag, value])
}

function optional(flag: string, value: string | undefined): string[] {
  return value === undefined ? [] : [flag, value]
}

export const VERBS: { [K in VerbName]: ArgvFor<K> } = {
  list: (input) => [
    ...optional('--block', input.block),
    ...optional('--role', input.role),
    ...optional('--marker', input.marker),
    ...repeated('--have', input.have),
    ...(input.stale === true ? ['--stale'] : []),
    ...(input.startable === true ? ['--startable'] : []),
  ],
  show: (input) => [input.id, ...(input.noBody === true ? ['--no-body'] : [])],
  stats: (input) => [
    ...optional('--block', input.block),
    ...optional('--role', input.role),
    ...repeated('--have', input.have),
  ],
  brief: (input) => [
    ...(input.id === undefined ? [] : [input.id]),
    ...optional('--block', input.block),
    ...(input.designed === true ? ['--designed'] : []),
    ...repeated('--have', input.have),
    ...(input.claim === true ? ['--claim'] : []),
  ],
  deps: (input) => [input.id],
  delivered: (input) => [
    input.block,
    ...optional('--near', input.near),
    ...(input.open === true ? ['--open'] : []),
  ],
  reversals: (input) => [...optional('--id', input.id)],
  budget: (input) => [
    ...(input.id === undefined ? [] : [input.id]),
    ...optional('--block', input.block),
    ...repeated('--dep', input.deps),
    ...repeated('--requires', input.requires),
    ...optional('--status', input.status),
    ...optional('--symptom', input.symptom),
    ...optional('--why', input.why),
    ...optional('--anchor', input.anchor),
    ...optional('--role', input.role),
    ...optional('--body', input.body),
    ...optional('--body-file', input.bodyFile),
    ...(input.ship === true ? ['--ship'] : []),
    ...(input.defer === true ? ['--defer'] : []),
    // One flag, an optional value: bare is an abandonment, named is a supersession.
    ...(input.retire === true
      ? ['--retire', ...(input.supersededBy === undefined ? [] : [input.supersededBy])]
      : []),
  ],
  nonGoalList: () => [],
  criterionList: (input) => [
    ...optional('--block', input.block),
    ...optional('--task', input.task),
  ],
  lint: (input) => [...optional('--baseline', input.baseline)],
  engines: () => [],
  explain: (input) => [input.code],
  commands: () => [],
  config: () => [],
  pick: (input) => [
    ...optional('--block', input.block),
    ...(input.designed === true ? ['--designed'] : []),
    ...repeated('--have', input.have),
  ],
  blockList: () => [],
  sectionShow: (input) => [input.anchor, ...optional('--role', input.role)],
  claims: () => [],
}

/**
 * One input per verb with every field filled in, so the flags a builder can emit can be
 * derived by running it rather than listed beside it.
 *
 * A list beside the builders would drift the moment somebody adds a flag to one and not
 * the other, and it would drift in the direction that matters: the capability check would
 * go on approving a flag nothing ever verifies this build accepts. These values are never
 * sent to an engine — they exist to be handed to `VERBS[verb]` and have their output read.
 */
export const EVERY_INPUT: { [K in VerbName]: VerbInputs[K] } = {
  list: { block: 'A', role: 'roadmap', marker: '📋', have: ['signing-cert'], stale: true },
  show: { id: 'RG1', noBody: true },
  stats: { block: 'A', role: 'roadmap', have: ['signing-cert'] },
  brief: { id: 'RG1', block: 'A', designed: true, have: ['signing-cert'], claim: true },
  deps: { id: 'RG1' },
  delivered: { block: 'A', near: 'a symptom about to be proposed', open: true },
  reversals: { id: 'RG1' },
  budget: {
    id: 'RG1',
    block: 'A',
    status: '📋',
    deps: ['RG2'],
    requires: ['signing-cert'],
    symptom: 'a symptom',
    why: 'A sentence.',
    anchor: 'RG1',
    role: 'improvements',
    body: 'Prose.',
    bodyFile: 'a.md',
    ship: true,
    defer: true,
    retire: true,
    supersededBy: 'RG9',
  },
  nonGoalList: {},
  criterionList: { block: 'A', task: 'RG1' },
  lint: { baseline: 'HEAD' },
  engines: {},
  explain: { code: 'symptom.too-long' },
  commands: {},
  config: {},
  pick: { block: 'A', designed: true, have: ['signing-cert'] },
  blockList: {},
  sectionShow: { anchor: 'RG1', role: 'decisions' },
  claims: {},
}
