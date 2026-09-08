import type { BudgetPayload, FieldBudget, SectionBudget } from './payloads'

/**
 * The budget, before the sentence.
 *
 * `budget` prices the fields of a line that does not exist yet: what the symptom has, what
 * the why has once the structure and the deps are counted, what a section has in words,
 * and the aim each is composed towards. A form calls it when it opens.
 *
 * **`allowed` and not `limit` is what a counter counts down from.** `[limits] why` is 200
 * and the rendered line's 320 binds first, so on a line carrying deps the why has less —
 * and `boundByLine` says which was the binding number. A screen counting against the limit
 * would promise room the write is going to refuse.
 *
 * **An aim, not a gate.** `aim` is what to compose towards and `limit` is what refuses.
 * Both are shown: a field written to its limit is one nobody can add a clause to later.
 * The verb still decides and this only reports.
 *
 * **Re-read when the arithmetic moves.** The why's allowance depends on the rendered line,
 * which depends on the deps, the marker and the pointer, so adding a dep changes what the
 * sentence may say. The budget is asked again rather than adjusted here.
 *
 * **Exit 1 means a draft is over, not that the call was refused** — exactly as for `lint`.
 * `over` is the field that says so, and the answer is an ordinary payload.
 */

/** What a screen needs to draw one field's counter. */
export interface Counter {
  readonly field: string
  /** What to count down from. Never `limit`, which can be the looser of the two. */
  readonly allowed: number
  readonly taken: number
  /** What is left of the allowance. Zero and `over` above zero is the refusing state. */
  readonly left: number
  /** What is left against the aim, which is the number worth composing towards. */
  readonly room: number
  readonly over: number
  readonly unit: string
  /**
   * Why the allowance is what it is, where it is not the field's own limit. Empty when
   * the field's declared limit was the binding one.
   */
  readonly boundBy: string
}

/**
 * One field, as something to count against.
 *
 * `boundBy` is composed and everything else is carried. It exists because "176" with no
 * explanation reads as a number somebody made up, and the answer already knows it was the
 * line and not `[limits] why`.
 */
export function counterOf(field: FieldBudget): Counter {
  return {
    field: field.field,
    allowed: field.allowed,
    taken: field.taken,
    left: field.left,
    room: field.room,
    over: field.over,
    unit: field.unit,
    boundBy: field.boundByLine ? 'the rendered line' : '',
  }
}

export function countersOf(payload: BudgetPayload): Counter[] {
  return payload.fields.map(counterOf)
}

/** One field by name, or null where this call did not price it. */
export function counterFor(payload: BudgetPayload, field: string): Counter | null {
  const found = payload.fields.find((one) => one.field === field)
  return found === undefined ? null : counterOf(found)
}

/**
 * Whether any drafted field is past its limit.
 *
 * Read off `over` and not off the exit code: `budget` exits 1 when a draft is over, the
 * way `lint` exits 1 when it finds something, and both answer with an ordinary payload.
 */
export function anyOver(payload: BudgetPayload): boolean {
  return payload.fields.some((field) => field.over > 0) || (payload.section?.over ?? 0) > 0
}

/** The fields a draft has already outgrown, so a form can mark them. */
export function overBy(payload: BudgetPayload): Counter[] {
  return countersOf(payload).filter((counter) => counter.over > 0)
}

/**
 * What the line's own shape costs before a word of prose.
 *
 * The marker, the deps and the pointer are structure, and they are why adding a dep takes
 * room away from the sentence. Worth showing beside the counters, because otherwise the
 * number moving looks arbitrary.
 */
export function structureOf(payload: BudgetPayload): string {
  if (payload.lineMax === 0) return ''
  const deps = payload.deps.length
  const because = deps === 0 ? '' : ` with ${String(deps)} dep${deps === 1 ? '' : 's'}`
  return (
    `${String(payload.structure)} of ${String(payload.lineMax)} is structure${because}, ` +
    `leaving ${String(payload.prose)} for prose`
  )
}

/**
 * A counter as a person reads it.
 *
 * The aim comes second because it is advice and the allowance is the wall. Over the limit
 * says by how much, since "0 left" and "14 over" are different amounts of rewriting.
 */
export function saidOfCounter(counter: Counter): string {
  if (counter.over > 0) {
    return `${String(counter.taken)} of ${String(counter.allowed)}, ${String(counter.over)} over`
  }
  const bound = counter.boundBy === '' ? '' : ` (${counter.boundBy})`
  const aim = counter.room > 0 ? `, ${String(counter.room)} to the aim` : ''
  return `${String(counter.left)} left of ${String(counter.allowed)}${bound}${aim}`
}

/** What a section has left, where this call priced one. */
export function sectionCounter(payload: BudgetPayload): SectionBudget | null {
  return payload.section
}
