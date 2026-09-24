import { asRecord } from './reading'
import { readDoor, type Door } from './refusals'

/**
 * The doors an answer carried, and the words a person puts in one (RG165).
 *
 * A door is **the engine's own argv**, handed back by a refusal, a gate finding or `explain`
 * — not something this app's verb tables compose. That is why the carrier's guard refuses to
 * run one, and why running one goes the other way round: the side that received the door keeps
 * it, and a caller names which door rather than what to run. Everything here is the reading
 * that makes that possible, and none of it decides who may run anything.
 *
 * **A blank is the engine's, and so is everything around it.** An incomplete door has
 * placeholders where a person's prose goes — `<lead>`, `…` — and filling one replaces exactly
 * those elements, in order. Nothing else in the argv is touched, so a caller cannot add a
 * flag, a path or a second verb by supplying more words: extra words are refused rather than
 * appended, which is the difference between filling a form and writing a command line.
 */

/**
 * What the engine writes where a caller has to put something.
 *
 * Two spellings, both the engine's: `<name>` in the doors a refusal publishes, and `…` in
 * the ones a gate finding does. A word that is neither is an argument the engine chose.
 */
export function isBlank(word: string): boolean {
  return word === '…' || (word.startsWith('<') && word.endsWith('>') && word.length > 2)
}

/**
 * The engine's third spelling: a value it reads on standard input rather than off the argv
 * (RG261).
 *
 * `section amend T50 --body - --role improvements` is one — the prose is the thing a person
 * writes, and a body runs to paragraphs, which is what stdin is for. A blank all the same, and
 * filled in the same order: what differs is only where the word ends up.
 */
export function isBody(word: string): boolean {
  return word === '-'
}

/** Where the blanks are, in the order a caller fills them — a `-` among them (RG261). */
export function blanksIn(argv: readonly string[]): number[] {
  return argv.flatMap((word, at) => (isBlank(word) || isBody(word) ? [at] : []))
}

/** A door's argv with its blanks filled, and what it was given to say on standard input. */
export interface Filled {
  readonly argv: readonly string[]
  /** Empty where the door asked for nothing, which is still written and still ended. */
  readonly stdin: string
}

/**
 * A door's argv with the person's words in its blanks, or null where they do not fit.
 *
 * Null rather than a best effort: too few words leaves a placeholder on a command line that
 * would then run with `<lead>` as a lead, and too many is a caller trying to say something
 * the door did not ask for. Both are refusals, and neither is a thing to guess about.
 */
export function filledArgv(argv: readonly string[], words: readonly string[]): Filled | null {
  const blanks = blanksIn(argv)
  if (blanks.length !== words.length) return null
  // A word that is empty would leave the engine an argument it never offered to take.
  if (words.some((word) => word === '')) return null

  const filled = [...argv]
  let stdin = ''
  blanks.forEach((at, which) => {
    const word = words[which] ?? ''
    // The `-` stays exactly where the engine wrote it: this app fills a door's blanks and
    // never rewrites its command line, and `-` is the argument that says where to read.
    if (isBody(argv[at] ?? '')) stdin = word
    else filled[at] = word
  })
  return { argv: filled, stdin }
}

/**
 * Every door in one answer, wherever the engine put it.
 *
 * The shape appears at the top of an `explain`, under `remedy` on each `lint` finding, and on
 * a refusal — so this walks the document for `doors` lists rather than naming the three
 * places, which is the same reason `readDoor` is one reader: a door offered somewhere this
 * did not look is a button a screen would not draw.
 *
 * The order is the document's, because that is the order a reader sees them in.
 */
export function doorsIn(answer: unknown): Door[] {
  const found: Door[] = []
  const seen = new Set<unknown>()

  const walk = (value: unknown): void => {
    if (Array.isArray(value)) {
      for (const one of value) walk(one)
      return
    }
    const object = asRecord(value)
    if (object === null || seen.has(object)) return
    seen.add(object)

    for (const [key, under] of Object.entries(object)) {
      if (key === 'doors' && Array.isArray(under)) {
        for (const one of under) {
          const door = readDoor(one, 'doors')
          if (door.ok) found.push(door.value)
        }
        continue
      }
      walk(under)
    }
  }

  walk(answer)
  return found
}
