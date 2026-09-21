import type { BriefPayload } from './payloads'
import { asRecord } from './reading'

/**
 * A task said in plain words (RG283): what is asked of Claude Code, and what shape its answer
 * comes back in.
 *
 * A line is written for whoever builds it — a symptom, one why, and a design that names modules
 * and non-goals — and a person new to the project reads all three and still asks what the task
 * *is*. This is the read that answers that, and nothing here draws it: a screen is RG285's.
 *
 * **The prompt is `promptFor`'s shape.** The brief payload goes in verbatim, as the hand-over
 * sends it, and what is added is what a session does not need: who the reader is, which language
 * to write in, and that nothing in the payload is to be changed. This app paraphrases no line.
 *
 * **The answer is a shape, not a page.** `GLOSS_SCHEMA` is what the engine answers against, and
 * `readGloss` reads it the way every payload reader here reads one: a slot nobody filled is
 * empty, and an entry keyed by an id or a lead the brief does not carry is dropped. So every
 * fact on the screen is one the brief already held, and the gloss only says it in other words.
 *
 * *No Markdown parsed in this app* reaches this: the strings are drawn as they are, and the keys
 * are matched against the brief rather than found in prose.
 */

/** One of the project's own words, said plainly. */
export interface GlossTerm {
  readonly term: string
  readonly said: string
}

export interface Gloss {
  /** One line: what this task is, for somebody who has never read the project. */
  readonly headline: string
  /** What is true now, which is the symptom without its terms. */
  readonly today: string
  /** What is true once it is done. */
  readonly after: string
  /** What the work involves, in the order it would be done. */
  readonly steps: readonly string[]
  /** The words the line uses that a newcomer would have to look up. */
  readonly terms: readonly GlossTerm[]
  /** What could go wrong, or what is easy to get wrong. */
  readonly risks: readonly string[]
  /** How somebody would know it is finished. */
  readonly done: readonly string[]
  /** What each dep is, by the id the brief carries. */
  readonly deps: Readonly<Record<string, string>>
  /** What shipping this frees, by the id the brief carries. */
  readonly unblocks: Readonly<Record<string, string>>
  /** What each non-goal binding this line means, by its lead. */
  readonly binds: Readonly<Record<string, string>>
}

/** A gloss with every slot empty, which is what a refusal and a missing answer both read as. */
export const NO_GLOSS: Gloss = {
  headline: '',
  today: '',
  after: '',
  steps: [],
  terms: [],
  risks: [],
  done: [],
  deps: {},
  unblocks: {},
  binds: {},
}

/**
 * The schema the engine answers against.
 *
 * Written here rather than assembled from the type: a schema is what crosses to another program,
 * and one derived from a type would change shape whenever a field was renamed here — which the
 * other program would answer against without knowing.
 */
export const GLOSS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['headline', 'today', 'after'],
  properties: {
    headline: { type: 'string', description: 'One line: what this task is, in plain words.' },
    today: { type: 'string', description: 'What is true now, said without the project’s terms.' },
    after: { type: 'string', description: 'What is true once this is done.' },
    steps: {
      type: 'array',
      items: { type: 'string' },
      description: 'What the work involves, in the order it would be done.',
    },
    terms: {
      type: 'array',
      description: 'Each word the line uses that a newcomer would look up.',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['term', 'said'],
        properties: {
          term: { type: 'string' },
          said: { type: 'string', description: 'What it means here, in a sentence.' },
        },
      },
    },
    risks: { type: 'array', items: { type: 'string' } },
    done: {
      type: 'array',
      items: { type: 'string' },
      description: 'How somebody would know it is finished.',
    },
    deps: {
      type: 'object',
      additionalProperties: { type: 'string' },
      description: 'What each dep is, keyed by the id the brief carries.',
    },
    unblocks: {
      type: 'object',
      additionalProperties: { type: 'string' },
      description: 'What shipping this frees, keyed by the id the brief carries.',
    },
    binds: {
      type: 'object',
      additionalProperties: { type: 'string' },
      description:
        'What each non-goal means here, keyed by its lead, exactly as the brief spells it.',
    },
  },
} as const

