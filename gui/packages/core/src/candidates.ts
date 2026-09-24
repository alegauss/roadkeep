import type { ProjectRow } from './portfolio'

/**
 * Seventeen answers to "what next", side by side.
 *
 * Each project's `pick` applies three tiers inside its own file, and **that ranking is
 * roadkeep's and stays roadkeep's**. What this app adds is only the comparison: the
 * candidates laid out together with the tier each was chosen by, so a person reads
 * seventeen answers instead of remembering them.
 *
 * What it must not do is order the projects against each other. There is no field in the
 * format that would justify one — no priority across repositories, no size, no date — so
 * any ordering this app produced would be a number it invented, presented next to numbers
 * a verb printed. That is exactly the fiction the non-goals refuse, and it is the more
 * dangerous half of it: an invented total looks obviously derived, while an invented
 * *ranking* looks like advice.
 *
 * So the board is in the recorded project order, which is the person's own, and the tier
 * is shown rather than sorted on. `tiers` is offered so a view can filter by one without
 * this file deciding which comes first.
 */

export interface Candidate {
  /** The project this line came from. */
  readonly project: string
  readonly name: string
  readonly id: string
  readonly symptom: string
  readonly block: string
  readonly status: string
  /** Which tier of roadkeep's own three answered. */
  readonly tier: string
}

export interface CandidateBoard {
  /** One per project that offered a line, in the recorded project order. */
  readonly candidates: readonly Candidate[]
  /**
   * Projects whose backlog offered nothing. An answer, not an absence — a finished
   * backlog and one that has not been read are different things and both matter.
   */
  readonly nothingToPick: readonly string[]
  /** Projects still pending or unreadable: no answer rather than no candidate. */
  readonly unanswered: readonly string[]
  /**
   * The distinct tiers present, in the order they first appear. Data-derived, and not a
   * precedence: which tier outranks which is roadkeep's and this app was not told it.
   */
  readonly tiers: readonly string[]
}

export function candidateBoard(rows: readonly ProjectRow[]): CandidateBoard {
  const candidates: Candidate[] = []
  const nothingToPick: string[] = []
  const unanswered: string[] = []
  const tiers: string[] = []

  for (const row of rows) {
    if (row.state !== 'read' || row.next === null) {
      unanswered.push(row.path)
      continue
    }
    if (row.next.id === null) {
      nothingToPick.push(row.path)
      continue
    }

    candidates.push({
      project: row.path,
      name: row.name,
      id: row.next.id,
      symptom: row.next.symptom,
      block: row.next.block,
      status: row.next.status,
      tier: row.next.tier,
    })
    if (!tiers.includes(row.next.tier)) tiers.push(row.next.tier)
  }

  return { candidates, nothingToPick, unanswered, tiers }
}

/**
 * The candidates chosen by one tier.
 *
 * A filter and not a sort. Asking for "everything already in progress" is a question about
 * roadkeep's own classification; asking which project's in-progress line matters most is a
 * question nobody here can answer.
 */
export function inTier(board: CandidateBoard, tier: string): Candidate[] {
  return board.candidates.filter((candidate) => candidate.tier === tier)
}
