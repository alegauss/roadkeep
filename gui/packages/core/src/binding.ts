import type { CriteriaPayload, Criterion, NonGoalsPayload } from './payloads'
import type { Door } from './refusals'

/**
 * The two lists a proposal is checked against, laid out for the places they are needed.
 *
 * A non-goal says what is not built and a criterion says what would finish a block, and
 * between them they decide what may become a line. Two verbs, one read each. They belong
 * where a person is about to write rather than on a page somebody has to remember to
 * open: the non-goals beside the add form, a block's criteria at the head of its list,
 * where the question of whether the block is finished is actually asked.
 *
 * **The two answers are not symmetric and this must not pretend otherwise.** A criterion
 * arrives with its lead, its reason and its address. A non-goal arrives as a lead alone —
 * the reason is in the file and no read publishes it — so there is no `why` on a non-goal
 * here, because a key that always held the empty string would read as a missing reason
 * rather than an unpublished one.
 *
 * **Empty is three different answers** and the engine spells which: ungoverned, unasked,
 * or every entry dropped. All three draw as no rows, and a list that showed nothing
 * without saying which would claim a project has no constraints when it has simply never
 * declared any.
 */

export interface NonGoal {
  readonly lead: string
  /**
   * The ids whose design quotes this lead. Empty means nothing has answered it in
   * writing, which is the nearest thing to a review state either list carries.
   */
  readonly answeredBy: readonly string[]
}

export interface Bounds {
  readonly file: string
  /** False where the project declares no list. A state, and one a screen has to say. */
  readonly governed: boolean
  readonly nonGoals: readonly NonGoal[]
  /** Entries the answer did not list. Above zero, `nonGoals` is a sample. */
  readonly elided: number
}

export function boundsFrom(payload: NonGoalsPayload): Bounds {
  return {
    file: payload.file,
    governed: payload.governed,
    nonGoals: payload.nonGoals.map((lead) => ({
      lead,
      answeredBy: payload.nonGoalsQuoted[lead] ?? [],
    })),
    elided: payload.nonGoalsElided,
  }
}

/** Criteria under one address, in the order the file spells them. */
export interface CriterionGroup {
  /** A block label, or a task id where a line carries its own. */
  readonly about: string
  readonly criteria: readonly Criterion[]
}

export interface Finishing {
  readonly file: string
  readonly governed: boolean
  /** Every block label the roadmap declares — what a narrowing can ask for. */
  readonly blocks: readonly string[]
  /** Which kind of nothing, in the engine's word. Empty string when there is something. */
  readonly empty: string
  readonly groups: readonly CriterionGroup[]
  readonly doors: readonly Door[]
}

/**
 * Group the criteria by what they are about, keeping file order inside each group.
 *
 * A Map because insertion order is the file's order, and the addresses are read off the
 * entries rather than taken from `blocks`: a block with no criteria has no group, and one
 * carrying criteria that `blocks` never listed still gets drawn.
 */
export function finishingFrom(payload: CriteriaPayload): Finishing {
  const grouped = new Map<string, Criterion[]>()
  for (const criterion of payload.criteria) {
    const group = grouped.get(criterion.about)
    if (group === undefined) grouped.set(criterion.about, [criterion])
    else group.push(criterion)
  }

  return {
    file: payload.file,
    governed: payload.governed,
    blocks: payload.blocks,
    empty: payload.empty ?? '',
    groups: [...grouped].map(([about, criteria]) => ({ about, criteria })),
    doors: payload.doors,
  }
}

/** One address's criteria, or nothing. The lookup a block heading makes. */
export function criteriaAbout(finishing: Finishing, about: string): readonly Criterion[] {
  return finishing.groups.find((group) => group.about === about)?.criteria ?? []
}

/**
 * Why a list is empty, or the empty string when it is not.
 *
 * Built out of what the payload carries and nothing else. `governed` is checked first
 * because ungoverned is the answer that means the project never declared the list at all,
 * which is different from having declared it and dropped everything in it.
 */
export function whyNothing(list: Bounds | Finishing): string {
  const rows = 'nonGoals' in list ? list.nonGoals.length : list.groups.length
  if (rows > 0) return ''
  if (!list.governed) return `nothing in ${list.file || 'this project'} governs this list`
  return 'empty' in list && list.empty !== '' ? list.empty : 'the list is declared and empty'
}