/**
 * The frame around the payload, for a reader who knows neither the project nor roadkeep.
 *
 * Short, for `promptFor`'s reason: everything about the task is in the payload, and a paragraph
 * of this app's own prose about it would be a second account of a line the engine already
 * stated. What is added is the audience, the language and the one rule — say what is there.
 *
 * @param tag the language every string comes back in, as a BCP-47 tag
 */
export function promptForGloss(payload: BriefPayload, tag: string): string {
  return [
    `Explain roadkeep task ${payload.id} to somebody who has never worked on this project.`,
    '',
    'Below is the `brief` payload roadkeep answered for it, verbatim: the line, its design',
    'section, its deps and what resolves them, what shipping it unblocks, and the criteria',
    'and non-goals that bind it. Nothing in it was rewritten.',
    '',
    JSON.stringify(payload, null, 2),
    '',
    'The reader knows neither this project nor roadkeep. Say what the task is, what is true',
    'now and what is true once it is done, what the work involves, which of the words above',
    'they would have to look up, and how anybody would know it is finished. Explain the deps',
    'and the non-goals under the exact ids and leads the payload spells them with.',
    '',
    `Write every string in ${tag}. Say only what the payload says: no fact of your own, no`,
    'advice on how to build it, and nothing about files you have not been shown here.',
  ].join('\n')
}

function sentence(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function sentences(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((one) => typeof one === 'string' && one !== '') : []
}

/** The words the answer explained, each one it gave a meaning for. */
function termsIn(value: unknown): GlossTerm[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((one): GlossTerm[] => {
    const record = asRecord(one)
    const term = sentence(record?.['term'])
    const said = sentence(record?.['said'])
    return term === '' || said === '' ? [] : [{ term, said }]
  })
}

/**
 * The entries whose key the brief carries, in the brief's own order.
 *
 * The dropping is the point: an id or a lead the payload never held would be a fact the agent
 * supplied, and this screen says only what the engine said.
 */
function keyed(value: unknown, keys: readonly string[]): Record<string, string> {
  const answered = asRecord(value)
  if (answered === null) return {}
  const kept: Record<string, string> = {}
  for (const key of keys) {
    const said = sentence(answered[key])
    if (said !== '') kept[key] = said
  }
  return kept
}

/** Every dep id the brief carries, as the ids an answer may key by. */
function depIds(payload: BriefPayload): string[] {
  const resolved = payload.depsResolved.map((one) => one.dep)
  return [...new Set([...resolved, ...payload.deps])]
}

function unblockIds(payload: BriefPayload): string[] {
  const unblocks = payload.unblocks
  if (unblocks === null) return []
  return [...new Set([...unblocks.direct, ...unblocks.transitive])]
}

/**
 * One gloss, read against the brief it was asked about (RG283).
 *
 * Lenient about what is missing and strict about what is invented: a slot the answer left out is
 * empty, and an entry under an id or a lead the brief does not carry is dropped rather than
 * drawn. Nothing here fails — a gloss is an extra, and a screen with none of it is the screen
 * that was there before.
 */
export function readGloss(answer: unknown, payload: BriefPayload): Gloss {
  const said = asRecord(answer)
  if (said === null) return NO_GLOSS

  return {
    headline: sentence(said['headline']),
    today: sentence(said['today']),
    after: sentence(said['after']),
    steps: sentences(said['steps']),
    terms: termsIn(said['terms']),
    risks: sentences(said['risks']),
    done: sentences(said['done']),
    deps: keyed(said['deps'], depIds(payload)),
    unblocks: keyed(said['unblocks'], unblockIds(payload)),
    binds: keyed(said['binds'], payload.nonGoals),
  }
}

/** Whether a gloss says anything at all, which is what a screen draws or does not. */
export function hasGloss(gloss: Gloss): boolean {
  return (
    gloss.headline !== '' ||
    gloss.today !== '' ||
    gloss.after !== '' ||
    gloss.steps.length > 0 ||
    gloss.terms.length > 0 ||
    gloss.risks.length > 0 ||
    gloss.done.length > 0
  )
}
