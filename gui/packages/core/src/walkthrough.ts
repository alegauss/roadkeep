import { placesIn, type GlossPlace } from './gloss'
import type { OriginPayload } from './payloads'
import { asRecord } from './reading'

/**
 * How to check a shipped entry (RG291): what is asked of Claude Code, and the shape it answers in.
 *
 * A ledger entry says what now works, which is the outcome and never the change. Somebody told
 * that entry awaits a verdict has one sentence and a project, and has to work out from them what
 * to open — so a walkthrough written from the sentence alone is generic, and a generic one is
 * worse than none: four invented clicks, followed, teach nothing about what shipped.
 *
 * **So the run is anchored where the truth is.** `origin` resolves the commit that wrote the
 * entry, and the diff of that commit is what the agent reads. The ledger's sentence goes in as
 * the subject and the commit as the evidence; nothing here paraphrases either.
 *
 * **The shape mirrors `gloss.ts`.** `before` is what has to be true first — a build, a project
 * open, a checkout somewhere. `steps` is pairs, one `does` and the `sees` it should produce,
 * because a step with no expected result is not a step anybody can check. `where` is the gloss's
 * own slot, reused whole rather than restated.
 *
 * **And `nothingToSee`, which the gloss has no equivalent of.** It is the slot that decides
 * whether any of this gets used: a test-only change, a refactor or a rule nobody can open has
 * nothing a person could try, and an agent with no way to say so invents a procedure instead.
 * Filled, it is the answer — and a screen proposes that verdict rather than a walkthrough.
 *
 * Nothing here draws it, and nothing here decides a verdict: the words come back and a person
 * decides. *No rule compiled into the client* holds by there being no rule here at all.
 */

/** One step: what a person does, and what they should see if it worked. */
export interface WalkthroughStep {
  readonly does: string
  /** What that produces. Empty is not a step — a step nobody can check is not one. */
  readonly sees: string
}

export interface Walkthrough {
  /** What has to be true before the first step: a build, a project open, a checkout. */
  readonly before: readonly string[]
  readonly steps: readonly WalkthroughStep[]
  /** Where the change landed, the gloss's own slot (RG288). */
  readonly where: readonly GlossPlace[]
  /**
   * Why there is nothing a person can open, empty where there is something.
   *
   * Filled and the steps are beside the point: the run found a change nobody can try, and said
   * so rather than making one up.
   */
  readonly nothingToSee: string
}

/** A walkthrough with every slot empty, which a refusal and a missing answer both read as. */
export const NO_WALKTHROUGH: Walkthrough = {
  before: [],
  steps: [],
  where: [],
  nothingToSee: '',
}

/**
 * The schema the engine answers against.
 *
 * Written here rather than derived from the type, for `GLOSS_SCHEMA`'s reason: a schema is what
 * crosses to another program, and one generated from a type would change shape whenever a field
 * was renamed on this side — which the other program would go on answering against.
 */
export const WALKTHROUGH_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['before', 'steps', 'nothingToSee'],
  properties: {
    before: {
      type: 'array',
      items: { type: 'string' },
      description:
        'What has to be true before the first step: a build, a project open, something on disk.',
    },
    steps: {
      type: 'array',
      description:
        'What a person does to see this for themselves, in order. Empty where there is nothing to see.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['does', 'sees'],
        properties: {
          does: { type: 'string', description: 'One thing the person does.' },
          sees: { type: 'string', description: 'What they should see if it worked.' },
        },
      },
    },
    where: {
      type: 'array',
      description:
        'Each place the change landed, one per file the commit touched that matters to a reader.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['path', 'said'],
        properties: {
          path: { type: 'string', description: 'Relative to the repository root.' },
          said: { type: 'string', description: 'What the commit changed there.' },
        },
      },
    },
    nothingToSee: {
      type: 'string',
      description:
        'Why a person cannot try this — a refactor, a test, an internal rule. Empty where they can, and then steps say how.',
    },
  },
} as const

