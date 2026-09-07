import { describe, expect, it } from 'vitest'

import { boundsFrom, criteriaAbout, finishingFrom, whyNothing } from './binding'
import {
  readCriteriaPayload,
  readNonGoalsPayload,
  type CriteriaPayload,
  type NonGoalsPayload,
} from './payloads'

/** Captured from a real `non-goal list --json`. */
const NON_GOALS = {
  file: 'docs/ROADMAP.md',
  governed: true,
  non_goals: [
    'No Markdown parsed in this app',
    'No write to a governed file',
    'No store of its own',
  ],
  non_goals_elided: 0,
  non_goals_quoted: {
    'No store of its own': ['RG28'],
  },
}

/** Captured from a real `criterion list --json`. */
const CRITERIA = {
  file: 'docs/ROADMAP.md',
  governed: true,
  blocks: ['A', 'B', 'C', 'D'],
  empty: null,
  criteria: [
    {
      about: 'A',
      lead: 'The client runs with no Electron and no React',
      why: 'The transport is one interface, so the same reads answer anywhere.',
      line: 81,
      shaped: true,
    },
    {
      about: 'D',
      lead: 'A task opens with everything starting it costs',
      why: "The detail is brief's own join, so the screen is one read and not six.",
      line: 117,
      shaped: true,
    },
    {
      about: 'D',
      lead: 'Readiness is never derived in this app',
      why: 'A resolver rewritten in a client is the one that disagrees in silence.',
      line: 120,
      shaped: true,
    },
  ],
}

function bounds(over: Record<string, unknown> = {}): NonGoalsPayload {
  const parsed = readNonGoalsPayload({ ...NON_GOALS, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function criteria(over: Record<string, unknown> = {}): CriteriaPayload {
  const parsed = readCriteriaPayload({ ...CRITERIA, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG26: what may not be proposed at all', () => {
  it('reads the leads the project declares', () => {
    const list = boundsFrom(bounds())

    expect(list.governed).toBe(true)
    expect(list.nonGoals.map((one) => one.lead)).toEqual([
      'No Markdown parsed in this app',
      'No write to a governed file',
      'No store of its own',
    ])
  })

  it('says which designs already answered a lead in writing', () => {
    // `non-goal.reaches` goes silent for a lead a section quotes, so a quoted lead has
    // been reasoned about and a bare one has not.
    const list = boundsFrom(bounds())

    expect(list.nonGoals[2]?.answeredBy).toEqual(['RG28'])
    expect(list.nonGoals[0]?.answeredBy).toEqual([])
  })

  it('carries no reason, because no read publishes one', () => {
    // A key that always held the empty string would read as a missing reason rather than
    // an unpublished one.
    expect(Object.keys(boundsFrom(bounds()).nonGoals[0]!)).toEqual(['lead', 'answeredBy'])
  })

  it('says so when the answer was a sample', () => {
    expect(boundsFrom(bounds({ non_goals_elided: 4 })).elided).toBe(4)
  })
})

describe('RG26: what would finish a block', () => {
  it('groups the criteria by what they are about, in file order', () => {
    const list = finishingFrom(criteria())

    expect(list.groups.map((group) => group.about)).toEqual(['A', 'D'])
    expect(list.groups[1]?.criteria).toHaveLength(2)
    expect(list.groups[1]?.criteria[0]?.line).toBe(117)
  })

  it('carries each criterion whole, its reason and its address included', () => {
    const found = criteriaAbout(finishingFrom(criteria()), 'D')

    expect(found[1]?.lead).toBe('Readiness is never derived in this app')
    expect(found[1]?.why).toContain('disagrees in silence')
    expect(found[1]?.line).toBe(120)
    expect(found[1]?.shaped).toBe(true)
  })

  it('answers nothing for an address that carries no criteria', () => {
    // A block with none has no group, rather than an empty one nobody asked for.
    expect(criteriaAbout(finishingFrom(criteria()), 'B')).toEqual([])
  })

  it('draws a group the block list never declared', () => {
    // A task carrying its own criteria is `about` a task id, which is not in `blocks`.
    const list = finishingFrom(
      criteria({
        criteria: [
          { about: 'RG26', lead: 'Both lists are one read each', why: '', line: 30, shaped: true },
        ],
      }),
    )

    expect(list.groups.map((group) => group.about)).toEqual(['RG26'])
    expect(list.blocks).not.toContain('RG26')
  })
})

describe('RG26: three kinds of nothing, and the engine says which', () => {
  it('says nothing at all when there is something to show', () => {
    expect(whyNothing(finishingFrom(criteria()))).toBe('')
    expect(whyNothing(boundsFrom(bounds()))).toBe('')
  })

  it('names an ungoverned list rather than drawing it as empty', () => {
    // Reading is never refused, so an ungoverned list arrives empty and says so. A screen
    // that drew it silently would claim the project has no constraints.
    const list = boundsFrom(bounds({ governed: false, non_goals: [] }))

    expect(whyNothing(list)).toContain('docs/ROADMAP.md')
    expect(whyNothing(list)).toContain('governs')
  })

  it('carries the engine word for an address that was never asked', () => {
    const list = finishingFrom(criteria({ empty: 'unasked', criteria: [] }))

    expect(list.empty).toBe('unasked')
    expect(whyNothing(list)).toBe('unasked')
  })

  it('offers the door that opens a list nobody has started', () => {
    const list = finishingFrom(
      criteria({
        empty: 'unasked',
        criteria: [],
        doors: [
          {
            argv: ['criterion', 'add', '--block', 'Z', '--lead', '…', '--why', '…'],
            what: 'the address has no list, and this opens one',
            complete: false,
            writes: true,
          },
        ],
      }),
    )

    expect(list.doors[0]?.argv[0]).toBe('criterion')
    expect(list.doors[0]?.complete).toBe(false)
    expect(list.doors[0]?.writes).toBe(true)
  })

  it('falls back when the list is governed and empty with no word for it', () => {
    const list = finishingFrom(criteria({ empty: null, criteria: [] }))

    expect(whyNothing(list)).toBe('the list is declared and empty')
  })
})
