import {
  applyWrite,
  changeLine,
  composeWrite,
  createWatching,
  governedFiles,
  landingBetween,
  readAddedPayload,
  readDeferPayload,
  readSectionWritten,
  readShipPayload,
  readStatusPayload,
  saidButNotDone,
  watchedFiles,
  type Reading,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveClient as client, liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'
import { createGovernedWatcher, REAL_CLOCK } from './governed-watch'

/**
 * What a session did, read the way this app will read it: real writes through the real
 * verbs, and the line re-briefed to see what moved.
 *
 * The writes stand in for an agent's. That is the point rather than a shortcut — an agent
 * ships through the same verbs a person does, so a write here is the same evidence.
 */

let fixture: Fixture
let files: string[] = []

/** Read the line as it stands, or as the refusal that says it has gone. */
async function readingOf(id: string): Promise<Reading> {
  const answer = await client.call(fixture.root, 'brief', { id }, { timeoutMs: CEILING })
  if (answer.kind === 'unreadable') throw new Error(answer.unreadable.message)
  return answer.kind === 'read'
    ? { kind: 'read', payload: answer.value }
    : { kind: 'gone', refusal: answer.refusal }
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 4, shipped: 0, deferred: 0 })

  files = watchedFiles(Object.values(governedFiles(await read(fixture.root, 'config', {}))))
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG42: what the files say a session did', () => {
  it('sees the marker move', async () => {
    const before = await readingOf('FX1')

    const moved = await applyWrite(
      engine,
      composeWrite(fixture.root, 'status', { id: 'FX1', marker: '🛠' }),
      readStatusPayload,
      { timeoutMs: CEILING },
    )
    expect(moved.kind).toBe('applied')

    const landing = landingBetween(before, await readingOf('FX1'))

    expect(landing.moved).toBe(true)
    expect(landing.changes.some((change) => change.kind === 'marker')).toBe(true)
  })

  it('sees a design appear where a session wrote one', async () => {
    const filed = await applyWrite(
      engine,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'a line whose rationale a session will write',
        why: 'A design appearing is evidence, and it is in the same read.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(filed.kind).toBe('applied')
    if (filed.kind !== 'applied') throw new Error('unreachable')
    const id = filed.value.id

    const before = await readingOf(id)

    const written = await applyWrite(
      engine,
      composeWrite(fixture.root, 'sectionAdd', {
        anchor: id,
        title: 'What a session wrote here',
        body: 'Prose long enough to read as a rationale and well inside the declared budget.',
      }),
      readSectionWritten,
      { timeoutMs: CEILING },
    )
    expect(written.kind).toBe('applied')

    const landing = landingBetween(before, await readingOf(id))
    expect(landing.changes.map(changeLine)).toContain('design written')
  })

  it('sees the line leave for the ledger, with its design deleted', async () => {
    const before = await readingOf('FX2')

    const shipped = await applyWrite(
      engine,
      composeWrite(fixture.root, 'ship', {
        id: 'FX2',
        why: 'The read now answers, and a test holds it.',
      }),
      readShipPayload,
      { timeoutMs: CEILING },
    )
    expect(shipped.kind).toBe('applied')

    const landing = landingBetween(before, await readingOf('FX2'))
    const lines = landing.changes.map(changeLine)

    // All three, off one re-read: the marker, the ledger and the deleted design.
    expect(lines).toContain('shipped, and in the ledger')
    expect(lines).toContain('design deleted')
    expect(landing.changes.some((change) => change.kind === 'marker')).toBe(true)
  })

  it('sees a line that stopped briefing as having left, in the engine sentence', async () => {
    const before = await readingOf('FX3')

    const set = await applyWrite(
      engine,
      composeWrite(fixture.root, 'defer', { id: 'FX3', reason: 'Waiting on a decision.' }),
      readDeferPayload,
      { timeoutMs: CEILING },
    )
    expect(set.kind).toBe('applied')

    const after = await readingOf('FX3')
    expect(after.kind).toBe('gone')

    const landing = landingBetween(before, after)
    expect(landing.changes[0]?.kind).toBe('left')
    expect(changeLine(landing.changes[0]!)).toContain('FX3')
  })
})

describe('RG42: beside the stream, not inside it', () => {
  it('names a session that claimed a ship the files do not show', async () => {
    // The disagreement is the point: a session can report shipping a line it did not.
    const before = await readingOf('FX4')
    const landing = landingBetween(before, await readingOf('FX4'))

    expect(landing.moved).toBe(false)
    expect(saidButNotDone(true, landing)).toBe(true)
  })
})

describe('RG42: watched while the session runs', () => {
  it('is told the project moved, then re-reads to find what', async () => {
    // The whole loop: the watch says *something* changed and the brief says *what*. The
    // watch never claims to know which line moved.
    const watching = createWatching(createGovernedWatcher(), REAL_CLOCK)
    const interest = watching.hold(fixture.root, files)

    const told = new Promise<string>((resolve, reject) => {
      const stop = watching.onChanged((root) => {
        stop()
        clearTimeout(timer)
        resolve(root)
      })
      const timer = setTimeout(() => {
        stop()
        reject(new Error('nothing changed'))
      }, 8000)
    })

    const before = await readingOf('FX1')
    const moved = await applyWrite(
      engine,
      composeWrite(fixture.root, 'status', { id: 'FX1', marker: '📋' }),
      readStatusPayload,
      { timeoutMs: CEILING },
    )
    expect(moved.kind).toBe('applied')

    await expect(told).resolves.toBe(fixture.root)

    const landing = landingBetween(before, await readingOf('FX1'))
    expect(landing.moved).toBe(true)
    interest.release()
  })
})
