import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import {
  applyWrite,
  composeWrite,
  createClient,
  createWatching,
  governedFiles,
  readAddedPayload,
  watchedFiles,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createGovernedWatcher, REAL_CLOCK } from './governed-watch'
import { createProcessTransport } from './process-transport'
import { stampGoverned } from './governed-stamp'

/**
 * The watcher against real files and real writes.
 *
 * The claim worth proving here is the one the design turns on: a write this app made is
 * seen the same way as one anything else made. So the test writes through the write path
 * and waits for the watch, rather than telling the cache itself.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture
let files: string[] = []
const scratch: string[] = []

/** Wait for the next change, or give up. Nothing here sleeps a fixed amount. */
function nextChange(watching: ReturnType<typeof createWatching>, ms = 8000): Promise<string> {
  return new Promise((resolve, reject) => {
    const stop = watching.onChanged((root) => {
      stop()
      clearTimeout(timer)
      resolve(root)
    })
    const timer = setTimeout(() => {
      stop()
      reject(new Error('nothing changed'))
    }, ms)
  })
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })

  const answer = await client.call(fixture.root, 'config', {}, { timeoutMs: CEILING })
  if (!answer.ok || answer.value.kind === 'refused') throw new Error('config did not read')
  files = watchedFiles(Object.values(governedFiles(answer.value.value)))
}, 180000)

afterAll(() => {
  fixture.dispose()
  for (const home of scratch) rmSync(home, { recursive: true, force: true })
})

describe('RG45: what to watch comes off the config', () => {
  it('reads the governed set the project declares, plus the config itself', () => {
    expect(files.length).toBeGreaterThan(3)
    expect(files).toContain('roadkeep.toml')
    expect(files.some((file) => file.includes('ROADMAP'))).toBe(true)
  })
})

describe('RG45: one path to a redraw', () => {
  it('sees a write this app made, through the same watch as any other', async () => {
    // Nothing tells the watcher that this app wrote. It finds out the way it would find
    // out about a terminal or an agent — which is the whole point of there being one path.
    const watching = createWatching(createGovernedWatcher(), REAL_CLOCK)
    const interest = watching.hold(fixture.root, files)
    const changed = nextChange(watching)

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'a line filed to make the files move',
        why: 'The watcher has to see this the way it sees anything else.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(outcome.kind).toBe('applied')

    await expect(changed).resolves.toBe(fixture.root)
    interest.release()
  })

  it('sees a write nothing in this app made', async () => {
    const watching = createWatching(createGovernedWatcher(), REAL_CLOCK)
    const interest = watching.hold(fixture.root, files)
    const changed = nextChange(watching)

    // A terminal, an agent, an editor — all the same to a watch on the files.
    writeFileSync(path.join(fixture.root, 'roadkeep.toml'), '\n# touched\n', { flag: 'a' })

    await expect(changed).resolves.toBe(fixture.root)
    interest.release()
  })

  it('moves the stamp the cache is keyed on, so a re-read is a real re-read', async () => {
    // The watch and the cache agree about what a change is: both are about these files.
    const before = stampGoverned(fixture.root, files)

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'a second line, to move the stamp',
        why: 'A watch that fired spuriously costs a read and never a wrong answer.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(outcome.kind).toBe('applied')

    expect(stampGoverned(fixture.root, files)).not.toBe(before)
  })

  it('says nothing for a project nobody is holding', async () => {
    const watching = createWatching(createGovernedWatcher(), REAL_CLOCK)
    const told: string[] = []
    watching.onChanged((root) => told.push(root))

    // Held and released before anything happens: the handles are gone.
    watching.hold(fixture.root, files).release()
    writeFileSync(path.join(fixture.root, 'roadkeep.toml'), '\n# again\n', { flag: 'a' })
    await new Promise((resolve) => setTimeout(resolve, 600))

    expect(told).toEqual([])
    expect(watching.held).toEqual([])
  })
})

describe('RG45: a governed file that is not there yet', () => {
  it('is watched by its directory, so the moment it appears is a change', async () => {
    // A project whose deferred store has never been written is the ordinary case, and the
    // moment `defer` creates it is exactly when a screen needs telling.
    const home = mkdtempSync(path.join(tmpdir(), 'rk-watch-'))
    scratch.push(home)

    const watching = createWatching(createGovernedWatcher(), REAL_CLOCK)
    const interest = watching.hold(home, ['roadkeep.toml', 'docs/NOT-YET.md'])
    const changed = nextChange(watching)

    writeFileSync(path.join(home, 'roadkeep.toml'), 'prefix = "FX"\n')

    await expect(changed).resolves.toBe(home)
    interest.release()
  })
})
