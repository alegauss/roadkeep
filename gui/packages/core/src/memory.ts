import type {
  DeliveredEntry,
  DeliveredPayload,
  ReversalEntry,
  ReversalsPayload,
  Standing,
} from './payloads'

/**
 * The memory a proposal is tested against: what a block shipped, and what was undone.
 *
 * Two reads, reached from a block and from a task because that is where the question
 * comes up, and never a screen of their own.
 *
 * **The order is the answer and there is no score.** `delivered --near` ranks a block's
 * entries against a sentence about to be proposed, and roadkeep measured that an absolute
 * number separates nothing and refused to publish one — so a percentage or a *likely
 * duplicate* badge drawn here would be inventing the threshold that cannot exist. Rank is
 * a position among the five returned, and this module spells it that way.
 *
 * **A revert is filed as a delivery.** So `delivered` on its own answers *yes, shipped*
 * about an entry that says the work did not hold, and `reversals` is what reads the
 * forward pointer back. Neither read refuses anything and neither may be made to:
 * re-proposing reverted work is sometimes right, and which time takes meaning no tool
 * here has.
 */

export interface Delivery extends DeliveredEntry {
  /** Whether the ledger itself superseded this entry. `undoneBy` names what did. */
  readonly undone: boolean
}

export interface Ledger {
  readonly file: string
  readonly block: string
  readonly standing: Standing | null
  readonly recorded: number
  /** The sentence the ranking answered, or the empty string for the whole block. */
  readonly near: string
  /** True where these are the nearest few and not the block — a sample, and it says so. */
  readonly ranked: boolean
  readonly delivered: readonly Delivery[]
}

export function ledgerFrom(payload: DeliveredPayload): Ledger {
  const near = payload.near ?? ''
  return {
    file: payload.file,
    block: payload.block,
    standing: payload.standing,
    recorded: payload.recorded,
    near,
    ranked: near !== '',
    delivered: payload.delivered.map((entry) => ({
      ...entry,
      undone: entry.undoneBy !== null && entry.undoneBy !== '',
    })),
  }
}

export interface Reversed {
  readonly root: string
  /** The id asked about, or the empty string where the question was the whole ledger. */
  readonly asked: string
  /** True when this answer was narrowed, so a listing of one is not read as the ledger. */
  readonly narrowed: boolean
  readonly reversals: readonly ReversalEntry[]
}

export function reversedFrom(payload: ReversalsPayload): Reversed {
  const asked = payload.asked ?? ''
  return {
    root: payload.root,
    asked,
    narrowed: asked !== '',
    reversals: payload.reversed,
  }
}

/**
 * What undid one id, or null.
 *
 * A lookup and not a verdict. It answers that the ledger records a reversal, which is a
 * fact; whether the revert was about a broken implementation or a wrong idea is the one
 * thing nobody here can tell.
 */
export function undoneBy(reversed: Reversed, id: string): ReversalEntry | null {
  return reversed.reversals.find((one) => one.undone === id) ?? null
}

/**
 * How this listing came about, for a screen that must not present five as all of them.
 *
 * Drawing the nearest five as the block's deliveries would answer a duplicate question
 * with a set that was chosen by the question itself.
 */
export function howListed(ledger: Ledger): string {
  if (!ledger.ranked) {
    return `${String(ledger.recorded)} delivered under ${ledger.block || 'this block'}`
  }
  return (
    `${String(ledger.delivered.length)} nearest of ${String(ledger.recorded)} ` +
    `delivered under ${ledger.block || 'this block'} — an order, not a verdict`
  )
}
