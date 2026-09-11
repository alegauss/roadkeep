import type { BriefPayload, HeldClaim } from './payloads'
import type { VerbInputs } from './verbs'

/**
 * Taking the line, not just reading it.
 *
 * Every tier of a pick is a function of the file, so a second caller reading an unchanged
 * backlog is handed the line the first one took. `brief --claim` answers and moves the
 * marker in one transaction, and it is the call that starts a task anyway — so handing a
 * task to a session takes it in the same act, with no window between the two.
 *
 * **A claim is an expiry and not a lock.** It names nobody, it is stepped over once the
 * declared time has passed, and nothing re-dates a live one: a second `--claim` is refused,
 * which is how the window stays an expiry rather than something a caller can extend. This
 * app does not retry it, and the refusal names no field, so it is shown as the sentence it
 * is.
 *
 * **The claim and the marker stay two facts.** `claimed` says what this call did to the
 * marker; `held` says who is on the line. Neither is a proxy for the other, and a handover
 * reads both rather than inferring one from the other.
 */

/**
 * The read that starts a task.
 *
 * With no id it is the pick as well, which is the whole point: the tier that chose the
 * line and the transaction that took it are one call, so nothing can read a line and lose
 * it before claiming.
 */
export function claimingBrief(id?: string): VerbInputs['brief'] {
  return id === undefined ? { claim: true } : { id, claim: true }
}

export interface Handover {
  readonly id: string
  /** True where this call moved the marker and the line is now this session's. */
  readonly taken: boolean
  /** The marker before and after. Empty where the call only read. */
  readonly from: string
  readonly to: string
  /**
   * Workers on the line, in the engine's words. Non-empty is what has to be named before
   * a second session is offered it — the block's own criterion.
   */
  readonly held: readonly HeldClaim[]
  /** The line's readiness, carried. Never worked out here. */
  readonly readiness: string
}

export function handoverOf(payload: BriefPayload): Handover {
  return {
    id: payload.id,
    taken: payload.claimed?.taken ?? false,
    from: payload.claimed?.from ?? '',
    to: payload.claimed?.to ?? '',
    held: payload.held,
    readiness: payload.readiness,
  }
}

/**
 * Whether this line may be handed to a session.
 *
 * Both facts, and neither standing in for the other: the engine's readiness says the work
 * can start, and `held` says nobody else is on it. A marker is not consulted — RG74's
 * point, and the reason a line somebody started and left is offered again once its claim
 * has expired.
 */
export function mayHandOver(handover: Handover): boolean {
  return handover.readiness === 'ready' && handover.held.length === 0
}

/**
 * Who holds it, named before a second session is offered it.
 *
 * The engine's own words for the holder and the age. A claim names nobody, so "another
 * worker" is what there is to say when it did not — and saying it is still better than
 * offering the line as free.
 */
export function heldBy(handover: Handover): string {
  const holder = handover.held[0]
  if (holder === undefined) return ''
  const who = holder.by === '' ? 'another worker' : holder.by
  const since = holder.since === '' ? '' : ` since ${holder.since}`
  return `${handover.id} is held by ${who}${since}`
}

/*
 * `saidOfHandover` stood here, composing what the handover did as an English sentence. No
 * screen drew it — the task screen says it through the catalogue — so RG172 deleted it
 * rather than keep one language's copy of a sentence every language already has.
 */
