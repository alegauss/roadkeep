import path from 'node:path'

import { listedTasks } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { openHere } from './open-here'
import { createProcessTransport } from './process-transport'

/**
 * RG103: the composition, against a real engine.
 *
 * The unit tests hold the order and the states against a machine described by hand. This
 * holds the same call against a real roadkeep, because the point of the line is that a
 * screen can make one call and get something to read from — and a composition that only
 * works against a fake is the recipe it replaced with extra steps.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CEILING = 60000

const engine = createProcessTransport({
  command: 'python',
  prefixArgs: [path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')],
})

let fixture: Fixture

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG103: opening a real project in one call', () => {
  it('resolves the engine, reads what it governs, and hands back a client', async () => {
    const opened = await openHere(fixture.root, { timeoutMs: CEILING })

    expect(opened.kind).toBe('open')
    if (opened.kind !== 'open') return

    // The three facts a screen needs before it draws anything, none of which it had to
    // assemble a transport to get.
    expect(opened.project.engine.payload.writing.version).toMatch(/^\d+\.\d+\.\d+/)
    expect(Object.values(opened.project.governed)).toContain('docs/ROADMAP.md')
    expect(opened.project.capabilities.kind).toBe('known')
  })

  it('reads a backlog through the client it was handed', async () => {
    const opened = await openHere(fixture.root, { timeoutMs: CEILING })
    if (opened.kind !== 'open') return

    const answer = await opened.project.client.call(fixture.root, 'list', {}, {})

    expect(answer.kind).toBe('read')
    if (answer.kind !== 'read') return
    expect(listedTasks(answer.value).length).toBeGreaterThan(0)
  })

  it('says which build this is, and that this app can run every verb it sends', async () => {
    const opened = await openHere(REPO, { timeoutMs: CEILING })
    if (opened.kind !== 'open') return
    const report = opened.project.capabilities
    if (report.kind !== 'known') return

    // The read RG6 is about, now paid for once per project rather than per caller.
    expect(report.complete).toBe(true)
    expect(report.version).toBe(opened.project.engine.payload.writing.version)
  })
})

describe('RG103: what an open project stops paying for', () => {
  it('serves a second read of an unchanged project without starting an interpreter', async () => {
    const opened = await openHere(fixture.root, { timeoutMs: CEILING })
    if (opened.kind !== 'open') return

    const first = Date.now()
    await opened.project.client.call(fixture.root, 'list', {}, {})
    const cold = Date.now() - first

    const second = Date.now()
    await opened.project.client.call(fixture.root, 'list', {}, {})
    const warm = Date.now() - second

    // The stamp is over the files this project declared, which the composition read for
    // itself. A caller assembling the cache by hand had to know them first.
    expect(cold).toBeGreaterThan(100)
    expect(warm).toBeLessThan(cold / 2)
  })

  it('asks again once a governed file has moved under it', async () => {
    const opened = await openHere(fixture.root, { timeoutMs: CEILING })
    if (opened.kind !== 'open') return

    const before = await opened.project.client.call(fixture.root, 'list', {}, {})
    if (before.kind !== 'read') return

    await engine.run({
      root: fixture.root,
      argv: [
        '-C',
        fixture.root,
        'add',
        '--block',
        'A',
        '--symptom',
        'a line written after the project was opened',
        '--why',
        'The cache is keyed on the files, so this has to reach a reader that already read.',
        '--json',
      ],
      timeoutMs: CEILING,
    })

    const after = await opened.project.client.call(fixture.root, 'list', {}, {})
    if (after.kind !== 'read') return

    // Not a timer and not a count of this app's own writes: the file moved, so the stamp
    // moved, and a write from anywhere — a terminal, an agent — is caught the same way.
    expect(listedTasks(after.value).length).toBe(listedTasks(before.value).length + 1)
  })

  it('never remembers the read that takes the line', async () => {
    const opened = await openHere(fixture.root, { timeoutMs: CEILING })
    if (opened.kind !== 'open') return

    const first = await opened.project.client.call(fixture.root, 'brief', { claim: true }, {})
    const again = await opened.project.client.call(fixture.root, 'brief', { claim: true }, {})

    expect(first.kind).toBe('read')
    expect(again.kind).toBe('read')
    if (first.kind !== 'read' || again.kind !== 'read') return

    // Both calls reached the engine, and the second line is the proof: a claim moves the
    // marker, so an unclaimed `brief` answers about the next line. Served from a cache the
    // second would be the first again, reporting one claim as though it were two.
    expect(first.value.claimed?.taken).toBe(true)
    expect(again.value.claimed?.taken).toBe(true)
    expect(again.value.id).not.toBe(first.value.id)
  })
})

describe('RG103: a project that does not open', () => {
  it('names what it tried, for a folder no roadkeep governs', async () => {
    const opened = await openHere(path.join(REPO, 'packages'), {
      timeoutMs: CEILING,
      candidates: { onPath: 'no-such-engine-anywhere' },
    })

    expect(opened.kind).toBe('unresolved')
    if (opened.kind !== 'unresolved') return
    expect(opened.reason).toContain('unknown')
    expect(opened.tried).toEqual([['no-such-engine-anywhere']])
  })
})
