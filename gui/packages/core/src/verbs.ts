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
  }
  /** Every id the ledger undid, and the entry that undid it. `id` asks about one. */
  reversals: { id?: string }
  /** What this project says it is not building. Takes nothing: the list is the project's. */
  'non-goal list': Record<string, never>
  /** What would finish a block, or what one line carries of its own. */
  'criterion list': {
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
}

export type VerbName = keyof VerbInputs

type ArgvFor<K extends VerbName> = (input: VerbInputs[K]) => readonly string[]

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
  ],
  deps: (input) => [input.id],
  delivered: (input) => [input.block, ...optional('--near', input.near)],
  reversals: (input) => [...optional('--id', input.id)],
  'non-goal list': () => [],
  'criterion list': (input) => [
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
  list: { block: 'A', role: 'roadmap', marker: '📋', have: ['signing-cert'] },
  show: { id: 'RG1', noBody: true },
  stats: { block: 'A', role: 'roadmap', have: ['signing-cert'] },
  brief: { id: 'RG1', block: 'A', designed: true, have: ['signing-cert'] },
  deps: { id: 'RG1' },
  delivered: { block: 'A', near: 'a symptom about to be proposed' },
  reversals: { id: 'RG1' },
  'non-goal list': {},
  'criterion list': { block: 'A', task: 'RG1' },
  lint: { baseline: 'HEAD' },
  engines: {},
  explain: { code: 'symptom.too-long' },
  commands: {},
  config: {},
  pick: { block: 'A', designed: true, have: ['signing-cert'] },
}
