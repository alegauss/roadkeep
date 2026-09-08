import { describe, expect, it } from 'vitest'

import {
  anyOver,
  counterFor,
  countersOf,
  overBy,
  saidOfCounter,
  structureOf,
} from './budgeting'
import { readBudgetPayload, type BudgetPayload } from './payloads'
import { buildArgv } from './client'

/** Captured from a real `budget --block D --dep RG29 --symptom … --json`. */
const BUDGET = {
  id: 'RG85',
  status: '📋',
  deps: ['RG29'],
  open_line: false,
  line_max: 320,
  structure: 42,
  ref: 'RG85',
  ref_assumed: false,
  prose: 278,
  fields: [
    {
      field: 'symptom',
      limit: 120,
      allowed: 120,
      aim: 18,
      taken: 22,
      left: 98,
      over: 0,
      drafted: true,
      replaced: false,
      sentences: 0,
      terminated: false,
      room: 14,
      unit: 'utf-16-code-units',
      bound_by_line: false,
      source: 'roadkeep.toml:20 [limits].symptom',
    },
    {
      field: 'why',
      limit: 200,
      allowed: 176,
      aim: 26,
      taken: 0,
      left: 176,
      over: 0,
      drafted: false,
      replaced: false,
      sentences: 0,
      terminated: false,
      room: 26,
      unit: 'utf-16-code-units',
      bound_by_line: true,
      source: 'roadkeep.toml:21 [limits].why',
    },
  ],
  section: {
    anchor: 'RG85',
    role: 'improvements',
    written: false,
    unit: 'words',
    limit: 250,
    allowed: 250,
    aim: 233,
    taken: 0,
    left: 250,
    room: 233,
    subtree: 0,
    over: 0,
  },
}

