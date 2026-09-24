import {
  aboutNoInput,
  applyWrite,
  composeWrite,
  movedFrom,
  openMarkers,
  readStatusPayload,
  saidOfMove,
  type Moved,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * Moving a marker against a real engine, and only ever on a fixture. A live test that
 * moved a marker in this repository's own roadmap would be one that governs the file it
 * is testing.
 */

let fixture: Fixture
let markers: string[] = []
/**
 * Which declared marker takes a claim, found by writing each one and seeing which says so.
 *
 * Not named here. Which marker is the working one is `[markers] undesigned`'s neighbour in
 * the project's own config, and a test that wrote `🛠` would be asserting about this
 * repository's choice rather than about the verb.
 */
let working = ''
/** Any other declared marker, which is how a line is put back within reach. */
let off = ''

async function move(id: string, marker: string) {
  return applyWrite(
    engine,
    composeWrite(fixture.root, 'status', { id, marker }),
    readStatusPayload,
    { timeoutMs: CEILING },
  )
}

async function moved(id: string, marker: string): Promise<Moved> {
  const outcome = await move(id, marker)
  if (outcome.kind !== 'applied') {
    throw new Error(`status ${id} ${marker} was ${outcome.kind}`)
  }
  return movedFrom(outcome.value)
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 0, deferred: 0 })

  markers = openMarkers(await read(fixture.root, 'config', {}))

  // One at a time: these are writes to one file, and running them together would be two
  // callers on one governed file, which is the thing the claim registry exists about.
  for (const marker of markers) {
    if ((await moved('FX1', marker)).claim === 'claimed') working = marker
  }
  off = markers.find((marker) => marker !== working) ?? ''
  if (working !== '') await moved('FX1', off)
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG30: the markers offered are the ones the project declared', () => {
  it('reads the open set off the fixture own config', () => {
    // The fixture is `init`'s defaults, so this is roadkeep's own declared set and not
    // one written into this test.
    expect(markers.length).toBeGreaterThan(1)
    expect(markers.every((marker) => marker !== '')).toBe(true)
  })

  it('takes every marker it offers, which is what makes the list a list of doors', () => {
    // Proved by `beforeAll`, which wrote every one of them to find the working marker.
    expect(working).not.toBe('')
    expect(off).not.toBe('')
    expect(markers).toContain(working)
  })
})

describe('RG30: what moved with the marker', () => {
  it('moves the line and says where from and to', async () => {
    await moved('FX2', off)
    const one = await moved('FX2', working)

    expect(one.changed).toBe(true)
    expect(one.from).toBe(off)
    expect(one.to).toBe(working)
    expect(one.rendered).toContain('FX2')
    expect(one.wrote.some((file) => file.includes('ROADMAP.md'))).toBe(true)
  })

  it('takes a claim moving to the working marker, and gives it back moving off', async () => {
    await moved('FX3', off)
    expect(saidOfMove(await moved('FX3', working))).toContain('yours')

    const released = await moved('FX3', off)

    expect(released.claim).toBe('released')
    expect(saidOfMove(released)).toContain('given back')
  })

  it('refuses to re-take a line a live claim already holds, naming no input', async () => {
    // Nothing re-dates a live claim: the window is the expiry, not something a second call
    // can postpone. And the refusal names no field — a claim names nobody, so it may be
    // the caller's own, and there is no box to mark.
    await moved('FX3', off)
    expect((await moved('FX3', working)).claim).toBe('claimed')

    const again = await move('FX3', working)

    expect(again.kind).toBe('refused')
    if (again.kind !== 'refused') throw new Error('unreachable')
    expect(aboutNoInput(again.refusal)).toBe(true)
    expect(again.refusal.said).toContain('FX3')
  })

  it('reads a marker already set as an answer, not a failure', async () => {
    // A marker that takes no claim, so the answer is about the no-op and not about a
    // second call re-dating something.
    await moved('FX2', off)
    const again = await moved('FX2', off)

    expect(again.changed).toBe(false)
    expect(again.to).toBe(off)
    expect(saidOfMove(again)).toContain('already')
  })
})

describe('RG30: a marker this project does not declare', () => {
  it('is refused by the engine rather than filtered here', async () => {
    // The set is the project's, so the check is too. This app offers the declared ones and
    // never decides that an undeclared one is invalid.
    const outcome = await move('FX2', '🚀')

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.said).not.toBe('')
  })

  it('names no input to mark for a refusal that is not about one', async () => {
    const outcome = await move('FX9999', off)

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    // No such id is not a field's fault, so there is no box, and the sentence is what
    // there is to show.
    expect(aboutNoInput(outcome.refusal)).toBe(true)
    expect(outcome.refusal.said).toContain('FX9999')
  })
})
