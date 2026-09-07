import path from 'node:path'

import {
  accountOf,
  applyWrite,
  composeWrite,
  createClient,
  deferred,
  leftPointing,
  readDeferPayload,
  readListPayload,
  readPayload,
  readResumePayload,
  readRetirePayload,
  readShipPayload,
  resumed,
  retired,
  shipped,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The four departures against a real engine, on a fixture and never on this repository.
 * Every one of them is irreversible in the direction that matters, which is exactly why
 * the project they run against is a temporary directory.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function ids(role?: string): Promise<string[]> {
  const input = role === undefined ? {} : { role }
  const result = await client.call(fixture.root, 'list', input, { timeoutMs: CEILING })
  const parsed = readPayload(readListPayload, result.stdout, { verb: 'list', engineVersion: '' })
  if (!parsed.ok) throw new Error('list did not read')
  return parsed.value.tasks.map((task) => task.id)
}

beforeAll(async () => {
  // Six open lines, so each departure below has one of its own to act on.
  fixture = await buildFixture(engine, { open: 6, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG31: a ship writes three files in one transaction', () => {
  it('writes the ledger, clears the roadmap line and drops the section', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'ship', {
        id: 'FX1',
        why: 'The read now answers, and a test holds it.',
      }),
      readShipPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const departure = shipped(outcome.value)

    expect(departure.how).toBe('shipped')
    expect(departure.stillOpen).toBe(false)
    expect(departure.edits.map((edit) => edit.file)).toEqual([
      expect.stringContaining('CHANGELOG.md'),
      expect.stringContaining('ROADMAP.md'),
      expect.stringContaining('IMPROVEMENTS.md'),
    ])
    expect(accountOf(departure)).toContain('FX1 shipped')
    expect(await ids()).not.toContain('FX1')
    expect(await ids('changelog')).toContain('FX1')
  })

  it('leaves the line open where only half of it landed', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'ship', {
        id: 'FX2',
        why: 'The local half answers now.',
        part: 'the local half',
        remainder: 'The half that needs an account somebody has to buy.',
      }),
      readShipPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const departure = shipped(outcome.value)

    expect(departure.stillOpen).toBe(true)
    expect(await ids()).toContain('FX2')
    expect(await ids('changelog')).toContain('FX2')
  })
})

describe('RG31: a retire records a departure without a ship', () => {
  it('takes the line out and says what is left pointing at it', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'retire', {
        id: 'FX3',
        reason: 'The premise it rests on stopped being true.',
      }),
      readRetirePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const departure = retired(outcome.value)

    expect(departure.how).toBe('retired')
    expect(departure.rendered).toContain('abandoned')
    // Nothing depended on it here, so nothing is left pointing — the ordinary case, and
    // the one a screen must not draw as a warning.
    expect(leftPointing(departure)).toBe('')
    expect(await ids()).not.toContain('FX3')
  })

  it('records a replacement rather than an abandonment when one is named', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'retire', {
        id: 'FX4',
        supersededBy: 'FX5',
        reason: 'FX5 takes this over whole.',
      }),
      readRetirePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.supersededBy).toBe('FX5')
    expect(retired(outcome.value).rendered).not.toContain('abandoned')
  })
})

describe('RG31: a defer keeps every slot, and a resume brings them back', () => {
  it('moves the line to the store, carrying its section', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'defer', {
        id: 'FX5',
        reason: 'Waiting on a decision that is not this project.',
      }),
      readDeferPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const departure = deferred(outcome.value)

    expect(departure.how).toBe('deferred')
    // Set aside is not closed.
    expect(departure.stillOpen).toBe(true)
    // The section went with it rather than being dropped, which is what tells a defer
    // from a ship.
    expect(outcome.value.carried?.anchor).toContain('FX5')
    expect(await ids()).not.toContain('FX5')
    expect(await ids('deferred')).toContain('FX5')
  })

  it('brings it back with the reason it stood on, unwrapped', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'resume', { id: 'FX5' }),
      readResumePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const departure = resumed(outcome.value)

    expect(departure.how).toBe('resumed')
    // The one place a pause's own sentence is published apart from the design's why that
    // `defer` wrapped it around.
    expect(outcome.value.was).toBe('Waiting on a decision that is not this project.')
    expect(outcome.value.marker).not.toBe('')
    expect(await ids()).toContain('FX5')
    expect(await ids('deferred')).not.toContain('FX5')
  })
})

describe('RG31: a departure the engine refuses', () => {
  it('refuses a ship whose outcome sentence is missing', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'ship', { id: 'FX6' }),
      readShipPayload,
      { timeoutMs: CEILING },
    )

    // The roadmap's sentence states a problem and is not inherited, so an outcome is
    // required rather than defaulted — which is `No field this app composes` enforced at
    // the far end.
    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.said).not.toBe('')
    expect(await ids()).toContain('FX6')
  })

  it('refuses to resume a line that was never set aside', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'resume', { id: 'FX6' }),
      readResumePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.said).toContain('FX6')
  })
})
