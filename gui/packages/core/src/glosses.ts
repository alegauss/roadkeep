import type { Gloss } from './gloss'
import type { BriefPayload } from './payloads'
import { aNumber, aString, dictionaryOf, listOf, orMissing, record, type Reader } from './reading'

/**
 * The glosses a machine keeps between openings (RG287).
 *
 * A gloss costs a wait and somebody's tokens, and a dialog closed threw it away — so reopening
 * a task asked Claude Code the same question again. Kept, the second opening is instant and
 * silent, and asking again is a button rather than the only way in.
 *
 * **Kept by what it answered.** The key is the project, the line and the language: a window
 * switched to another language has no gloss in it — the same answer in the wrong language is
 * not the answer — and switching back finds the first one still there.
 *
 * **Stale is a comparison and never a clock.** A kept gloss stands while the line it answered
 * still reads the way it did: the same symptom and why, the same design, the same deps and the
 * same lists that bind it. `glossStands` is that comparison, as `readingStands` (RG251) is the
 * one for a remembered reading. A stale gloss is still shown — it was true of the line as it
 * was — under a notice saying the task has moved since.
 *
 * **Bounded, oldest first.** This is a cache and not a record: past `GLOSSES_KEPT` the least
 * recently answered goes, so a machine that reads a hundred projects keeps a file of a size
 * somebody could open.
 *
 * Where it is kept is the shell's: `core` says what one is and when it stands.
 */

/** What this build writes. A file claiming a higher number is not read. */
export const GLOSSES_VERSION = 1

/** How many glosses one machine keeps. */
export const GLOSSES_KEPT = 50

/**
 * The line as it read when the gloss was written, which is what staleness compares.
 *
 * The fields a reader would notice changing: what the line claims, why, its design, what it
 * waits on and what binds it. Not the marker, the readiness or the claims — a line taken by
 * somebody, or one whose dep shipped, is the same task explained the same way.
 */
export interface GlossedLine {
  readonly symptom: string
  readonly why: string
  readonly design: string
  readonly deps: readonly string[]
  readonly binds: readonly string[]
  readonly doneWhen: readonly string[]
}

export interface KeptGloss {
  readonly root: string
  readonly id: string
  /** The language every string in it is written in, as a BCP-47 tag. */
  readonly tag: string
  readonly gloss: Gloss
  /** Which Claude Code and which model wrote it, as the run named them. */
  readonly version: string
  readonly model: string
  /** When it was answered, as an ISO time: what the oldest-first bound reads. */
  readonly answered: string
  readonly line: GlossedLine
}

export interface KeptGlosses {
  readonly version: number
  readonly glosses: readonly KeptGloss[]
}

export const NOTHING_GLOSSED: KeptGlosses = { version: GLOSSES_VERSION, glosses: [] }

/** The line a gloss answered, off the brief it was written from. */
export function glossedLine(payload: BriefPayload): GlossedLine {
  return {
    symptom: payload.symptom,
    why: payload.why,
    design: payload.section?.body ?? '',
    deps: [...payload.deps],
    binds: [...payload.nonGoals],
    doneWhen: [...payload.doneWhen, ...payload.doneWhenOwn],
  }
}

function same(one: readonly string[], other: readonly string[]): boolean {
  return one.length === other.length && one.every((value, at) => other[at] === value)
}

/**
 * Whether a kept gloss still answers for the line as it is now (RG287).
 *
 * False where anything a reader would notice has moved: the claim, the reason, the design, what
 * it waits on, what binds it, or what finishing it means. The gloss is still worth showing —
 * it explained the line as it stood — and a screen that says so lets somebody decide whether to
 * ask again.
 */
export function glossStands(kept: KeptGloss, payload: BriefPayload): boolean {
  const now = glossedLine(payload)
  return (
    kept.line.symptom === now.symptom &&
    kept.line.why === now.why &&
    kept.line.design === now.design &&
    same(kept.line.deps, now.deps) &&
    same(kept.line.binds, now.binds) &&
    same(kept.line.doneWhen, now.doneWhen)
  )
}

/** The one kept for this line in this language, or null where none is. */
export function glossFor(
  kept: KeptGlosses,
  root: string,
  id: string,
  tag: string,
): KeptGloss | null {
  return kept.glosses.find((one) => one.root === root && one.id === id && one.tag === tag) ?? null
}

/**
 * The glosses with one written in, the one it replaces dropped and the oldest gone past the
 * bound — which is what makes this a cache rather than a record that grows.
 */
export function withGloss(kept: KeptGlosses, gloss: KeptGloss): KeptGlosses {
  const rest = kept.glosses.filter(
    (one) => !(one.root === gloss.root && one.id === gloss.id && one.tag === gloss.tag),
  )
  const all = [gloss, ...rest].toSorted((one, other) =>
    one.answered === other.answered ? 0 : one.answered < other.answered ? 1 : -1,
  )
  return { version: GLOSSES_VERSION, glosses: all.slice(0, GLOSSES_KEPT) }
}

const readGlossTerm = record<{ term: string; said: string }>({
  term: orMissing(aString, ''),
  said: orMissing(aString, ''),
})

const readPlace = record<{ path: string; said: string }>({
  path: orMissing(aString, ''),
  said: orMissing(aString, ''),
})

const readSaid: Reader<Gloss> = record<Gloss>({
  headline: orMissing(aString, ''),
  today: orMissing(aString, ''),
  after: orMissing(aString, ''),
  steps: orMissing(listOf(aString), []),
  // Missing in every gloss kept before RG288, which reads as a gloss that names no place: the
  // answer is still the line explained, and asking again is what fills the lanes in.
  where: orMissing(listOf(readPlace), []),
  terms: orMissing(listOf(readGlossTerm), []),
  risks: orMissing(listOf(aString), []),
  done: orMissing(listOf(aString), []),
  // A table of sentences by key, which is what the three keyed slots of a gloss are.
  deps: orMissing(dictionaryOf(aString), {}),
  unblocks: orMissing(dictionaryOf(aString), {}),
  binds: orMissing(dictionaryOf(aString), {}),
})

const readLine: Reader<GlossedLine> = record<GlossedLine>({
  symptom: orMissing(aString, ''),
  why: orMissing(aString, ''),
  design: orMissing(aString, ''),
  deps: orMissing(listOf(aString), []),
  binds: orMissing(listOf(aString), []),
  doneWhen: orMissing(listOf(aString), []),
})

const readKept: Reader<KeptGloss> = record<KeptGloss>({
  root: aString,
  id: aString,
  tag: orMissing(aString, ''),
  gloss: readSaid,
  version: orMissing(aString, ''),
  model: orMissing(aString, ''),
  answered: orMissing(aString, ''),
  line: readLine,
})

const readKeptGlosses: Reader<KeptGlosses> = record<KeptGlosses>({
  version: orMissing(aNumber, GLOSSES_VERSION),
  glosses: orMissing(listOf(readKept), []),
})

/**
 * What a file holds, or null where it is not a shape this build knows.
 *
 * Null and not a refusal: a cache that cannot be read is a cache that was not there, and the
 * window asks again. A file from a later build is null too, its fields possibly meaning
 * something else.
 */
export function glossesFrom(text: string): KeptGlosses | null {
  let source: unknown
  try {
    source = JSON.parse(text)
  } catch {
    return null
  }
  const read = readKeptGlosses(source, '')
  if (!read.ok) return null
  return read.value.version > GLOSSES_VERSION ? null : read.value
}
