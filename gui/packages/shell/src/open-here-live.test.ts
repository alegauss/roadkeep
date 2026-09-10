import { existsSync } from 'node:fs'
import path from 'node:path'

import { buildArgv, listedTasks, type Opening, type OpenProject } from '@rk/core'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { openHere, type OpenHereOptions } from './open-here'
import { createProcessTransport } from './process-transport'

/**
 * RG103: the composition, against a real engine.
 *
 * The unit tests hold the order and the states against a machine described by hand. This
 * holds the same call against a real roadkeep, because the point of the line is that a
 * screen can make one call and get something to read from — and a composition that only
 * works against a fake is the recipe it replaced with extra steps.
 *
 * Since RG122 that call keeps a `roadkeep mcp` per project, which is what the last block
 * here measures — and what makes `open` below the only way this file opens one.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CEILING = 60000

const engine = createProcessTransport({
  command: 'python',
  prefixArgs: [path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')],
})

let fixture: Fixture

/**
 * Open a project, and remember it for closing.
 *
 * Every project this file opens goes through here, because since RG122 one holds a process
 * with the project as its working directory — and the teardown below is what enforces it: a
 * fixture a server is still standing in is a directory Windows refuses to remove, so a test
 * that forgets to close reports a red `afterAll` rather than a leak nobody sees.
 */
const held: OpenProject[] = []

async function open(root: string, options: OpenHereOptions = {}): Promise<Opening> {
  const opening = await openHere(root, { timeoutMs: CEILING, ...options })
  if (opening.kind === 'open') held.push(opening.project)
  return opening
}

afterEach(async () => {
  await Promise.all(held.splice(0).map((project) => project.close()))
})

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG103: opening a real project in one call', () => {
  it('resolves the engine, reads what it governs, and hands back a client', async () => {
    const opened = await open(fixture.root)

    expect(opened.kind).toBe('open')
    if (opened.kind !== 'open') return

    // The three facts a screen needs before it draws anything, none of which it had to
    // assemble a transport to get.
    expect(opened.project.engine.payload.writing.version).toMatch(/^\d+\.\d+\.\d+/)
    expect(Object.values(opened.project.governed)).toContain('docs/ROADMAP.md')
    expect(opened.project.capabilities.kind).toBe('known')
  })

  it('reads a backlog through the client it was handed', async () => {
    const opened = await open(fixture.root)
    if (opened.kind !== 'open') return

    const answer = await opened.project.client.call(fixture.root, 'list', {}, {})

    expect(answer.kind).toBe('read')
    if (answer.kind !== 'read') return
    expect(listedTasks(answer.value).length).toBeGreaterThan(0)
  })

  it('says which build this is, and that this app can run every verb it sends', async () => {
    const opened = await open(REPO)
    if (opened.kind !== 'open') return
    const report = opened.project.capabilities
    if (report.kind !== 'known') return

    // The read RG6 is about, now paid for once per project rather than per caller.
    expect(report.complete).toBe(true)
    expect(report.version).toBe(opened.project.engine.payload.writing.version)
  })
})

describe('RG103: what an open project stops paying for', () => {
  it('serves a second read of an unchanged project without asking the engine at all', async () => {
    const opened = await open(fixture.root)
    if (opened.kind !== 'open') return

    const first = await opened.project.client.call(fixture.root, 'list', {}, {})
    expect(first.kind).toBe('read')

    // A signal that is already aborted, which is what a screen that redrew looks like. The
    // pool refuses a cancelled call rather than starting one, so an answer here is the
    // remembered one and could not be anything else — and this is a mechanism rather than a
    // clock, which RG122 is why: with the engine held, a read of this fixture and a read of
    // memory are both about a millisecond, and timing the two says nothing.
    const cancelled = AbortSignal.abort()
    const again = await opened.project.client.call(
      fixture.root,
      'list',
      {},
      { signal: cancelled, timeoutMs: CEILING },
    )
    expect(again.kind).toBe('read')

    // The control, and what makes the assertion above mean anything: with nothing
    // remembered the same call reaches the pool and is refused. The stamp is over the files
    // this project declared, which the composition read for itself — a caller assembling
    // the cache by hand had to know them first.
    opened.project.invalidate()
    const forgotten = await opened.project.client.call(
      fixture.root,
      'list',
      {},
      { signal: cancelled, timeoutMs: CEILING },
    )
    expect(forgotten.kind).toBe('unreadable')
  })

  it('asks again once a governed file has moved under it', async () => {
    const opened = await open(fixture.root)
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
    const opened = await open(fixture.root)
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
    const opened = await open(path.join(REPO, 'packages'), {
      candidates: { onPath: 'no-such-engine-anywhere' },
    })

    expect(opened.kind).toBe('unresolved')
    if (opened.kind !== 'unresolved') return
    expect(opened.reason).toContain('unknown')
    expect(opened.tried).toEqual([['no-such-engine-anywhere']])
  })
})

describe('RG122: what a read costs the app now, and what closing gives back', () => {
  it('reads eight times for less than one spawned read costs', async () => {
    // RG101 measured this repository at 5904ms for eight reads spawned and 45ms held, and
    // this is the claim of RG122: that the composition a screen calls pays the second
    // number. Nothing is remembered, so all eight reach the engine — a cached run would
    // measure the cache and say nothing about the transport.
    const opened = await open(fixture.root, { cacheable: () => false })
    if (opened.kind !== 'open') return

    const startedHeld = Date.now()
    for (let read = 0; read < 8; read += 1) {
      const answer = await opened.project.client.call(fixture.root, 'list', {}, {})
      expect(answer.kind).toBe('read')
    }
    const overHeld = Date.now() - startedHeld

    // The yardstick is a *single* spawn, because the margin is what makes this an assertion
    // about a transport and not about how fast this machine is: eight held reads against
    // one interpreter start is the smallest honest comparison, and it still has two orders
    // of magnitude in hand.
    const startedSpawn = Date.now()
    await engine.run({
      root: fixture.root,
      argv: buildArgv(fixture.root, 'list', {}),
      timeoutMs: CEILING,
    })
    const oneSpawn = Date.now() - startedSpawn

    expect(overHeld).toBeLessThan(oneSpawn)
  })

  it('lets the project directory go once the project is closed', async () => {
    // What closing has to mean, said in the one way an operating system can check: a server
    // has the project as its working directory, and Windows will not remove a directory a
    // live process is standing in. So a fixture that disposes is a process that is gone —
    // and RG101 records why that is `taskkill /T` here rather than a `kill`.
    const own = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })
    const opened = await openHere(own.root, { timeoutMs: CEILING })
    if (opened.kind !== 'open') throw new Error(`the fixture did not open: ${opened.kind}`)

    // A read first, because the engine is started by the call and not by the open.
    expect((await opened.project.client.call(own.root, 'list', {}, {})).kind).toBe('read')
    await opened.project.close()

    own.dispose()
    expect(existsSync(own.root)).toBe(false)
  })
})
