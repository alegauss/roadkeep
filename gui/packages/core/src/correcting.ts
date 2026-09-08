import type { CommandsPayload } from './capabilities'
import type { AmendPayload, RenumberPayload, RestatePayload } from './payloads'

/**
 * The corrections that keep the id.
 *
 * Three verbs exist because retiring and re-adding spends an id and deletes a design that
 * was right. `amend` corrects a why, the deps or the pointer. `restate` corrects a symptom
 * whose claim turned out false, keeping the id, the deps, the marker and the design.
 * `renumber` moves a line to a free id, taking its section and its dependents.
 *
 * **The reason each exists is read, not written.** `commands` publishes a sentence per
 * verb, so the guidance that stops somebody reaching for the expensive one comes off the
 * same read that says whether this build has them at all. Nothing here explains a verb in
 * its own words.
 *
 * **`was` is the key to be careful about.** `amend` answers with a map of the fields it
 * changed and what each held; `restate` answers with the one symptom as a string. One key,
 * two types, one verb apart — so they are two shapes here and never one reader.
 */

/** The three, in the order a screen should offer them: least costly first. */
export const CORRECTIONS = ['amend', 'restate', 'renumber'] as const

export type Correction = (typeof CORRECTIONS)[number]

export interface Offered {
  readonly verb: Correction
  /** Whether this build runs it. A door for a verb it lacks is a refusal in waiting. */
  readonly callable: boolean
  /** The one-line reason it exists, in the engine's words. Empty where it said none. */
  readonly help: string
  /** The same at length, where the engine published it. */
  readonly description: string
}

/**
 * What this build offers of the three, with the engine's own account of each.
 *
 * Driven off `commands` rather than a list here: a build that does not publish `restate`
 * should not be offered it, and the sentence distinguishing it from `amend` is the
 * engine's to write.
 */
export function correctionsOffered(payload: CommandsPayload): Offered[] {
  const published = new Map(payload.commands.map((command) => [command.command, command]))
  return CORRECTIONS.map((verb) => {
    const command = published.get(verb)
    return {
      verb,
      callable: command !== undefined && command.runs,
      help: command?.help ?? '',
      description: command?.description ?? '',
    }
  })
}

/** What one correction did, over the three shapes the three verbs answer in. */
export interface Corrected {
  readonly verb: Correction
  readonly id: string
  /** The id afterwards, which only `renumber` changes. */
  readonly nowId: string
  /** Which fields moved, in the engine's words. */
  readonly changed: readonly string[]
  /** The line as the file now spells it. */
  readonly rendered: string
  /** Ids whose deps were rewritten or re-derived because of this. */
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
  /**
   * What the correction did not do and left for a person. Empty for most — `restate` is
   * the one that has any, and they are the engine's commands and not a prompt composed
   * here.
   */
  readonly next: readonly string[]
}

export function amended(payload: AmendPayload): Corrected {
  return {
    verb: 'amend',
    id: payload.id,
    nowId: payload.id,
    changed: payload.changed,
    rendered: payload.rendered,
    refreshed: payload.refreshed,
    wrote: payload.wrote,
    next: [],
  }
}

export function restated(payload: RestatePayload): Corrected {
  return {
    verb: 'restate',
    id: payload.id,
    nowId: payload.id,
    // The one field it touches, named the way `amend` names its own.
    changed: payload.changed ? ['symptom'] : [],
    rendered: payload.rendered,
    refreshed: payload.refreshed,
    wrote: payload.wrote,
    // Carried, never turned into a form: deciding a sentence went stale is the reader's.
    next: payload.premise?.next ?? [],
  }
}

export function renumbered(payload: RenumberPayload): Corrected {
  return {
    verb: 'renumber',
    id: payload.id,
    nowId: payload.to,
    changed: ['id'],
    rendered: payload.rendered,
    // Every line whose deps now name the new id, plus whatever was re-derived.
    refreshed: [...payload.moved, ...payload.refreshed],
    wrote: payload.wrote,
    next: [],
  }
}

/**
 * What `amend` replaced, field by field.
 *
 * Its own reader because the shape is its own: a map of field to what it held, where
 * `restate` sends one string. A screen showing "was" for both would be reading one of them
 * wrong.
 */
export function replacedBy(payload: AmendPayload): [string, string][] {
  return payload.changed.map((field) => [field, payload.was[field] ?? ''])
}

/**
 * Whether a restate was a slip of the pen rather than a false premise.
 *
 * The engine's own word for it. It matters because a typo leaves the why and the design
 * standing, and a false premise leaves both in question — which is why the verb reports
 * which it was rather than treating them alike.
 */
export function wasTypo(payload: RestatePayload): boolean {
  return payload.typo
}
