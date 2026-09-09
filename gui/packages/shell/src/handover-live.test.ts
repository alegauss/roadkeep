import {
  aboutNoInput,
  claimingBrief,
  handoverOf,
  heldBy,
  mayHandOver,
  saidOfHandover,
  type Handover,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveClient as client, liveEngine as engine } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * Taking a line against a real engine, on a fixture. `--claim` writes, so it runs nowhere
 * else — and the interesting assertions are about the second call, which is the one that
 * proves nothing re-dates a live claim.
 */

let fixture: Fixture

/** A brief, claiming or not, read as either the payload or the refusal it answered with. */
async function briefing(input: Parameters<typeof claimingBrief>[0] | undefined, claim: boolean) {
  const result = await client.call(
    fixture.root,
    'brief',
    claim ? claimingBrief(input) : input === undefined ? {} : { id: input },
    { timeoutMs: CEILING },
  )
  if (!result.ok) throw new Error('brief did not read at all')
  return result.value
}

async function taking(id?: string): Promise<Handover> {
  const answer = await briefing(id, true)
  if (answer.kind !== 'payload') throw new Error('the claim was refused')
  return handoverOf(answer.value)
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG41: reading and taking are one call', () => {
  it('answers with the whole brief and moves the marker in the same transaction', async () => {
    const before = await briefing('FX1', false)
    if (before.kind !== 'payload') throw new Error('unreachable')

    const handover = await taking('FX1')

    expect(handover.taken).toBe(true)
    expect(handover.from).toBe(before.value.status)
    expect(handover.to).not.toBe(handover.from)
    expect(saidOfHandover(handover)).toContain('FX1 taken')

    // And it is a whole brief: the claim did not cost the read it came with.
    const after = await briefing('FX1', false)
    if (after.kind !== 'payload') throw new Error('unreachable')
    expect(after.value.status).toBe(handover.to)
    expect(after.value.symptom).toBe(before.value.symptom)
  })

  it('picks and takes in one call when no id is named', async () => {
    // The tier that chose the line and the transaction that took it are the same call, so
    // nothing can read a line and lose it before claiming.
    const handover = await taking()

    expect(handover.id).toMatch(/^FX\d+$/)
    expect(handover.taken).toBe(true)
  })
})

describe('RG41: a claim is an expiry, and nothing re-dates a live one', () => {
  it('refuses a second claim on a line already held', async () => {
    await taking('FX3')
    const again = await briefing('FX3', true)

    // The engine keeps the window an expiry rather than something a caller can extend.
    // This app does not retry it.
    expect(again.kind).toBe('refused')
    if (again.kind !== 'refused') throw new Error('unreachable')
    expect(again.refusal.said).toContain('FX3')
    // No field to mark: the claim names nobody, so it may be the caller's own.
    expect(aboutNoInput(again.refusal)).toBe(true)
  })

  it('still reads the line without the flag, which is what the refusal says to do', async () => {
    const read = await briefing('FX3', false)

    expect(read.kind).toBe('payload')
    if (read.kind !== 'payload') throw new Error('unreachable')
    // A read carries no claim of its own: `claimed` is null where nothing was taken.
    expect(read.value.claimed).toBeNull()
    expect(handoverOf(read.value).taken).toBe(false)
  })
})

describe('RG41: a held line is named before a second session is offered it', () => {
  it('offers a line nobody is on', async () => {
    const read = await briefing('FX2', false)
    if (read.kind !== 'payload') throw new Error('unreachable')
    const handover = handoverOf(read.value)

    expect(handover.held).toEqual([])
    expect(mayHandOver(handover)).toBe(true)
    expect(heldBy(handover)).toBe('')
  })

  it('reads a line this session took as still offerable to itself', async () => {
    // The marker moved and `held` stayed empty, which is RG74's whole point: a claim is
    // dated on a window and a marker is not, so the two answer different questions.
    const read = await briefing('FX1', false)
    if (read.kind !== 'payload') throw new Error('unreachable')

    expect(read.value.held).toEqual([])
    expect(mayHandOver(handoverOf(read.value))).toBe(true)
  })
})
