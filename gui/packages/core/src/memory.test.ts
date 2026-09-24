import { describe, expect, it } from 'vitest'

import { howListed, ledgerFrom, reversedFrom, undoneBy } from './memory'
import {
  readDeliveredPayload,
  readReversalsPayload,
  type DeliveredPayload,
  type ReversalsPayload,
} from './payloads'

/** Captured from a real `delivered D --json`. */
const DELIVERED = {
  file: 'docs/CHANGELOG.md',
  block: 'D',
  standing: {
    block: 'D',
    state: 'live',
    sentence: 'Block D has 5 open',
    open: 5,
    recorded: 6,
    paused: 0,
  },
  recorded: 6,
  near: null,
  delivered: [
    {
      id: 'RG21',
      marker: '✅',
      symptom: 'opening a project shows counts and no lines',
      line: 32,
      undone_by: null,
    },
    {
      id: 'RG23',
      marker: '✅',
      symptom: 'a task has no detail',
      line: 34,
      undone_by: null,
    },
  ],
}

/** Captured from a real `reversals --json` on a project that has none. */
const REVERSALS = { root: 'D:/Git/alegauss/roadkeep-gui', asked: null, reversed: [] }

function delivered(over: Record<string, unknown> = {}): DeliveredPayload {
  const parsed = readDeliveredPayload({ ...DELIVERED, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function reversals(over: Record<string, unknown> = {}): ReversalsPayload {
  const parsed = readReversalsPayload({ ...REVERSALS, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG27: what a block already delivered', () => {
  it('reads the ledger entries with the standing of the block they sit under', () => {
    const ledger = ledgerFrom(delivered())

    expect(ledger.file).toContain('CHANGELOG.md')
    expect(ledger.block).toBe('D')
    expect(ledger.standing?.sentence).toBe('Block D has 5 open')
    expect(ledger.delivered.map((one) => one.id)).toEqual(['RG21', 'RG23'])
  })

  it('says a delivery the ledger itself undid, because that still reads as shipped', () => {
    // A revert is filed as a delivery, so an entry can say shipped and mean the work did
    // not hold.
    const ledger = ledgerFrom(
      delivered({
        delivered: [
          { id: 'RG21', marker: '✅', symptom: 'held', line: 32, undone_by: null },
          { id: 'RG30', marker: '✅', symptom: 'did not hold', line: 40, undone_by: 'RG55' },
        ],
      }),
    )

    expect(ledger.delivered[0]?.undone).toBe(false)
    expect(ledger.delivered[1]?.undone).toBe(true)
    expect(ledger.delivered[1]?.undoneBy).toBe('RG55')
  })

  it('reads the whole block as the whole block', () => {
    const ledger = ledgerFrom(delivered())

    expect(ledger.ranked).toBe(false)
    expect(ledger.near).toBe('')
    expect(howListed(ledger)).toBe('6 delivered under D')
  })
})

describe('RG27: the read before an add, which ranks and never scores', () => {
  it('knows a ranked answer is a sample and says how it came about', () => {
    // Drawing the nearest few as the block's deliveries answers a duplicate question with
    // a set the question itself chose.
    const ledger = ledgerFrom(
      delivered({
        near: 'the ledger is unreachable from this app',
        delivered: [
          { id: 'RG21', marker: '✅', symptom: 'one', line: 32, undone_by: null, rank: 1 },
          { id: 'RG23', marker: '✅', symptom: 'two', line: 34, undone_by: null, rank: 2 },
        ],
      }),
    )

    expect(ledger.ranked).toBe(true)
    expect(ledger.near).toBe('the ledger is unreachable from this app')
    expect(howListed(ledger)).toBe('2 nearest of 6 delivered under D — an order, not a verdict')
  })

  it('carries rank as a position and publishes nothing that could become a threshold', () => {
    // roadkeep measured that an absolute number separates nothing and refused to publish
    // one. A score invented here is exactly the threshold that cannot exist.
    const ledger = ledgerFrom(
      delivered({
        near: 'something',
        delivered: [{ id: 'RG21', marker: '✅', symptom: 'one', line: 32, rank: 1 }],
      }),
    )
    const entry = ledger.delivered[0]!

    expect(entry.rank).toBe(1)
    expect(Object.keys(entry).some((key) => /score|match|percent|likel/i.test(key))).toBe(false)
  })

  it('leaves rank at zero when nothing was asked to rank against', () => {
    expect(ledgerFrom(delivered()).delivered[0]?.rank).toBe(0)
  })
})

describe('RG27: what was already decided and undone', () => {
  it('reads a ledger with no reversals as the ordinary answer it is', () => {
    const reversed = reversedFrom(reversals())

    expect(reversed.reversals).toEqual([])
    expect(reversed.narrowed).toBe(false)
    expect(reversed.asked).toBe('')
  })

  it('names what undid an id, with the argument the superseding entry made', () => {
    const reversed = reversedFrom(
      reversals({
        reversed: [
          {
            undone: 'RG30',
            by: 'RG55',
            line: 40,
            why: 'The cache it added answered stale on every second read.',
          },
        ],
      }),
    )

    expect(undoneBy(reversed, 'RG30')?.by).toBe('RG55')
    expect(undoneBy(reversed, 'RG30')?.why).toContain('stale')
    expect(undoneBy(reversed, 'RG21')).toBeNull()
  })

  it('says a listing of one was narrowed, so it does not read as the whole ledger', () => {
    const reversed = reversedFrom(
      reversals({
        asked: 'RG30',
        reversed: [{ undone: 'RG30', by: 'RG55', line: 40, why: 'It did not hold.' }],
      }),
    )

    expect(reversed.narrowed).toBe(true)
    expect(reversed.asked).toBe('RG30')
  })
})
