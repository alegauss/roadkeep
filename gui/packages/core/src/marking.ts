import type { ConfigPayload, StatusPayload } from './payloads'
import type { Refusal } from './refusals'
import { fieldsRefused } from './refusals'

/**
 * Moving a marker, and what moves with it.
 *
 * `status` sets a marker in the roadmap and nowhere else — a sibling file carrying one for
 * the same id is refused rather than reconciled, because two files that both express
 * status will eventually express different status and nothing says which is right.
 *
 * **The markers offered are the ones the project declared.** `[markers] open` is four
 * emoji in this repository and something else in the next one, so a dropdown built from a
 * literal here is the rule compiled into the client that the non-goals refuse.
 *
 * **A move to the working marker takes a claim; a move off it gives one back.** The answer
 * says which, so the claim is drawn as what it is rather than inferred from the marker
 * somebody just wrote. RG74 is the reading half of the same fact and stands: the marker
 * says what state the work is in, the claim says whether a worker is on it, and neither is
 * a proxy for the other.
 */

/**
 * The markers `status` will accept, in the order the project declares them.
 *
 * The open set alone. Shipped and retired are written by `ship` and `retire`, which are
 * transactions across three files, and offering either here would be a door onto a verb
 * that is not this one.
 */
export function openMarkers(config: ConfigPayload): string[] {
  const entry = config.keys.find((key) => key.address === 'markers.open')
  if (entry?.set === undefined || entry.set === null || entry.set === '') return []

  try {
    const parsed: unknown = JSON.parse(entry.set)
    if (Array.isArray(parsed)) {
      return parsed.filter((value): value is string => typeof value === 'string')
    }
  } catch {
    // Not JSON — a bare value the file spells its own way.
  }
  return [entry.set.replace(/^["']|["']$/g, '')]
}

/**
 * The marker this project moves a line to when somebody starts it, or the empty string.
 *
 * **Declared or built in, and never guessed** (RG74). Most projects declare no
 * `markers.working` and every one of them still has one, which is why `config` carries what
 * a build uses when nothing declares it. Empty is a real answer and not a failure: a
 * backlog whose open set never spells the built-in marker has no working marker, and a
 * screen that invented one would show every line as started.
 */
export function workingMarker(config: ConfigPayload): string {
  const entry = config.keys.find((key) => key.address === 'markers.working')
  const spelled = entry?.set ?? entry?.fallback ?? ''
  const marker = spelled.replace(/^["']|["']$/g, '')
  // Held to the open set for the engine's own reason: a marker outside it is one no line
  // may carry, so reporting it would be describing a state this project cannot be in.
  return openMarkers(config).includes(marker) ? marker : ''
}

/** What a marker write did to the claim on its line. The engine's own three answers. */
export type ClaimEffect = 'claimed' | 'released' | 'neither'

export interface Moved {
  readonly id: string
  readonly from: string
  readonly to: string
  /** False where the line already carried the marker. An answer, not a failure. */
  readonly changed: boolean
  readonly rendered: string
  readonly claim: ClaimEffect
  /** Ids whose dep annotations were re-derived because this one moved. */
  readonly refreshed: readonly string[]
  readonly wrote: readonly string[]
}

/**
 * Read what the write did.
 *
 * `claim` is carried, and an unrecognised word becomes `neither` rather than being passed
 * through: this is the one field a screen branches on, and a fourth answer nobody has seen
 * should draw as no claim change and not as a state with no rendering.
 */
export function movedFrom(payload: StatusPayload): Moved {
  const claim = payload.claim ?? ''
  return {
    id: payload.id,
    from: payload.from,
    to: payload.to,
    changed: payload.changed,
    rendered: payload.rendered,
    claim: claim === 'claimed' || claim === 'released' ? claim : 'neither',
    refreshed: payload.refreshed,
    wrote: payload.wrote,
  }
}

/**
 * What to say about the move, in one line.
 *
 * The claim half is said out loud because it is the half nobody asked for: somebody
 * choosing a marker from a list has not obviously said "and take this line", and a write
 * that quietly did is the two-workers failure arriving through the verb meant to stop it.
 */
export function saidOfMove(moved: Moved): string {
  const marker = moved.changed ? `${moved.from} → ${moved.to}` : `already ${moved.to}`
  if (moved.claim === 'claimed') return `${marker}, and the line is yours`
  if (moved.claim === 'released') return `${marker}, and the claim is given back`
  return marker
}

/**
 * Whether a refusal is one no input can fix.
 *
 * A live claim on the line names no field: it is a sentence about a person, and the claim
 * may be the caller's own since a claim names nobody. So there is no box to mark, and a
 * screen that looked for one would highlight an input at random. Asked as "did the engine
 * name a field", never by reading the sentence.
 */
export function aboutNoInput(refusal: Refusal): boolean {
  return fieldsRefused(refusal).length === 0
}
