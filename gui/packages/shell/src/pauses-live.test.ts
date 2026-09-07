import path from 'node:path'

import {
  createClient,
  filingOf,
  pauseOf,
  readListPayload,
  readPayload,
  storeFrom,
  whereFiled,
  type ListPayload,
  type Store,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The deferred store against a project that has one. This repository pauses nothing, and
 * an empty store is exactly the answer that cannot tell whether the reading works — so
 * the fixture, which `defer` populates with the real verb, is where this runs.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function listing(root: string, input: Record<string, unknown> = {}): Promise<ListPayload> {
  const result = await client.call(root, 'list', input, { timeoutMs: CEILING })
  const parsed = readPayload(readListPayload, result.stdout, { verb: 'list', engineVersion: '' })
  if (!parsed.ok) {
    throw new Error(
      `list did not read: expected ${parsed.failure.expected} at ` +
        `${parsed.failure.path || '(the answer)'}, found ${parsed.failure.got}`,
    )
  }
  return parsed.value
}

async function storeOf(root: string): Promise<Store> {
  return storeFrom(await listing(root, { stale: true }))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 1 })
}, 180000)

afterAll(() => {
  fixture.dispose()
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
    const store = await storeOf(REPO)

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

    const paused = store.tasks[0]!.id
    const open = roadmap.tasks[0]!.id
    const shipped = ledger.tasks[0]!.id

    expect(filingOf(paused, filings)).toBe('paused')
    expect(filingOf(open, filings)).toBe('open')
    expect(filingOf(shipped, filings)).toBe('shipped')
    expect(filingOf('FX9999', filings)).toBe('unfiled')
  })

  it('says where a paused id went, with the sentence it was set aside on', async () => {
    const store = await storeOf(fixture.root)
    const said = whereFiled('paused', store, store.pauses[0]!.id)

    expect(said).toContain('DEFERRED.md')
    expect(said).toContain('Waiting on a decision')
  })
})
