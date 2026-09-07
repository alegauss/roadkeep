import type { BriefBudget, RationaleSection } from './payloads'

/**
 * The half of a task that explains it, laid out for a screen to draw.
 *
 * A rationale section is where a design lives until the ship that deletes it, and it is
 * what a reviewer needs before agreeing the line is right. `brief` already carries it —
 * the prose, where it lives, and what it has left of its budget — so nothing here goes
 * back to the engine and nothing here is worked out.
 *
 * **The prose is shown as the file stores it.** The body arrives as one string, already
 * wrapped to the column the project declared, and it is passed through: never parsed,
 * never reflowed, never trimmed. `No Markdown parsed in this app` bounds this and does
 * not forbid it — the prose is a field off a payload and not a file this app read — but a
 * renderer that turned `**` into markup would be reading the format a second time, and
 * what a reviewer needs is what the gate measured and what a commit will diff.
 *
 * **Three states, not two.** Prose is the ordinary one. A section whose body was not
 * asked for — `show --no-body` — has an address and no text, and drawing that as an empty
 * design would report a defect that is not there. A pointer resolving to nothing has
 * neither, and the engine's own sentence about it is the answer.
 */

/**
 * Prose, an address with the prose withheld, or no section at all.
 *
 * Three words rather than two booleans, because the pair `hasSection`/`hasBody` has a
 * fourth combination that cannot happen and a caller would still have to handle.
 */
export type DesignState = 'shown' | 'withheld' | 'absent'

export interface Design {
  readonly state: DesignState
  /** The heading text, in the engine's own words. Empty where there is no section. */
  readonly title: string
  readonly anchor: string
  readonly file: string
  readonly first: number
  readonly last: number
  /** The prose exactly as the payload carried it. Null in the other two states. */
  readonly prose: string | null
  /**
   * The same prose split on its own line breaks, so a screen can draw the file's wrapping
   * without measuring anything. A split, not a reflow: joining them back gives the body.
   */
  readonly lines: readonly string[]
  /** The subtree's count, and this heading's own. Both the engine's. */
  readonly words: number
  readonly ownWords: number
  /** What the prose has left, or null where the engine priced nothing. */
  readonly budget: BriefBudget['section']
  /** Why there is no section, in the engine's words. Empty unless the state is absent. */
  readonly absence: string
}

/**
 * A section that is not there, with the engine's sentence about it and nothing invented.
 *
 * The zeros are absences and not counts: there is no prose to have a length, and a
 * screen reading `state` first never reaches them.
 */
function noDesign(absence: string): Design {
  return {
    state: 'absent',
    title: '',
    anchor: '',
    file: '',
    first: 0,
    last: 0,
    prose: null,
    lines: [],
    words: 0,
    ownWords: 0,
    budget: null,
    absence,
  }
}

/**
 * Split the body the way the file breaks it, and no other way.
 *
 * `\r\n` is one break and not two — a Windows checkout otherwise leaves a carriage
 * return dangling off every line — and nothing else is touched: a trailing break is a
 * blank line the file has, and dropping it would be an edit to prose this app does not
 * edit.
 */
function brokenAsWritten(body: string): string[] {
  return body.split(/\r\n|\r|\n/)
}

/**
 * What a payload says about its own design.
 *
 * Structural on purpose: `brief` and `show` both carry a section and the sentence about
 * its absence, and only `brief` prices it. One reader over both is what stops the two
 * screens disagreeing about a state neither of them invented.
 */
export function designFrom(source: {
  readonly section: RationaleSection | null
  readonly sectionAbsence: string
  readonly budget?: BriefBudget | null
}): Design {
  const section = source.section
  if (section === null) return noDesign(source.sectionAbsence)

  const budget = source.budget?.section ?? null
  const body = section.body

  return {
    // Withheld and empty are different answers. `show --no-body` sends null, and a
    // section that exists and says nothing is a defect this must not disguise as one.
    state: body === null ? 'withheld' : 'shown',
    title: section.title,
    anchor: section.anchor,
    file: section.file,
    first: section.first,
    last: section.last,
    prose: body,
    lines: body === null ? [] : brokenAsWritten(body),
    words: section.words,
    ownWords: section.ownWords,
    budget,
    absence: '',
  }
}

/**
 * Where the prose lives, as one string somebody can go and open.
 *
 * The path is the engine's — which file holds the rationale is a rule roadkeep owns, and
 * a governed filename written in here would be the literal the non-goals refuse.
 */
export function whereDesignLives(design: Design): string {
  if (design.state === 'absent' || design.file === '') return ''
  if (design.first === design.last) return `${design.file}:${String(design.first)}`
  return `${design.file}:${String(design.first)}-${String(design.last)}`
}

/**
 * The count and the limit, beside the prose, in the engine's own numbers and unit.
 *
 * A section near its budget is a design about to need splitting, and that is worth
 * knowing before somebody adds to it — so the number shown has to be the number the gate
 * will use. Nothing is added up here, and `over` is the engine's word for past the limit
 * rather than a comparison this app made.
 */
export function wordsAgainstLimit(design: Design): string {
  const budget = design.budget
  if (budget === null || !budget.written || budget.limit === 0) {
    return design.words === 0 ? '' : String(design.words)
  }

  const unit = budget.unit === '' ? '' : ` ${budget.unit}`
  const counted = `${String(budget.taken)} of ${String(budget.limit)}${unit}`
  return budget.over > 0 ? `${counted}, ${String(budget.over)} over` : counted
}
