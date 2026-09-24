import type { SectionWritten } from './payloads'

/**
 * Writing the design where the pointer points.
 *
 * Every line carries a pointer that resolves to nothing until a section exists, and `add`
 * says so in its own answer. `add --section` files both in one transaction and is the
 * ordinary path; `section add` is the follow-up for a line that went in without one, and
 * the only door to the decisions role.
 *
 * **Amending is the other half.** A stored section is wrapped at the column the project
 * declared, so a caller holding the prose it meant to change would have to match bytes it
 * never chose. `--replace` is the verb's answer: a fragment, refused unless it occurs
 * exactly once, so the edit's reach is visible in the call rather than discovered in the
 * diff. The pair is one field in the input table — a `--replace` with nothing to put in
 * its place is a malformed command rather than a refused one, and the type makes that
 * unspellable instead of checking for it.
 *
 * **The answer is the file's account and not the draft.** Both verbs come back with the
 * section as it now stands, and the count that matters is the one the gate will read.
 */

/** Where the prose landed, and what a write changed about it. */
export interface Written {
  readonly anchor: string
  readonly title: string
  readonly file: string
  /** The lines it now occupies, as the file has them. */
  readonly first: number
  readonly last: number
  /** The subtree's count and this heading's own, both the file's. */
  readonly words: number
  readonly ownWords: number
  /** What an amend touched. Empty where the section was created rather than corrected. */
  readonly changed: readonly string[]
  readonly wrote: readonly string[]
}

export function writtenFrom(payload: SectionWritten): Written {
  return {
    anchor: payload.anchor,
    title: payload.title,
    file: payload.file,
    first: payload.first,
    last: payload.last,
    words: payload.words,
    ownWords: payload.ownWords,
    changed: payload.changed,
    wrote: payload.wrote,
  }
}

/** Whether this write created the section rather than correcting one. */
export function wasCreated(written: Written): boolean {
  return written.changed.length === 0
}

/**
 * Where the prose now lives, as one string somebody can go and open.
 *
 * The same spelling `whereDesignLives` uses for a read, and for the same reason: the path
 * is the engine's, because which file holds a rationale is a rule roadkeep owns.
 */
export function whereWritten(written: Written): string {
  if (written.file === '') return ''
  if (written.first === written.last) return `${written.file}:${String(written.first)}`
  return `${written.file}:${String(written.first)}-${String(written.last)}`
}

/**
 * What the write did, for a screen to show back.
 *
 * The word count comes last and always, because it is the number somebody adding to a
 * section needs before they add to it again.
 */
export function saidOfWrite(written: Written): string {
  const where = whereWritten(written)
  const what = wasCreated(written) ? 'written' : `amended (${written.changed.join(', ')})`
  return `§${written.anchor} ${what}  ${where}  ${String(written.words)} words`
}
