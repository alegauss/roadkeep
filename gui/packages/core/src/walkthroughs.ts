import { aNumber, aString, listOf, orMissing, record, type Reader } from './reading'
import { NO_WALKTHROUGH, type Walkthrough, type WalkthroughStep } from './walkthrough'
import type { GlossPlace } from './gloss'

/**
 * The walkthroughs a machine keeps between openings (RG292).
 *
 * RG287 keeps a gloss because reopening a task paid the wait and the tokens again. A walkthrough
 * has the sharper version of the same problem: **the sheet is closed by the act of following
 * it.** The person leaves the window, opens a terminal, runs a build, comes back. Throwing the
 * answer away at that moment throws it away every single time, not occasionally.
 *
 * **Kept by what it answered**, as a gloss is: the project, the entry and the language. The same
 * steps in the wrong language are not the steps somebody asked for.
 *
 * **Stale is a comparison and never a clock — and here it is one hash.** A gloss stands while its
 * line still reads the same, which is six fields. A walkthrough stands while the **shipping
 * commit is the same**, and that is the whole test: the entry's sentence can be corrected without
 * the work changing, and the work cannot change without a new commit. Cheaper than the gloss
 * comparison and stricter. A stale one is still drawn, under a notice, because it was true of
 * what shipped — and Regenerate asks anew.
 *
 * **Bounded, oldest first**, so a machine reading a hundred projects keeps a file somebody could
 * open. Where it is kept is the shell's, as it is for a gloss: `core` says what one is and when
 * it stands.
 */

/** What this build writes. A file claiming a higher number is not read. */
export const WALKTHROUGHS_VERSION = 1

/** How many walkthroughs one machine keeps. */
export const WALKTHROUGHS_KEPT = 50

export interface KeptWalkthrough {
  readonly root: string
  /** The ledger entry it is about. */
  readonly id: string
  /** The language every string in it is written in, as a BCP-47 tag. */
  readonly tag: string
  readonly walkthrough: Walkthrough
  /** Which Claude Code and which model wrote it, as the run named them. */
  readonly version: string
  readonly model: string
  /** When it was answered, as an ISO time: what the oldest-first bound reads. */
  readonly answered: string
  /**
   * The shipping commit it was written from, as `origin` resolved it.
   *
   * The whole of what staleness compares, and empty where the history could not say — which
   * never stands, because there is nothing to hold the answer against.
   */
  readonly commit: string
}

export interface KeptWalkthroughs {
  readonly version: number
  readonly walkthroughs: readonly KeptWalkthrough[]
}

export const NOTHING_WALKED: KeptWalkthroughs = {
  version: WALKTHROUGHS_VERSION,
  walkthroughs: [],
}

/**
 * Whether a kept walkthrough still answers for the entry as it shipped (RG292).
 *
 * One comparison, both sides of it a hash the engine resolved. An empty hash on either side
 * never stands: a history that cannot place the commit cannot say the answer is still about it,
 * and *probably still fine* is not something this decides on somebody's behalf.
 */
export function walkthroughStands(kept: KeptWalkthrough, commit: string): boolean {
  return kept.commit !== '' && kept.commit === commit
}

/** The one kept for this entry in this language, or null where none is. */
export function walkthroughFor(
  kept: KeptWalkthroughs,
  root: string,
  id: string,
  tag: string,
): KeptWalkthrough | null {
  return (
    kept.walkthroughs.find((one) => one.root === root && one.id === id && one.tag === tag) ?? null
  )
}

/**
 * The walkthroughs with one written in, the one it replaces dropped and the oldest gone past the
 * bound — which is what makes this a cache rather than a record that grows.
 */
export function withWalkthrough(
  kept: KeptWalkthroughs,
  walkthrough: KeptWalkthrough,
): KeptWalkthroughs {
  const rest = kept.walkthroughs.filter(
    (one) =>
      !(one.root === walkthrough.root && one.id === walkthrough.id && one.tag === walkthrough.tag),
  )
  const all = [walkthrough, ...rest].toSorted((one, other) =>
    one.answered === other.answered ? 0 : one.answered < other.answered ? 1 : -1,
  )
  return { version: WALKTHROUGHS_VERSION, walkthroughs: all.slice(0, WALKTHROUGHS_KEPT) }
}

const readStep: Reader<WalkthroughStep> = record<WalkthroughStep>({
  does: orMissing(aString, ''),
  sees: orMissing(aString, ''),
})

const readPlace: Reader<GlossPlace> = record<GlossPlace>({
  path: orMissing(aString, ''),
  said: orMissing(aString, ''),
})

const readSaid: Reader<Walkthrough> = record<Walkthrough>({
  before: orMissing(listOf(aString), []),
  steps: orMissing(listOf(readStep), []),
  where: orMissing(listOf(readPlace), []),
  nothingToSee: orMissing(aString, ''),
})

const readKept: Reader<KeptWalkthrough> = record<KeptWalkthrough>({
  root: aString,
  id: aString,
  tag: orMissing(aString, ''),
  walkthrough: orMissing(readSaid, NO_WALKTHROUGH),
  version: orMissing(aString, ''),
  model: orMissing(aString, ''),
  answered: orMissing(aString, ''),
  commit: orMissing(aString, ''),
})

const readKeptWalkthroughs: Reader<KeptWalkthroughs> = record<KeptWalkthroughs>({
  version: orMissing(aNumber, WALKTHROUGHS_VERSION),
  walkthroughs: orMissing(listOf(readKept), []),
})

/**
 * What a file holds, or null where it is not a shape this build knows.
 *
 * Null and not a refusal, as a gloss file is: a cache that cannot be read is a cache that was not
 * there, and the window asks again. A file from a later build is null too, its fields possibly
 * meaning something else.
 */
export function walkthroughsFrom(text: string): KeptWalkthroughs | null {
  let source: unknown
  try {
    source = JSON.parse(text)
  } catch {
    return null
  }
  const read = readKeptWalkthroughs(source, '')
  if (!read.ok) return null
  return read.value.version > WALKTHROUGHS_VERSION ? null : read.value
}
