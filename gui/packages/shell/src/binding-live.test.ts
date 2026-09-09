import {
  boundsFrom,
  criteriaAbout,
  finishingFrom,
  whyNothing,
  type Bounds,
  type Finishing,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { liveEngine as engine, read, REPO } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * The two binding lists against real projects. This repository governs both and has
 * quoted leads; the fixture governs one non-goal and one criterion and nothing else,
 * which is what makes an unasked address reachable.
 */

let fixture: Fixture

async function boundsOf(root: string): Promise<Bounds> {
  return boundsFrom(await read(root, 'nonGoalList', {}))
}

async function finishingOf(
  root: string,
  input: { block?: string; task?: string } = {},
): Promise<Finishing> {
  return finishingFrom(await read(root, 'criterionList', input))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG26: what may not be proposed at all', () => {
  it('reads this project own list, with the file it came from', async () => {
    const bounds = await boundsOf(REPO)

    expect(bounds.governed).toBe(true)
    expect(bounds.file).toContain('ROADMAP.md')
    expect(bounds.nonGoals.length).toBeGreaterThan(5)
    expect(bounds.nonGoals.every((one) => one.lead !== '')).toBe(true)
    expect(whyNothing(bounds)).toBe('')
  })

  it('names the designs that already answered a lead in writing', async () => {
    const bounds = await boundsOf(REPO)
    const answered = bounds.nonGoals.filter((one) => one.answeredBy.length > 0)

    // This backlog has open designs quoting a lead, which is what silences
    // `non-goal.reaches` for them.
    expect(answered.length).toBeGreaterThan(0)
    expect(answered[0]?.answeredBy.every((id) => /^RG\d+$/.test(id))).toBe(true)
  })

  it('reads a project that governs one, without calling that ungoverned', async () => {
    const bounds = await boundsOf(fixture.root)

    expect(bounds.governed).toBe(true)
    expect(bounds.nonGoals).toHaveLength(1)
  })
})

describe('RG26: what would finish a block', () => {
  it('groups every block criteria under the block they are about', async () => {
    const finishing = await finishingOf(REPO)

    expect(finishing.groups.length).toBeGreaterThan(1)
    expect(finishing.blocks.length).toBeGreaterThan(1)
    for (const group of finishing.groups) {
      expect(group.criteria.length).toBeGreaterThan(0)
      expect(group.criteria.every((one) => one.about === group.about)).toBe(true)
      expect(group.criteria.every((one) => one.lead !== '' && one.why !== '')).toBe(true)
    }
  })

  it('narrows to one block and answers only about that one', async () => {
    const finishing = await finishingOf(REPO, { block: 'A' })

    expect(finishing.groups.map((group) => group.about)).toEqual(['A'])
    expect(criteriaAbout(finishing, 'A').length).toBeGreaterThan(0)
    expect(criteriaAbout(finishing, 'B')).toEqual([])
  })
})

describe('RG26: three kinds of nothing, and the engine says which', () => {
  it('names an address nobody has opened a list for', async () => {
    // A task with no criteria of its own. Not an error and not ungoverned — unasked, and
    // the engine is what says so.
    const finishing = await finishingOf(fixture.root, { task: 'FX1' })

    expect(finishing.groups).toEqual([])
    expect(finishing.empty).not.toBe('')
    expect(whyNothing(finishing)).toBe(finishing.empty)
  })

  it('offers the door that opens it, as argv this app never composed', async () => {
    const finishing = await finishingOf(fixture.root, { task: 'FX1' })

    expect(finishing.doors.length).toBeGreaterThan(0)
    expect(finishing.doors[0]?.argv).toContain('criterion')
    expect(finishing.doors[0]?.writes).toBe(true)
    // Incomplete: the lead and the reason are the person's, and the app fills in neither.
    expect(finishing.doors[0]?.complete).toBe(false)
  })
})
