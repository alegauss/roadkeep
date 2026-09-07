import type { Spelling } from './verbs'

/**
 * A write is data too.
 *
 * The mirror of `verbs.ts`, and deliberately a second table rather than more rows in that
 * one: a read is offered freely and a write is not, and a screen asking "may I show this
 * door" wants the two sets apart. Everything else is the same argument — a verb here is
 * the argv it builds, and adding one is a row rather than a code path.
 *
 * **This app composes an argv and the command writes.** Nothing in this file opens a
 * governed file, renders a line or fills a field: the person's own words go into the
 * array and the verb decides what becomes of them. That is `No write to a governed file`
 * and `No field this app composes`, held by construction rather than by care.
 *
 * `--json` is appended by the composer for the same reason every read asks for it, and it
 * matters more here: a refusal read as prose is a refusal whose field nobody can mark.
 */

/** What each write verb takes. The key is the verb's own name on the command line. */
export interface WriteInputs {
  /**
   * File one task line, and the rationale its pointer needs in the same transaction.
   *
   * `section` and `sectionBody` are one move, not two: a line whose section is missing is
   * a `ref.unresolved` finding the moment it is written, so the follow-up belongs in the
   * call that creates the need for it.
   */
  add: {
    block: string
    symptom: string
    why: string
    /** The status marker. Omitted, the engine uses the first the project declares. */
    status?: string
    deps?: readonly string[]
    requires?: readonly string[]
    section?: string
    sectionBody?: string
  }
  /**
   * Move one task's marker in the roadmap.
   *
   * Both arguments are positional and the marker is not an enum here: it comes from the
   * open set `config` publishes, which is four emoji in this repository and something
   * else in the next one.
   */
  status: {
    id: string
    marker: string
  }
  /**
   * Close a line: the ledger entry, the roadmap line cleared and the section dropped, in
   * one transaction or none.
   *
   * `why` is the outcome and the person's — the roadmap's sentence states a problem, and
   * inheriting it would file a defect report under a heading that means done.
   */
  ship: {
    id: string
    why?: string
    /** Record only the half that landed and leave the line open. */
    part?: string
    /** What is still left, with `part`: it becomes the open line's why. */
    remainder?: string
    lines?: string
    /** What the deleted design turned out to be wrong about. */
    supersededDesign?: string
    /** Where the deleted design's durable half moved to. Must resolve. */
    recordedIn?: string
    /** The constraint the deleted design leaves behind, filed in the decisions role. */
    decides?: string
    decidesRef?: string
    /** A criterion of this task that was verified, repeatable. */
    checked?: readonly string[]
  }
  /** End a line without a ship. Terminal: the id never comes back. */
  retire: {
    id: string
    /** The id taking the work over — a replacement rather than an abandonment. */
    supersededBy?: string
    /** The open line that absorbs this one, its symptom becoming a criterion there. */
    foldsInto?: string
    reason?: string
  }
  /** Set a line aside, keeping its id, deps, symptom and section. */
  defer: {
    id: string
    reason?: string
  }
  /** Bring a set-aside line back to its block. */
  resume: {
    id: string
    /** The open marker it returns with; omitted, the first the project declares. */
    marker?: string
  }
}

export type WriteName = keyof WriteInputs

type ArgvFor<K extends WriteName> = (input: WriteInputs[K]) => readonly string[]

/**
 * How each write is spelled on the command line, where that is more than one word.
 *
 * Empty today because `add` is one word, and declared anyway because everything coming
 * next is not: `section add`, `criterion add`, `block add`, `non-goal add`. The rule is
 * `verbs.ts`'s — the key is an identifier, the spelling is an array, and nothing splits a
 * string into arguments.
 */
export const WRITE_WORDS: Spelling = {}

function optional(flag: string, value: string | undefined): string[] {
  return value === undefined || value === '' ? [] : [flag, value]
}

/**
 * Repeat a flag once per value.
 *
 * `--dep` and not `--dep`s: the schema publishes the field as `deps` and this CLI spells
 * the argument singular, which is the kind of thing a table gets right once.
 */
function repeated(flag: string, values: readonly string[] | undefined): string[] {
  return (values ?? []).flatMap((value) => [flag, value])
}

export const WRITES: { [K in WriteName]: ArgvFor<K> } = {
  add: (input) => [
    '--block',
    input.block,
    '--symptom',
    input.symptom,
    '--why',
    input.why,
    ...optional('--status', input.status),
    ...repeated('--dep', input.deps),
    ...repeated('--requires', input.requires),
    ...optional('--section', input.section),
    ...optional('--section-body', input.sectionBody),
  ],
  status: (input) => [input.id, input.marker],
  ship: (input) => [
    input.id,
    ...optional('--why', input.why),
    ...optional('--part', input.part),
    ...optional('--remainder', input.remainder),
    ...optional('--lines', input.lines),
    ...optional('--superseded-design', input.supersededDesign),
    ...optional('--recorded-in', input.recordedIn),
    ...optional('--decides', input.decides),
    ...optional('--decides-ref', input.decidesRef),
    ...repeated('--checked', input.checked),
  ],
  retire: (input) => [
    input.id,
    ...optional('--superseded-by', input.supersededBy),
    ...optional('--folds-into', input.foldsInto),
    ...optional('--reason', input.reason),
  ],
  defer: (input) => [input.id, ...optional('--reason', input.reason)],
  resume: (input) => [input.id, ...optional('--marker', input.marker)],
}

/**
 * One input per write with every field filled in, so the flags a builder can emit are
 * derived by running it rather than listed beside it.
 *
 * Never sent to an engine. These exist to be handed to `WRITES[verb]` and have their
 * output read, which is what keeps the capability check honest when somebody adds a flag
 * to a builder and forgets the list that was supposed to mirror it.
 */
export const EVERY_WRITE_INPUT: { [K in WriteName]: WriteInputs[K] } = {
  add: {
    block: 'A',
    symptom: 'a symptom',
    why: 'A sentence.',
    status: '📋',
    deps: ['RG1'],
    requires: ['signing-cert'],
    section: 'A heading',
    sectionBody: 'Prose.',
  },
  status: { id: 'RG1', marker: '🛠' },
  ship: {
    id: 'RG1',
    why: 'An outcome.',
    part: 'the local half',
    remainder: 'The rest.',
    lines: '2',
    supersededDesign: 'A note.',
    recordedIn: 'packages/core/src/index.ts',
    decides: 'A constraint.',
    decidesRef: '1.2',
    checked: ['A criterion'],
  },
  retire: { id: 'RG1', supersededBy: 'RG2', foldsInto: 'RG3', reason: 'A sentence.' },
  defer: { id: 'RG1', reason: 'A sentence.' },
  resume: { id: 'RG1', marker: '📋' },
}
