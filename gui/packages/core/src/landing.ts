import type { BriefPayload } from './payloads'
import type { Refusal } from './refusals'

/**
 * What the session did, beside what it said.
 *
 * An agent writes through the same verbs a person does, so the evidence a session worked
 * is the governed files changing. RG45 watches them; this says what changed about the line.
 *
 * **One re-read answers all of it.** The marker moving, the section appearing or going and
 * the line leaving for the ledger are three keys of the same `brief` — `status`, `section`
 * and `shipped` — so the evidence is that payload read again and the two compared. Nothing
 * here infers a ship from a marker or a design from a word count.
 *
 * **Beside the stream, not inside it.** What the agent said and what the repository now
 * holds are two things and only the second is true: a session can report shipping a line it
 * did not ship. So the acts and the landing are kept apart, and where they disagree the
 * files are what a screen shows.
 *
 * **A read that refuses is an answer too.** A line that was deferred or retired stops
 * briefing at all, and the refusal names where it went — so leaving is read from that
 * rather than from a payload that will never arrive.
 */

/** What the line is, at one moment. Either the engine briefed it or it refused to. */
export type Reading =
  | { readonly kind: 'read'; readonly payload: BriefPayload }
  /** The brief refused — the line is not where it was, and the sentence says where. */
  | { readonly kind: 'gone'; readonly refusal: Refusal }

export type Change =
  | { readonly kind: 'marker'; readonly from: string; readonly to: string }
  /** The design was written, or deleted by the ship that closed the line. */
  | { readonly kind: 'design'; readonly from: 'none' | 'written'; readonly to: 'none' | 'written' }
  | { readonly kind: 'shipped' }
  | { readonly kind: 'symptom'; readonly from: string; readonly to: string }
  | { readonly kind: 'why'; readonly from: string; readonly to: string }
  | {
      readonly kind: 'deps'
      readonly added: readonly string[]
      readonly dropped: readonly string[]
    }
  /** The line stopped briefing. What the engine said about that is the whole answer. */
  | { readonly kind: 'left'; readonly said: string }

export interface Landing {
  readonly id: string
  readonly changes: readonly Change[]
  /** True where anything at all moved, which is what a screen redraws on. */
  readonly moved: boolean
}

function designOf(payload: BriefPayload): 'none' | 'written' {
  return payload.section === null ? 'none' : 'written'
}

/**
 * What changed between two readings of one line.
 *
 * Both sides are the engine's answers, so this compares two of its statements rather than
 * a statement against an expectation. A field it does not carry is a field this cannot
 * claim moved.
 */
export function landingBetween(before: Reading, after: Reading): Landing {
  const id = before.kind === 'read' ? before.payload.id : ''

  if (after.kind === 'gone') {
    // Deferred, retired, renumbered away. The refusal names where it went, and reading it
    // for meaning is not this app's business — showing it is.
    return { id, changes: [{ kind: 'left', said: after.refusal.said }], moved: true }
  }
  if (before.kind === 'gone') {
    // It came back: resumed, or filed again under the same id.
    return { id: after.payload.id, changes: [{ kind: 'marker', from: '', to: after.payload.status }], moved: true }
  }

  const was = before.payload
  const now = after.payload
  const changes: Change[] = []

  if (was.status !== now.status) {
    changes.push({ kind: 'marker', from: was.status, to: now.status })
  }
  if (!was.shipped && now.shipped) changes.push({ kind: 'shipped' })
  if (designOf(was) !== designOf(now)) {
    changes.push({ kind: 'design', from: designOf(was), to: designOf(now) })
  }
  if (was.symptom !== now.symptom) {
    changes.push({ kind: 'symptom', from: was.symptom, to: now.symptom })
  }
  if (was.why !== now.why) changes.push({ kind: 'why', from: was.why, to: now.why })

  const before_ = new Set(was.deps)
  const after_ = new Set(now.deps)
  const added = now.deps.filter((dep) => !before_.has(dep))
  const dropped = was.deps.filter((dep) => !after_.has(dep))
  if (added.length > 0 || dropped.length > 0) changes.push({ kind: 'deps', added, dropped })

  return { id: now.id, changes, moved: changes.length > 0 }
}

/**
 * One change as a line, for the column beside the stream.
 *
 * Said plainly and in the engine's own values: a marker is the emoji the project declared,
 * and a design is written or it is not.
 */
export function changeLine(change: Change): string {
  switch (change.kind) {
    case 'marker':
      return change.from === '' ? `marker ${change.to}` : `${change.from} → ${change.to}`
    case 'design':
      return change.to === 'written' ? 'design written' : 'design deleted'
    case 'shipped':
      return 'shipped, and in the ledger'
    case 'symptom':
      return 'symptom restated'
    case 'why':
      return 'why amended'
    case 'deps': {
      const added = change.added.length === 0 ? '' : `+${change.added.join(' +')}`
      const dropped = change.dropped.length === 0 ? '' : `-${change.dropped.join(' -')}`
      return `deps ${[added, dropped].filter((part) => part !== '').join(' ')}`
    }
    default:
      return change.said
  }
}

/**
 * Whether the stream and the files agree that the line shipped.
 *
 * The disagreement is the point: a session can say it shipped a line it did not, and the
 * files are what settle it. This names the mismatch rather than resolving it, because
 * which of the two somebody needs to look at depends on what they were doing.
 */
export function saidButNotDone(claimedShipped: boolean, landing: Landing): boolean {
  return claimedShipped && !landing.changes.some((change) => change.kind === 'shipped')
}
