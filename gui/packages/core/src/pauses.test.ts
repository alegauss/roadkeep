import { describe, expect, it } from 'vitest'

import { filingOf, pauseOf, storeFrom, whereFiled } from './pauses'
import { readListPayload, type ListPayload } from './payloads'

/** Captured from a real `list --stale --json` against a fixture with one pause. */
const STORE = {
  file: 'docs/DEFERRED.md',
  total: 1,
  uncounted: [],
  standing: null,
  startable: { open: 0, startable: 0, waiting: 0, absent: [] },
  over: null,
  tasks: [
    {
      id: 'FX1',
      status: '⏸',
      block: 'A',
      symptom: 'nothing answers question 1 yet',
      why: 'set aside (Waiting on a decision that is not this project.): The 1th read has no call path, so the screen has nothing to draw.',
      deps: [],
      ref: 'FX1',
      line: 5,
      length: 192,
    },
  ],
}

function listing(over: Record<string, unknown> = {}): ListPayload {
  const parsed = readListPayload({ ...STORE, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function withIds(file: string, ids: readonly string[]): ListPayload {
  return listing({
    file,
    total: ids.length,
    tasks: ids.map((id, index) => ({
      id,
      status: '📋',
      block: 'A',
      symptom: 'something',
      why: 'a reason.',
      deps: [],
      ref: id,
      line: index + 1,
      length: 100,
    })),
  })
}

describe('RG28: the deferred store, read like any other listing', () => {
  it('reads the paused lines with the marker the project declares', () => {
    const store = storeFrom(listing())

    expect(store.file).toContain('DEFERRED.md')
    expect(store.total).toBe(1)
    expect(store.pauses[0]?.id).toBe('FX1')
    // Carried, not compared to a literal: the pause marker is per project.
    expect(store.pauses[0]?.marker).toBe('⏸')
  })

  it('keeps the store own sentence whole, wrapper and all', () => {
    // `defer` writes the reason around the design's own why. Splitting it back out is a
    // rule about a format that is roadkeep's.
    const store = storeFrom(listing())

    expect(store.pauses[0]?.why).toBe(STORE.tasks[0]!.why)
    expect(store.pauses[0]?.why).toContain('set aside (')
    expect(store.pauses[0]?.symptom).toBe('nothing answers question 1 yet')
  })

  it('keeps the file order, because no age is carried to sort by', () => {
    // `--stale` orders by how long each pause has stood and prints that for a terminal.
    // A `--json` caller gets the store and no ordering, and none is invented here.
    const store = storeFrom(withIds('docs/DEFERRED.md', ['FX9', 'FX2', 'FX5']))

    expect(store.pauses.map((one) => one.id)).toEqual(['FX9', 'FX2', 'FX5'])
  })

  it('says so when a marker-bearing line in the store was refused', () => {
    const store = storeFrom(
      listing({ uncounted: [{ line: 9, block: 'A', reason: 'no symptom', raw: '- ⏸ **FX4**' }] }),
    )

    expect(store.complete).toBe(false)
  })

  it('finds one pause by id, and nothing for an id it does not hold', () => {
    const store = storeFrom(listing())

    expect(pauseOf(store, 'FX1')?.block).toBe('A')
    expect(pauseOf(store, 'FX7')).toBeNull()
  })
})

describe('RG28: a paused line told from one nothing ever filed', () => {
  const roadmap = withIds('docs/ROADMAP.md', ['FX3', 'FX4'])
  const ledger = withIds('docs/CHANGELOG.md', ['FX2'])
  const store = listing()
  const filings = { roadmap, ledger, store }

  it('answers the third state the store made visible', () => {
    expect(filingOf('FX1', filings)).toBe('paused')
  })

  it('still tells open from shipped from nowhere', () => {
    expect(filingOf('FX3', filings)).toBe('open')
    expect(filingOf('FX2', filings)).toBe('shipped')
    expect(filingOf('FX99', filings)).toBe('unfiled')
  })

  it('reads open first, because a ledger entry can cite a line still open', () => {
    // A ship of one half writes an entry while the line stays open. Open is what a person
    // means when both files carry the id.
    const both = { roadmap, ledger: withIds('docs/CHANGELOG.md', ['FX3']), store }

    expect(filingOf('FX3', both)).toBe('open')
  })

  it('says unfiled where a listing was never read, rather than guessing', () => {
    expect(filingOf('FX1', {})).toBe('unfiled')
    expect(filingOf('FX1', { store })).toBe('paused')
  })
})

describe('RG28: what to say about an id that is not open', () => {
  it('names the store and the sentence it was set aside on', () => {
    const store = storeFrom(listing())

    expect(whereFiled('paused', store, 'FX1')).toContain('docs/DEFERRED.md')
    expect(whereFiled('paused', store, 'FX1')).toContain('Waiting on a decision')
  })

  it('names the store even when the pause itself is not to hand', () => {
    expect(whereFiled('paused', storeFrom(listing()), 'FX7')).toBe('set aside in docs/DEFERRED.md')
    expect(whereFiled('paused')).toBe('set aside in the deferred store')
  })

  it('is shortest and clearest for an id nothing carries', () => {
    expect(whereFiled('unfiled')).toBe('nothing in this project carries that id')
    expect(whereFiled('open')).toBe('open in the roadmap')
    expect(whereFiled('shipped')).toBe('shipped, and in the ledger')
  })
})
