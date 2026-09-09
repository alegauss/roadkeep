import { howListed, ledgerFrom, reversedFrom, undoneBy, type Ledger, type Reversed } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { read, REPO } from './live'

/**
 * The ledger and the decisions file, read against this repository. Its changelog has real
 * deliveries under every live block and no reversals, which is the ordinary shape and the
 * one a reader most needs drawn correctly.
 */

async function ledgerOf(block: string, near?: string): Promise<Ledger> {
  return ledgerFrom(await read(REPO, 'delivered', near === undefined ? { block } : { block, near }))
}

async function reversedOf(id?: string): Promise<Reversed> {
  return reversedFrom(await read(REPO, 'reversals', id === undefined ? {} : { id }))
}

describe('RG27: what a block already delivered', () => {
  it('reads the ledger a block at a time, with the block standing beside it', async () => {
    // Block D is where this task lives, so it has entries whatever else moves.
    const ledger = await ledgerOf('D')

    expect(ledger.file).toContain('CHANGELOG.md')
    expect(ledger.block).toBe('D')
    expect(ledger.recorded).toBeGreaterThan(0)
    expect(ledger.delivered.length).toBeGreaterThan(0)
    expect(ledger.standing?.sentence).not.toBe('')
  })

  it('carries each entry claim, which is what a duplicate collides with', async () => {
    const ledger = await ledgerOf('D')

    expect(ledger.delivered.every((one) => one.symptom !== '')).toBe(true)
    expect(ledger.delivered.every((one) => one.line > 0)).toBe(true)
    expect(ledger.delivered.every((one) => /^RG\d+$/.test(one.id))).toBe(true)
  })

  it('reads a live backlog as having nothing undone, which is the ordinary answer', async () => {
    const ledger = await ledgerOf('D')

    expect(ledger.delivered.every((one) => !one.undone)).toBe(true)
  })
})

describe('RG27: the read before an add', () => {
  it('bounds the same read by the sentence about to be proposed', async () => {
    const whole = await ledgerOf('D')
    const near = await ledgerOf('D', 'the ledger is unreachable from this app')

    expect(near.ranked).toBe(true)
    expect(near.near).toBe('the ledger is unreachable from this app')
    expect(near.delivered.length).toBeLessThanOrEqual(whole.delivered.length)
    expect(near.recorded).toBe(whole.recorded)
  })

  it('says the ranked answer is an order and how many of how many it is', async () => {
    const near = await ledgerOf('D', 'a task has no detail worth opening')

    expect(howListed(near)).toContain('nearest of')
    expect(howListed(near)).toContain('not a verdict')
    expect(near.delivered[0]?.rank).toBeGreaterThan(0)
  })

  it('says the whole block is the whole block, with no ranking implied', async () => {
    const whole = await ledgerOf('D')

    expect(whole.ranked).toBe(false)
    expect(howListed(whole)).not.toContain('nearest')
  })
})

describe('RG27: what was already decided and undone', () => {
  it('reads the whole ledger for reversals, and this one has none', async () => {
    const reversed = await reversedOf()

    expect(reversed.root).not.toBe('')
    expect(reversed.narrowed).toBe(false)
    expect(reversed.reversals).toEqual([])
  })

  it('narrows to one id and says the answer was narrowed', async () => {
    // Without `asked`, a listing of one would read as a ledger with one reversal in it.
    const reversed = await reversedOf('RG21')

    expect(reversed.narrowed).toBe(true)
    expect(reversed.asked).toBe('RG21')
    expect(undoneBy(reversed, 'RG21')).toBeNull()
  })
})
