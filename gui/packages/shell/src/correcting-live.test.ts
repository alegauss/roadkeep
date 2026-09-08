import path from 'node:path'

import {
  amended,
  applyWrite,
  composeWrite,
  correctionsOffered,
  createClient,
  readAmendPayload,
  readCommandsPayload,
  readListPayload,
  readPayload,
  readRenumberPayload,
  readRestatePayload,
  readShowPayload,
  renumbered,
  replacedBy,
  restated,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The three corrections against a real engine, on a fixture. Each keeps an id that
 * retiring would spend, so what these tests check is that the id, the deps, the marker and
 * the design are all still there afterwards.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function shown(id: string) {
  const result = await client.call(fixture.root, 'show', { id }, { timeoutMs: CEILING })
  const parsed = readPayload(readShowPayload, result.stdout, { verb: 'show', engineVersion: '' })
  if (!parsed.ok) throw new Error(`show ${id} did not read`)
  return parsed.value
}

async function ids(): Promise<string[]> {
  const result = await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })
  const parsed = readPayload(readListPayload, result.stdout, { verb: 'list', engineVersion: '' })
  if (!parsed.ok) throw new Error('list did not read')
  return parsed.value.tasks.map((task) => task.id)
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG35: the reason each exists, off the live build', () => {
  it('offers the three with the sentences this engine publishes', async () => {
    const result = await client.call(fixture.root, 'commands', {}, { timeoutMs: CEILING })
    const parsed = readPayload(readCommandsPayload, result.stdout, {
      verb: 'commands',
      engineVersion: '',
    })
    if (!parsed.ok) throw new Error('commands did not read')

    const offered = correctionsOffered(parsed.value)

    expect(offered.every((one) => one.callable)).toBe(true)
    expect(offered.every((one) => one.help !== '')).toBe(true)
    // The sentence that distinguishes them is the engine's, and it says so.
    expect(offered.find((one) => one.verb === 'restate')?.help).toContain('id')
  })
})

describe('RG35: a why corrected, keeping everything else', () => {
  it('changes the sentence and says what it replaced', async () => {
    const before = await shown('FX1')

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'amend', {
        id: 'FX1',
        why: 'A corrected sentence that ends in a stop.',
      }),
      readAmendPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const one = amended(outcome.value)

    expect(one.changed).toContain('why')
    expect(replacedBy(outcome.value)).toEqual([['why', before.why]])

    const after = await shown('FX1')
    expect(after.why).toBe('A corrected sentence that ends in a stop.')
    // Everything else stood: the id, the symptom, the marker and the design.
    expect(after.id).toBe(before.id)
    expect(after.symptom).toBe(before.symptom)
    expect(after.status).toBe(before.status)
    expect(after.section?.anchor).toBe(before.section?.anchor)
  })
})

describe('RG35: a symptom restated, keeping the design that was right', () => {
  it('replaces the claim and leaves the id, the marker and the section', async () => {
    const before = await shown('FX2')

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'restate', {
        id: 'FX2',
        symptom: 'the claim this line made turned out to be false',
      }),
      readRestatePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')

    // `was` is a string here, where `amend` sends a map. One key, two shapes.
    expect(outcome.value.was).toBe(before.symptom)
    expect(outcome.value.now).toBe('the claim this line made turned out to be false')
    expect(restated(outcome.value).changed).toEqual(['symptom'])

    const after = await shown('FX2')
    expect(after.id).toBe('FX2')
    expect(after.status).toBe(before.status)
    expect(after.section?.body).toBe(before.section?.body)
  })

  it('names the follow-ups it did not do, and does not do them', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'restate', {
        id: 'FX2',
        symptom: 'a second restatement, to read what the verb leaves behind',
      }),
      readRestatePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const next = restated(outcome.value).next

    // The why and the design were written from the claim just replaced. Whether they still
    // hold is the reader's call, so the verb names the doors and leaves them shut.
    expect(next.length).toBeGreaterThan(0)
    expect(next.join(' ')).toContain('FX2')
  })

  it('says when it was a slip of the pen rather than a false premise', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'restate', {
        id: 'FX2',
        symptom: 'a second restatement, to read what the verb leaves behind it',
        typo: true,
      }),
      readRestatePayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.typo).toBe(true)
  })
})

describe('RG35: a line moved to a free id, with everything that names it', () => {
  it('takes the section with it and rewrites what pointed at it', async () => {
    const before = await shown('FX3')

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'renumber', { id: 'FX3', to: 'FX90' }),
      readRenumberPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const one = renumbered(outcome.value)

    expect(one.id).toBe('FX3')
    expect(one.nowId).toBe('FX90')
    // The section moved and was re-anchored, which is the half a hand edit would forget.
    expect(outcome.value.section?.anchor).toBe('FX90')
    expect(outcome.value.wrote.some((file) => file.includes('IMPROVEMENTS.md'))).toBe(true)

    const after = await shown('FX90')
    expect(after.symptom).toBe(before.symptom)
    expect(after.section?.body).toBe(before.section?.body)
    expect(await ids()).not.toContain('FX3')
    expect(await ids()).toContain('FX90')
  })
})
