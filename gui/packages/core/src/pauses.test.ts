import { describe, expect, it } from 'vitest'

import { filingOf, pauseOf, storeFrom, whereaboutsOf, whereFiled } from './pauses'
import { readListPayload, type ListPayload } from './payloads'
import type { Refusal } from './refusals'

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

/** The bound a listing went past, as the engine answers it: counts and no lines. */
const OVER = { characters: 9000, limit: 4000, blocks: [], scoped: false, narrows: '', doors: [] }

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

  it('says unknown where a listing was never read, rather than claiming nowhere', () => {
    // RG100: an absence is only evidence where somebody looked. Being *found* still
    // settles it whatever the other two listings did.
    expect(filingOf('FX1', {})).toBe('unknown')
    expect(filingOf('FX1', { store })).toBe('paused')
    expect(filingOf('FX99', { roadmap, ledger })).toBe('unknown')
  })

  it('says unknown where a listing was read past its bound', () => {
    // The case RG67 made possible: counts and no lines, so nothing is found in it and
    // nothing may be concluded from that.
    const withheld = { roadmap, ledger, store: listing({ tasks: null, over: OVER }) }

    expect(filingOf('FX99', withheld)).toBe('unknown')
  })

  it('says unknown where a line in the file was one the grammar refused', () => {
    // The older and quieter half of the same question: a refused line is in `uncounted`
    // and not in `tasks`, so an id sitting in one was never in the list being searched.
    const refused = {
      roadmap,
      ledger,
      store: listing({ uncounted: [{ file: 'docs/DEFERRED.md', line: 9, text: '- ?? FX8' }] }),
    }

    expect(filingOf('FX99', refused)).toBe('unknown')
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

/** Captured from a real `show FX1 --json` on a line that had been set aside. */
const REFUSED: Refusal = {
  refused: [],
  beside: '',
  about: '',
  said:
    'roadkeep: no task FX1 in docs/ROADMAP.md or docs/CHANGELOG.md: FX1 is paused in ' +
    'docs/DEFERRED.md:5 — `roadkeep list --role deferred` prints it with the reason it ' +
    'was set aside, and `roadkeep resume FX1` returns it to its block',
}

describe('RG80: the refusal that knows where the line went', () => {
  const roadmap = withIds('docs/ROADMAP.md', ['FX3'])
  const ledger = withIds('docs/CHANGELOG.md', ['FX2'])
  const filings = { roadmap, ledger, store: listing() }

  it('has nothing typed to read on the refusal itself, which is the symptom', () => {
    // Not a claim about this app: it is what the engine answers, and the reason the three
    // listings are asked at all.
    expect(REFUSED.refused).toEqual([])
    expect(REFUSED.beside).toBe('')
    expect(REFUSED.about).toBe('')
  })

  it('answers a paused id with the store entry and the way back', () => {
    const found = whereaboutsOf('/w', 'FX1', REFUSED, filings)

    expect(found.filing).toBe('paused')
    expect(found.pause?.line).toBe(5)
    expect(found.pause?.why).toContain('Waiting on a decision')
    expect(found.sentence).toContain('docs/DEFERRED.md')
    expect(found.back?.argv).toEqual(['-C', '/w', 'resume', 'FX1', '--json'])
  })

  it('offers no way back for an id nothing carries, and says that instead', () => {
    // The two states this exists to separate. Both refuse; only one has anywhere to go.
    const found = whereaboutsOf('/w', 'FX99', REFUSED, filings)

    expect(found.filing).toBe('unfiled')
    expect(found.pause).toBeNull()
    expect(found.back).toBeNull()
    expect(found.sentence).toBe('nothing in this project carries that id')
  })

  it('reads a withheld store as unknown rather than as never filed', () => {
    // RG100: a listing past `[reads] list` carries counts and no lines, so nothing is found
    // in it — and the id may well still be paused in the file. What is refused is the
    // sentence claiming nothing here ever carried it.
    const withheld = whereaboutsOf('/w', 'FX1', REFUSED, { store: listing({ tasks: null }) })

    expect(withheld.filing).toBe('unknown')
    expect(withheld.sentence).toContain('did not see every line')
    expect(withheld.sentence).not.toContain('nothing in this project')
    expect(withheld.pause).toBeNull()
    expect(withheld.back).toBeNull()
  })

  it('carries the engine sentence whole, because nothing above may say more', () => {
    // The one case with no listings to ask: the sentence is all there is, and it is passed
    // through rather than picked apart.
    const nothing = whereaboutsOf('/w', 'FX1', REFUSED, {})

    expect(nothing.filing).toBe('unknown')
    expect(nothing.said).toBe(REFUSED.said)
    expect(nothing.said).toContain('roadkeep resume FX1')
  })
})
