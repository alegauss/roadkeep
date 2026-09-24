import {
  backlogFrom,
  insteadOf,
  listedTasks,
  narrowingOfList,
  narrowedBy,
  storeFrom,
  type ListPayload,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * RG67: the answer shape no repository here produces.
 *
 * A project declaring `[reads] list` gets a listing past that bound answered with its
 * blocks and their counts and the lines withdrawn — `tasks: null`, `over` carrying the
 * ceiling and a narrower call. Nothing in this app had ever seen one, so the shape could
 * not be written; a shape invented from the sentence describing it is the second
 * declaration of roadkeep's format the non-goals refuse.
 *
 * So two fixtures declare a bound and this reads what the engine actually prints. Two
 * because the interesting states sit on either side of the same number: at 1200 the whole
 * file is over and a single block fits, so a narrowing is offered; at 400 nothing fits and
 * the honest answer is that there is no smaller call to make. A shape written from one of
 * them alone is a shape that fails on the other.
 */

/** Measured: this fixture's whole listing is ~1440 characters and each block's is ~970. */
const ROOMY = 1200
const TIGHT = 400

let roomy: Fixture
let tight: Fixture

beforeAll(async () => {
  const shape = { open: 4, shipped: 0, deferred: 0 }
  roomy = await buildFixture(engine, { ...shape, listRead: ROOMY })
  tight = await buildFixture(engine, { ...shape, listRead: TIGHT })
}, 180000)

afterAll(() => {
  roomy.dispose()
  tight.dispose()
})

/** One listing, read with the shape the verb declares. A bound is an answer, not a refusal. */
async function listing(root: string, input: Record<string, unknown> = {}): Promise<ListPayload> {
  return read(root, 'list', input)
}

describe('RG67: a listing past the bound the project declares', () => {
  it('is read rather than refused, which is what a wrong shape did instead', async () => {
    // The whole symptom: the reader demanded a `tasks` array, so this answer came back as
    // "this app is behind the engine" for a project that is simply large and has said so.
    const payload = await listing(roomy.root)

    expect(payload.tasks).toBeNull()
    expect(payload.over).not.toBeNull()
  })

  it('carries the ceiling it went past and what it would have cost', async () => {
    const payload = await listing(roomy.root)

    expect(payload.over?.limit).toBe(ROOMY)
    expect(payload.over?.characters).toBeGreaterThan(ROOMY)
  })

  it('answers with the blocks and their counts, which came instead of the lines', async () => {
    const payload = await listing(roomy.root)

    // The counts are the engine's own, and they are the only number there is once the
    // lines are withheld. The fixture alternates blocks, so four lines are two and two.
    const counted = Object.fromEntries(
      (payload.over?.blocks ?? []).map((block) => [block.label, block.counted]),
    )
    expect(counted).toEqual({ A: 2, B: 2 })
    expect(payload.total).toBe(4)
    expect(payload.over?.blocks.every((block) => block.name !== '')).toBe(true)
  })

  it('offers the narrower call, already split, as the engine composed it', async () => {
    const payload = await listing(roomy.root)

    expect(payload.over?.narrows).not.toBe('')
    const [door] = insteadOf(payload)
    expect(door?.argv).toEqual(['list', '--block', payload.over?.narrows])
    expect(door?.writes).toBe(false)
  })

  it('names no narrowing where nothing smaller would fit either', async () => {
    // Every block of the tight fixture is over its bound as well. Saying so is an answer;
    // offering a door that answers the same way would not be.
    const payload = await listing(tight.root, { block: 'A' })

    expect(payload.tasks).toBeNull()
    expect(payload.over?.scoped).toBe(true)
    expect(payload.over?.narrows).toBe('')
    expect(insteadOf(payload)).toEqual([])
  })

  it('reads as an ordinary listing for a call that fits under the bound', async () => {
    const payload = await listing(roomy.root, { block: 'A' })

    // The other reading, from the same project and the same shape: the lines arrive.
    expect(listedTasks(payload)).toHaveLength(2)
    expect(payload.over).toBeNull()
    expect(narrowingOfList(payload).complete).toBe(true)
  })
})

describe('RG67: what a screen is told about it', () => {
  it('reports the answer as narrower than the file rather than as complete', async () => {
    const narrowing = narrowingOfList(await listing(roomy.root))

    expect(narrowing.complete).toBe(false)
    expect(narrowing.reasons.join(' ')).toContain(String(ROOMY))
  })

  it('opens into the blocks the file runs, with no lines under them', async () => {
    const backlog = backlogFrom(await listing(roomy.root))

    // Not an empty backlog: the headings are there, the counts are there, and `complete`
    // says the lines are not. A screen drawing this as a project with nothing in it is
    // exactly the silence a bounded read is supposed to prevent.
    expect(backlog.blocks.map((block) => block.block)).toEqual(['A', 'B'])
    expect(backlog.blocks.map((block) => block.counted)).toEqual([2, 2])
    expect(backlog.blocks.every((block) => block.lines.length === 0)).toBe(true)
    expect(backlog.complete).toBe(false)
    expect(backlog.over?.limit).toBe(ROOMY)
  })

  it('answers the bound and the call to make instead, as fills (RG172)', async () => {
    const payload = await listing(roomy.root)
    const narrowed = narrowedBy(backlogFrom(payload))

    expect(narrowed?.code).toBe('over-narrows')
    expect(narrowed?.fields['limit']).toBe(String(ROOMY))
    expect(narrowed?.fields['narrows']).toBe(payload.over?.narrows ?? '')
  })

  it('answers the other code where there is nothing smaller to ask for', async () => {
    const narrowed = narrowedBy(backlogFrom(await listing(tight.root, { block: 'A' })))

    expect(narrowed?.code).toBe('over-whole')
  })

  it('keeps the ordinary backlog reading for a listing that fits', async () => {
    const backlog = backlogFrom(await listing(roomy.root, { block: 'A' }))

    expect(backlog.complete).toBe(true)
    expect(backlog.over).toBeNull()
    expect(narrowedBy(backlog)).toBeNull()
    expect(backlog.blocks.map((block) => block.counted)).toEqual([2])
  })

  it('does not read a listing whose lines were withheld as an empty one', async () => {
    // The same trap one file over. `storeFrom` reads a listing exactly as the backlog
    // does, and zero entries against a total of four is a silence `complete` breaks.
    const payload = await listing(roomy.root)
    const store = storeFrom(payload)

    expect(store.pauses).toEqual([])
    expect(store.total).toBe(4)
    expect(store.complete).toBe(false)
  })
})