function budget(over: Record<string, unknown> = {}): BudgetPayload {
  const parsed = readBudgetPayload({ ...BUDGET, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG36: allowed and not limit is what a counter counts down from', () => {
  it('counts the why against what the line leaves it, not against its own limit', () => {
    // `[limits] why` is 200 and the rendered line's 320 binds first. Counting against 200
    // would promise 24 characters the write is going to refuse.
    const why = counterFor(budget(), 'why')

    expect(why?.allowed).toBe(176)
    expect(why?.left).toBe(176)
    expect(why?.boundBy).toBe('the rendered line')
  })

  it('says nothing bound it where the field own limit was the binding number', () => {
    const symptom = counterFor(budget(), 'symptom')

    expect(symptom?.allowed).toBe(120)
    expect(symptom?.boundBy).toBe('')
  })

  it('answers nothing for a field this call did not price', () => {
    expect(counterFor(budget(), 'lead')).toBeNull()
  })

  it('carries the unit, because characters and words are not the same field', () => {
    expect(counterFor(budget(), 'symptom')?.unit).toBe('utf-16-code-units')
    expect(budget().section?.unit).toBe('words')
  })
})

describe('RG36: an aim, not a gate', () => {
  it('shows what is left and what is left to the aim, which are different numbers', () => {
    // A field written to its limit is one nobody can add a clause to later.
    const symptom = counterFor(budget(), 'symptom')!

    expect(symptom.left).toBe(98)
    expect(symptom.room).toBe(14)
    expect(saidOfCounter(symptom)).toBe('98 left of 120, 14 to the aim')
  })

  it('names what bound the allowance when it was not the field limit', () => {
    expect(saidOfCounter(counterFor(budget(), 'why')!)).toBe(
      '176 left of 176 (the rendered line), 26 to the aim',
    )
  })

  it('drops the aim once a draft is past it, since it is advice and not a wall', () => {
    const past = counterFor(budget({ fields: [{ ...BUDGET.fields[0], taken: 110, left: 10, room: 0 }] }), 'symptom')!

    expect(saidOfCounter(past)).toBe('10 left of 120')
  })
})

describe('RG36: over is read from the answer, never from the exit code', () => {
  it('says by how much, because zero left and fourteen over are different rewrites', () => {
    const over = counterFor(
      budget({ fields: [{ ...BUDGET.fields[0], taken: 134, left: 0, over: 14, room: 0 }] }),
      'symptom',
    )!

    expect(saidOfCounter(over)).toBe('134 of 120, 14 over')
  })

  it('finds the fields a draft outgrew, so a form can mark them', () => {
    const payload = budget({
      fields: [
        { ...BUDGET.fields[0], taken: 134, left: 0, over: 14, room: 0 },
        BUDGET.fields[1],
      ],
    })

    expect(anyOver(payload)).toBe(true)
    expect(overBy(payload).map((one) => one.field)).toEqual(['symptom'])
  })

  it('counts a section past its budget too', () => {
    // `budget` exits 1 for this the way `lint` exits 1 when it finds something, and both
    // answer with an ordinary payload — so the reading is the payload's.
    const payload = budget({ section: { ...BUDGET.section, taken: 262, left: 0, over: 12 } })

    expect(anyOver(payload)).toBe(true)
    expect(overBy(payload)).toEqual([])
  })

  it('is quiet on a line with nothing over', () => {
    expect(anyOver(budget())).toBe(false)
    expect(overBy(budget())).toEqual([])
  })
})

describe('RG36: why the number moves', () => {
  it('says what the line shape costs before a word of prose', () => {
    // Otherwise the why losing 24 characters when a dep is added looks arbitrary.
    expect(structureOf(budget())).toBe('42 of 320 is structure with 1 dep, leaving 278 for prose')
  })

  it('counts two deps as two, and none as none', () => {
    expect(structureOf(budget({ deps: ['RG1', 'RG2'] }))).toContain('with 2 deps')
    expect(structureOf(budget({ deps: [] }))).toBe('42 of 320 is structure, leaving 278 for prose')
  })

  it('says nothing where no line was priced', () => {
    expect(structureOf(budget({ line_max: 0 }))).toBe('')
  })

  it('prices every field the answer carried', () => {
    expect(countersOf(budget()).map((one) => one.field)).toEqual(['symptom', 'why'])
  })
})

describe('RG36: the read a form makes when it opens', () => {
  it('prices a line that does not exist yet, from its block and its deps', () => {
    expect(buildArgv('/w', 'budget', { block: 'D', deps: ['RG29', 'RG5'] })).toEqual([
      '-C',
      '/w',
      'budget',
      '--block',
      'D',
      '--dep',
      'RG29',
      '--dep',
      'RG5',
      '--json',
    ])
  })

  it('measures a draft rather than sending it anywhere', () => {
    const argv = buildArgv('/w', 'budget', { block: 'D', symptom: 'a draft', why: 'A sentence.' })

    expect(argv).toContain('--symptom')
    expect(argv).toContain('a draft')
    expect(argv).toContain('--why')
  })

  it('prices a section by its anchor, against the prose file that holds it', () => {
    expect(buildArgv('/w', 'budget', { anchor: 'RG36', role: 'decisions' })).toEqual([
      '-C',
      '/w',
      'budget',
      '--anchor',
      'RG36',
      '--role',
      'decisions',
      '--json',
    ])
  })

  it('prices the sentence a departure writes, which is a different limit', () => {
    expect(buildArgv('/w', 'budget', { id: 'RG36', ship: true })).toContain('--ship')
    expect(buildArgv('/w', 'budget', { id: 'RG36', defer: true })).toContain('--defer')
    // One flag with an optional value: bare is an abandonment, named is a supersession.
    expect(buildArgv('/w', 'budget', { id: 'RG36', retire: true })).toEqual([
      '-C',
      '/w',
      'budget',
      'RG36',
      '--retire',
      '--json',
    ])
    expect(
      buildArgv('/w', 'budget', { id: 'RG36', retire: true, supersededBy: 'RG90' }),
    ).toContain('RG90')
  })
})