/**
 * The frame around the commit, for somebody about to check that the work does what it says.
 *
 * Short, for `promptForGloss`'s reason: the entry and the commit are both payloads the engine
 * answered, and they go in verbatim. What is added is who is asking, which language to write in,
 * and the one instruction that makes the answer honest — read the diff, and where there is
 * nothing to try, say so instead of inventing steps.
 *
 * @param origin the `origin` payload for the entry, verbatim
 * @param said the ledger's own sentence about it: what shipped, as the entry states it
 * @param tag the language every string comes back in, as a BCP-47 tag
 */
export function promptForWalkthrough(origin: OriginPayload, said: string, tag: string): string {
  const sha = origin.shippedIn?.sha ?? ''
  // A history that could not place the ship is not a run with less to read: there is no diff at
  // all, and the honest answer is the one slot that says so rather than steps read off a sentence.
  const evidence =
    sha === ''
      ? [
          'No commit in this history wrote that entry, so there is no diff to read and nothing',
          'here says what changed. Say that in `nothingToSee` and leave `steps` empty.',
        ]
      : [
          `Read that commit before writing anything — \`git show ${sha}\` — and then the files`,
          'around it with `Read`, `Grep` and `Glob`. The diff is the only account of what changed.',
        ]

  return [
    `Somebody is about to check whether roadkeep entry ${origin.id} does what its ledger says.`,
    '',
    'The ledger states the outcome, and the outcome is not the change:',
    '',
    said,
    '',
    'Below is the `origin` payload roadkeep answered for it, verbatim — the commit that',
    'proposed the line and the commit that shipped it, each with its whole message.',
    '',
    JSON.stringify(origin, null, 2),
    '',
    ...evidence,
    '',
    'Write what a person does to see this working, as pairs: one thing they do, and what they',
    'should see if it worked. Put what has to be true first in `before`. Fill `where` with the',
    'files the commit changed that a reader would want to open.',
    '',
    'Where the change is one nobody can open — a refactor, a test, an internal rule — say why',
    'in `nothingToSee` and leave `steps` empty. Do not invent a procedure for it.',
    '',
    `Write every string in ${tag}. Say only what the commit and those files say.`,
  ].join('\n')
}

function sentence(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function sentences(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((one) => typeof one === 'string' && one !== '') : []
}

/**
 * The steps the answer gave, each one a reader could act on and check.
 *
 * A pair missing either half is dropped: a `does` with no `sees` is an instruction nobody can
 * tell the outcome of, which is the thing this shape exists to refuse.
 */
function stepsIn(value: unknown): WalkthroughStep[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((one): WalkthroughStep[] => {
    const record = asRecord(one)
    const does = sentence(record?.['does'])
    const sees = sentence(record?.['sees'])
    return does === '' || sees === '' ? [] : [{ does, sees }]
  })
}

/**
 * One walkthrough, read off whatever the run answered (RG291).
 *
 * Lenient about what is missing, like `readGloss`: a slot nobody filled is empty, and nothing
 * here fails — a walkthrough is an offer, and a screen with none of it is the screen that was
 * there before. Unlike a gloss it is held against no payload, because it is about a commit and
 * not about a line: there are no ids to check an answer's keys against.
 */
export function readWalkthrough(answer: unknown): Walkthrough {
  const said = asRecord(answer)
  if (said === null) return NO_WALKTHROUGH

  return {
    before: sentences(said['before']),
    steps: stepsIn(said['steps']),
    where: placesIn(said['where']),
    nothingToSee: sentence(said['nothingToSee']),
  }
}

/** Whether a walkthrough says anything at all, which is what a screen draws or does not. */
export function hasWalkthrough(walkthrough: Walkthrough): boolean {
  return (
    walkthrough.steps.length > 0 ||
    walkthrough.nothingToSee !== '' ||
    walkthrough.before.length > 0 ||
    walkthrough.where.length > 0
  )
}
