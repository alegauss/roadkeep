import {
  applyWrite,
  listedTasks,
  filingOf,
  pauseOf,
  readResumePayload,
  storeFrom,
  whereaboutsOf,
  type ListPayload,
  type Refusal,
  type Store,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveClient, liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * The deferred store against a project that has one. An empty store is exactly the answer
 * that cannot tell whether the reading works — so the fixture, which `defer` populates
 * with the real verb, is where this runs.
 *
 * The empty case gets a fixture of its own rather than this repository. It was this
 * repository until something here was actually set aside, at which point an assertion
 * about "a project that pauses nothing" was an assertion about a backlog that had moved.
 */

let fixture: Fixture
/** A project with the store scaffolded and nothing filed into it. */
let unpaused: Fixture

async function listing(root: string, input: Record<string, unknown> = {}): Promise<ListPayload> {
  return read(root, 'list', input)
}

async function storeOf(root: string): Promise<Store> {
  return storeFrom(await listing(root, { stale: true }))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 1 })
  unpaused = await buildFixture(engine, { open: 2, shipped: 1, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
  unpaused.dispose()
})

describe('RG28: the deferred store, read like any other listing', () => {
  it('names the store without being told a role, which is what --stale does', async () => {
    const store = await storeOf(fixture.root)

    expect(store.file).toContain('DEFERRED.md')
    expect(store.total).toBe(1)
    expect(store.complete).toBe(true)
  })

  it('carries the pause marker and the sentence the store spells', async () => {
    const store = await storeOf(fixture.root)
    const pause = store.pauses[0]!

    expect(pause.id).toMatch(/^FX\d+$/)
    expect(pause.marker).not.toBe('')
    expect(pause.symptom).not.toBe('')
    // The reason `defer` wrote, wrapped around the design's own why, and not split apart.
    expect(pause.why).toContain('Waiting on a decision that is not this project.')
    expect(pauseOf(store, pause.id)).toEqual(pause)
  })

  it('reads a project that pauses nothing as an empty store, not a missing one', async () => {
    // A fixture with the store scaffolded and nothing filed, rather than this repository.
    // It used to be this one, and RG62 being set aside made that assertion false — an
    // "empty" that any later `defer` here can fill is not the condition being asserted.
    const store = await storeOf(unpaused.root)

    expect(store.file).toContain('DEFERRED.md')
    expect(store.total).toBe(0)
    expect(store.pauses).toEqual([])
    expect(store.complete).toBe(true)
  })

  it('asks for the same store through the role, and gets the same lines', async () => {
    const viaStale = await storeOf(fixture.root)
    const viaRole = storeFrom(await listing(fixture.root, { role: 'deferred' }))

    expect(viaRole.pauses.map((one) => one.id)).toEqual(viaStale.pauses.map((one) => one.id))
  })
})

describe('RG28: a paused line told from one nothing ever filed', () => {
  it('answers all four states off the three real listings', async () => {
    const roadmap = await listing(fixture.root)
    const ledger = await listing(fixture.root, { role: 'changelog' })
    const store = await listing(fixture.root, { stale: true })
    const filings = { roadmap, ledger, store }

    const paused = listedTasks(store)[0]!.id
    const open = listedTasks(roadmap)[0]!.id
    const shipped = listedTasks(ledger)[0]!.id

    expect(filingOf(paused, filings)).toBe('paused')
    expect(filingOf(open, filings)).toBe('open')
    expect(filingOf(shipped, filings)).toBe('shipped')
    expect(filingOf('FX9999', filings)).toBe('unfiled')
  })

  it('carries where a paused id went, and what it was set aside for', async () => {
    const store = await storeOf(fixture.root)
    const pause = pauseOf(store, store.pauses[0]!.id)

    expect(store.file).toContain('DEFERRED.md')
    expect(pause?.why).toContain('Waiting on a decision')
    expect(pause?.reason).toContain('Waiting on a decision')
  })
})

describe('RG80: opening a task the engine will not open', () => {
  /** The refusal a real `brief` answers with, for an id that is not in the roadmap. */
  async function refusalOf(root: string, id: string): Promise<Refusal> {
    const answer = await liveClient.call(root, 'brief', { id }, { timeoutMs: CEILING })
    if (answer.kind === 'unreadable') throw new Error(answer.unreadable.message)
    if (answer.kind !== 'refused') throw new Error(`brief on ${id} answered a payload`)
    return answer.refusal
  }

  it('refuses with every typed field empty, which is what this task is about', async () => {
    const store = await storeOf(fixture.root)
    const refusal = await refusalOf(fixture.root, store.pauses[0]!.id)

    // Not a shape this app chose: the engine puts the whole answer in `said` here, so a
    // screen reading the typed fields has nothing at all.
    expect(refusal.refused).toEqual([])
    expect(refusal.beside).toBe('')
    expect(refusal.about).toBe('')
    expect(refusal.said).not.toBe('')
  })

  it('fills that refusal from the listings, without reading the sentence', async () => {
    const filings = {
      roadmap: await listing(fixture.root),
      ledger: await listing(fixture.root, { role: 'changelog' }),
      store: await listing(fixture.root, { stale: true }),
    }
    const paused = listedTasks(filings.store)[0]!.id
    const found = whereaboutsOf(
      fixture.root,
      paused,
      await refusalOf(fixture.root, paused),
      filings,
    )

    expect(found.filing).toBe('paused')
    expect(found.pause?.why).toContain('Waiting on a decision')
    expect(found.back?.argv).toEqual(['-C', fixture.root, 'resume', paused, '--json'])
    // The engine's sentence names the same store and the same verb, and is carried rather
    // than read: everything asserted above came from a listing.
    expect(found.said).toContain('resume')
  })

  it('tells that apart from an id this project never carried', async () => {
    const filings = {
      roadmap: await listing(fixture.root),
      ledger: await listing(fixture.root, { role: 'changelog' }),
      store: await listing(fixture.root, { stale: true }),
    }
    const found = whereaboutsOf(
      fixture.root,
      'FX9999',
      await refusalOf(fixture.root, 'FX9999'),
      filings,
    )

    expect(found.filing).toBe('unfiled')
    expect(found.back).toBeNull()
    expect(found.pause).toBeNull()
  })

  it('brings the line back with the argv it composed', async () => {
    // The door is only a door if it runs. This takes it, on a fixture of its own so the
    // store the tests above read is still there.
    const own = await buildFixture(engine, { open: 2, shipped: 0, deferred: 1 })
    try {
      const paused = storeFrom(await listing(own.root, { stale: true })).pauses[0]!.id
      const found = whereaboutsOf(own.root, paused, await refusalOf(own.root, paused), {
        store: await listing(own.root, { stale: true }),
      })

      const outcome = await applyWrite(engine, found.back!, readResumePayload, {
        timeoutMs: CEILING,
      })

      expect(outcome.kind).toBe('applied')
      expect(listedTasks(await listing(own.root)).map((task) => task.id)).toContain(paused)
    } finally {
      own.dispose()
    }
  })
})
