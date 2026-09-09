import { narrowingOfBrief, type BriefPayload, type HeldClaim, type Narrowing } from './payloads'

/**
 * What a task costs to start, in one read.
 *
 * `brief` joins the line, its deps and what resolves them, the design section whole, what
 * shipping it would unblock, the criteria and non-goals that bind it, whether anybody is
 * holding it, and what the ledger already shipped citing the id. All of that is one call.
 *
 * **Six reads composed here would be six chances to compose them differently from the way
 * the tool does.** So this file assembles nothing: it lays out one payload, and everything
 * on the screen came from that payload.
 *
 * Two rules the block's criteria turn on. **Readiness is never derived** — the word is
 * carried, and there is no rule here that could disagree with the resolver that produced
 * it. And **the prose is shown as the file stores it**: the section body is a string,
 * passed through, never parsed, since parsing Markdown is a non-goal and re-wrapping
 * prose written to a column is how a design stops reading the way it was written.
 */

export interface TaskDetail {
  readonly payload: BriefPayload
  /** True when nobody is holding the line and nothing blocks it, in the engine's word. */
  readonly startable: boolean
  /** The deps that are not settled, so a blocked line says what it is waiting for. */
  readonly blocking: readonly string[]
  /** What the brief left out. Non-empty means the screen must say so. */
  readonly narrowing: Narrowing
  /** Whether the design section is there to show. */
  readonly hasDesign: boolean
}

/**
 * A dep counts as settled when the engine says so.
 *
 * The words are the engine's and the set is deliberately what it reports rather than what
 * this app would call finished: a retired dep is settled — the resolver reads it as never
 * — and a client that treated retirement as still-blocking would hold a line back for a
 * task that is never coming.
 */
const SETTLED = new Set(['shipped', 'retired'])

export function detailFrom(payload: BriefPayload): TaskDetail {
  const blocking = payload.depsResolved
    .filter((dep) => !SETTLED.has(dep.status))
    .map((dep) => dep.dep)

  return {
    payload,
    // Read, not worked out. `readiness` is the resolver's answer and this only compares it.
    startable: payload.readiness === 'ready' && payload.held.length === 0,
    blocking,
    narrowing: narrowingOfBrief(payload),
    hasDesign: payload.section !== null,
  }
}

/**
 * The marker and the claim, side by side, because they answer different questions.
 *
 * The marker says what state the **work** is in; the claim says whether a **worker** is on
 * it right now. They move independently — a claim is dated and released on a sixty-minute
 * window and a marker is not — so a line can be started with nobody holding it, held with
 * the marker not yet moved, or both.
 *
 * **Neither is a proxy for the other**, and the two obvious shortcuts are both wrong.
 * Reading the marker as the claim makes every line somebody once started look taken
 * forever, which is what the window exists to prevent. Reading the claim as the only truth
 * makes a line whose claim lapsed look free while a session is still working it.
 *
 * So this reports both and marks where they disagree. **The disagreement is drawn and not
 * resolved**: it is exactly the place somebody has to look, and an app that picked a winner
 * would be hiding the one fact worth showing.
 */
export interface Underway {
  /** The line carries this project's working marker. */
  readonly marked: boolean
  /** Who holds it now, or null. The engine's registry, not a state this app kept. */
  readonly held: HeldClaim | null
  /**
   * The two do not agree. True for a started line nobody holds, and for a held line that
   * was never moved — and false where the project declares no working marker, since one
   * fact cannot disagree with a question this project does not ask.
   */
  readonly disagree: boolean
}

/**
 * @param working this project's working marker, from `workingMarker`. Empty where the
 *   project has none, which makes the marker half of this unanswerable rather than false.
 */
export function underway(detail: TaskDetail, working: string): Underway {
  const marked = working !== '' && detail.payload.status === working
  const held = detail.payload.held[0] ?? null
  return { marked, held, disagree: working !== '' && marked !== (held !== null) }
}

/**
 * The pair as a sentence, or the empty string where there is nothing to say.
 *
 * Every version names what is true rather than what this app concluded, and the two that
 * disagree say so out loud — a reader who is told only "in progress" cannot tell a line
 * somebody is on from one abandoned an hour ago.
 */
export function saidOfUnderway(state: Underway): string {
  const by = state.held?.by ?? ''
  const since = state.held?.since ?? ''

  if (state.held !== null && state.marked) {
    return `${by || 'somebody'} is working it, since ${since || 'earlier'}`
  }
  if (state.held !== null) {
    return `held by ${by || 'somebody'} since ${since || 'earlier'}, and the line has not been moved to the working marker`
  }
  if (state.marked) {
    return 'started, and no claim on it is still live'
  }
  return ''
}

/**
 * Why this line cannot be started yet, or the empty string.
 *
 * Built out of what the engine reported and nothing else — a sentence naming the ids or
 * the holder, rather than a verdict this app reached.
 */
export function whyNotStartable(detail: TaskDetail): string {
  if (detail.startable) return ''

  const held = detail.payload.held[0]
  if (held !== undefined) {
    return `held by ${held.by || 'another worker'} since ${held.since || 'earlier'}`
  }
  if (detail.blocking.length > 0) {
    return `waiting on ${detail.blocking.join(', ')}`
  }
  if (detail.payload.requires.length > 0 && detail.payload.readiness !== 'ready') {
    return `needs ${detail.payload.requires.join(' and ')}`
  }
  return detail.payload.readiness
}

/**
 * The design, exactly as the file stores it, or null.
 *
 * Null covers two different things and the caller has to tell them apart: a line with no
 * section at all, and one whose prose was not asked for. `sectionAbsence` is the engine's
 * own sentence about the first.
 */
export function designOf(detail: TaskDetail): string | null {
  return detail.payload.section?.body ?? null
}
