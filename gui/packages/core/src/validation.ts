import type { UnvalidatedEntry, UnvalidatedPayload } from './payloads'

/**
 * What awaits a person, as a screen draws it (RG293).
 *
 * `unvalidated` answers one payload and four different screens, and only two of its fields tell
 * them apart. An empty list is **not one state**: a project that declares no `[validation]` is
 * not asking the question, a project whose history cannot place where looking starts is asking
 * and cannot answer, and a ledger every entry of which carries a verdict has answered it. A tab
 * reading the list alone would draw all three as *nothing to look at*, which is right for one.
 *
 * So the payload becomes a state here, in `core`, where the rest of this app's reading lives —
 * and the screen draws a sentence per state rather than deciding which one it is.
 */

/** The states a validation listing can be in, and what each one has to draw. */
export type Validation =
  /** No `[validation]` declared: the question is not asked in this project. */
  | { readonly kind: 'ungoverned' }
  /** Declared, and the history could not place where looking starts. */
  | { readonly kind: 'unplaced' }
  /** Asked and answered: every entry since looking started carries a verdict. */
  | { readonly kind: 'none'; readonly validated: number }
  /** Entries awaiting somebody, newest first. */
  | {
      readonly kind: 'awaiting'
      readonly rows: readonly UnvalidatedEntry[]
      /** How many of the entries asked about already carry one. */
      readonly validated: number
    }

/**
 * The listing as a state, its rows newest first (RG293).
 *
 * **Newest first, against the block order every other tab uses.** What somebody will actually
 * validate is what they just shipped, while they still remember what it was for, and the ledger's
 * own order buries that under whatever Block A left behind.
 *
 * The order is the engine's file order reversed, and that is all it is: the ledger appends within
 * each block heading, so the entries nearest its end are the ones written last. No date is read
 * and none is drawn — *no dates, estimates, velocity or burndown* — and nothing here works out a
 * ship order the payload does not carry.
 */
export function validationFrom(payload: UnvalidatedPayload): Validation {
  if (!payload.governed) return { kind: 'ungoverned' }
  if (!payload.placed) return { kind: 'unplaced' }
  if (payload.unvalidated.length === 0) return { kind: 'none', validated: payload.validated }
  return {
    kind: 'awaiting',
    rows: payload.unvalidated.toReversed(),
    validated: payload.validated,
  }
}

/** How many await somebody, which is what a count beside a tab draws. Zero in every other state. */
export function awaiting(validation: Validation): number {
  return validation.kind === 'awaiting' ? validation.rows.length : 0
}
