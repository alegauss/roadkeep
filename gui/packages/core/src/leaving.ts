import type {
  DeferPayload,
  RemovedLine,
  ResumePayload,
  RetirePayload,
  ShipPayload,
  WroteLine,
} from './payloads'

/**
 * The four ways a line leaves, and the account each one gives of itself.
 *
 * `ship` writes the ledger entry, clears the roadmap line and drops the section, in one
 * transaction or none. `retire` records a departure without a ship. `defer` moves the line
 * to the store keeping every slot. `resume` brings it back.
 *
 * **The account is read and never composed.** Each verb already prints what it touched, so
 * a `Departure` says which files were written and what became of the line, and each
 * payload keeps its own fields beside it. Flattening the four would lose exactly what
 * tells them apart: a section dropped is not a section carried, and an abandonment is not
 * a replacement.
 *
 * **Each takes a sentence the person writes.** `--why` on a ship is the outcome and not
 * the roadmap's problem inherited; `--reason` on a retire and a defer is the author's own.
 * Nothing here drafts one — `No field this app composes`.
 *
 * **Each is irreversible in the direction that matters.** A retired id never comes back
 * and a shipped section is deleted, which is what makes showing the command before it runs
 * more than a nicety. That surface is RG31's neighbour; what this leaves it is an answer
 * that accounts for every edit.
 */

/** How a line left, in this app's word for the four verbs. */
export type Leaving = 'shipped' | 'retired' | 'deferred' | 'resumed'

export interface Edit {
  readonly file: string
  /** What happened there, and to which line. */
  readonly wrote: number | null
  readonly removed: number | null
}

export interface Departure {
  readonly id: string
  readonly how: Leaving
  /** Every file this write touched, in the order the answer named them. */
  readonly edits: readonly Edit[]
  /** The line as it now reads wherever it landed, or empty where nothing landed. */
  readonly rendered: string
  /** Ids whose dep annotations were re-derived because this one left. */
  readonly refreshed: readonly string[]
  /**
   * Lines still naming this id. A retirement leaves them pointing at something the
   * resolver reads as never, which is the one consequence a person cannot see from here.
   */
  readonly dependents: readonly string[]
  /** Whether the line is still open afterwards — a partial ship leaves it so. */
  readonly stillOpen: boolean
}

function wrote(where: WroteLine | null): Edit[] {
  return where === null || where.file === ''
    ? []
    : [{ file: where.file, wrote: where.line, removed: null }]
}

function removed(where: RemovedLine | null): Edit[] {
  return where === null || where.file === ''
    ? []
    : [{ file: where.file, wrote: null, removed: where.removed }]
}

/**
 * The roadmap edit a ship made, which is two different things under one key.
 *
 * A ship that closed the line removed it. A partial left it there with a new marker. A
 * reader taking only `removed` would draw the second as the first.
 */
function roadmapEdit(roadmap: ShipPayload['roadmap']): Edit[] {
  if (roadmap === null || roadmap.file === '') return []
  if (roadmap.open) return [{ file: roadmap.file, wrote: roadmap.line, removed: null }]
  return [{ file: roadmap.file, wrote: null, removed: roadmap.removed }]
}

export function shipped(payload: ShipPayload): Departure {
  const improvements = payload.improvements
  return {
    id: payload.id,
    how: 'shipped',
    edits: [
      ...wrote(payload.changelog),
      ...roadmapEdit(payload.roadmap),
      ...(improvements?.dropped == null
        ? []
        : [{ file: improvements.file, wrote: null, removed: improvements.dropped.first }]),
      ...wrote(payload.decisions),
    ],
    rendered: payload.changelog?.rendered ?? '',
    refreshed: payload.refreshed,
    dependents: [],
    // Carried, not worked out: the engine says whether the line is still a task.
    stillOpen: payload.roadmap?.open ?? false,
  }
}

export function retired(payload: RetirePayload): Departure {
  return {
    id: payload.id,
    how: 'retired',
    edits: [...wrote(payload.changelog), ...removed(payload.roadmap)],
    rendered: payload.changelog?.rendered ?? '',
    refreshed: payload.refreshed,
    dependents: payload.dependents,
    stillOpen: false,
  }
}

export function deferred(payload: DeferPayload): Departure {
  return {
    id: payload.id,
    how: 'deferred',
    edits: [...wrote(payload.deferred), ...removed(payload.roadmap)],
    rendered: payload.deferred?.rendered ?? '',
    refreshed: payload.refreshed,
    dependents: payload.dependents,
    // Set aside is not closed. The id, the deps, the symptom and the section all survive.
    stillOpen: true,
  }
}

export function resumed(payload: ResumePayload): Departure {
  return {
    id: payload.id,
    how: 'resumed',
    edits: [...wrote(payload.roadmap), ...removed(payload.deferred)],
    rendered: payload.roadmap?.rendered ?? '',
    refreshed: payload.refreshed,
    dependents: [],
    stillOpen: true,
  }
}

/**
 * What the write did, as one sentence over the files it touched.
 *
 * Built from the edits the answer named and nothing else. The file names are the engine's
 * — which file holds which role is roadkeep's rule, and a governed filename written here
 * would be the literal the non-goals refuse.
 */
export function accountOf(departure: Departure): string {
  if (departure.edits.length === 0) return `${departure.id}: nothing was written`
  const parts = departure.edits.map((edit) =>
    edit.wrote === null
      ? `${edit.file}:${String(edit.removed ?? 0)} removed`
      : `${edit.file}:${String(edit.wrote)} written`,
  )
  return `${departure.id} ${departure.how}: ${parts.join(', ')}`
}

/**
 * What a retirement leaves behind, or the empty string.
 *
 * Named rather than counted, because the ids are what somebody has to go and look at: the
 * resolver reads a retired dep as never, so every line here is one that will not become
 * ready by anything happening to this id.
 */
export function leftPointing(departure: Departure): string {
  if (departure.dependents.length === 0) return ''
  return (
    `${String(departure.dependents.length)} line(s) still name ${departure.id}: ` +
    departure.dependents.join(', ')
  )
}
