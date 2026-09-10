import path from 'node:path'

import { glanceRow, withNext, type OpenProject, type RecordedProject } from '@rk/core'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { openHere } from './open-here'
import { createProcessTransport } from './process-transport'

/**
 * RG73: what a row costs, counted against a real engine.
 *
 * The number in the design is the claim — four interpreter starts per project, sixty-eight
 * over seventeen — so what is asserted here is calls, not milliseconds. A machine's speed
 * is not the thing that changed.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CEILING = 60000

const engine = createProcessTransport({
  command: 'python',
  prefixArgs: [path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')],
})

let fixture: Fixture

/** A project the catalogue already knows about, which is what a row is drawn onto. */
const recorded = (projectPath: string): RecordedProject => ({
  path: projectPath,
  aliases: [],
  commonDir: null,
  root: path.dirname(projectPath),
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
})

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

/**
 * Every project this file opened, closed after each test.
 *
 * Since RG122 an open project holds a `roadkeep mcp` whose working directory is the
 * fixture, and the teardown is what enforces the closing: Windows will not remove a
 * directory a live process is standing in, so a forgotten close is a red run.
 */
const held: OpenProject[] = []

afterEach(async () => {
  await Promise.all(held.splice(0).map((project) => project.close()))
})

/** One project, opened, with every call it makes counted from here on. */
async function opened(): Promise<{ project: OpenProject; calls: () => number }> {
  const opening = await openHere(fixture.root, { timeoutMs: CEILING })
  if (opening.kind !== 'open') throw new Error(`the fixture did not open: ${opening.kind}`)
  held.push(opening.project)

  let calls = 0
  const client = opening.project.client
  const counted: OpenProject = {
    ...opening.project,
    client: {
      call(root, verb, input, options) {
        calls += 1
        return client.call(root, verb, input, options)
      },
    },
  }
  return { project: counted, calls: () => calls }
}

describe('RG73: what one row costs', () => {
  it('draws a scannable row in one call, not four', async () => {
    const { project, calls } = await opened()

    const row = await glanceRow(recorded(fixture.root), project, { timeoutMs: CEILING })

    // Counts and the engine — how big, whose roadkeep, is it modified — which is what a
    // list is scanned for. `engines` is not among the calls because resolution answered it.
    expect(calls()).toBe(1)
    expect(row.state).toBe('read')
    expect(row.counts?.total).toBeGreaterThan(0)
    expect(row.engine?.version).toMatch(/^\d+\.\d+\.\d+/)
  })

  it('carries the engine resolution already read, rather than asking again', async () => {
    const { project } = await opened()

    const row = await glanceRow(recorded(fixture.root), project, { timeoutMs: CEILING })

    // The same payload, not a second answer to the same question.
    expect(row.engine?.version).toBe(project.engine.payload.writing.version)
    expect(row.engine?.home).toBe(project.engine.payload.writing.home)
  })

  it('adds the next line in a second call, keeping what was already drawn', async () => {
    const { project, calls } = await opened()

    const glanced = await glanceRow(recorded(fixture.root), project, { timeoutMs: CEILING })
    const filled = await withNext(glanced, project, null, { timeoutMs: CEILING })

    expect(calls()).toBe(2)
    expect(filled.next?.id).toMatch(/^FX\d+$/)
    // What the first pass drew survives the second: a list that recomputed its counts
    // would flicker for no new fact.
    expect(filled.counts).toEqual(glanced.counts)
    expect(filled.engine).toEqual(glanced.engine)
  })

  it('never runs the gate to draw a list', async () => {
    const { project, calls } = await opened()

    const row = await withNext(
      await glanceRow(recorded(fixture.root), project, { timeoutMs: CEILING }),
      project,
      null,
      { timeoutMs: CEILING },
    )

    // Two calls for a filled row, and `lint` is not one of them: the gate's verdict comes
    // off the ledger, because running it seventeen times to draw a list is the cost this
    // whole arrangement avoids.
    expect(calls()).toBe(2)
    expect(row.gate).toBeNull()
  })

  it('keeps a row that could not learn its next line', async () => {
    const { project } = await opened()
    const glanced = await glanceRow(recorded(fixture.root), project, { timeoutMs: CEILING })

    // A read that never happens, which is what a screen redrawing before its second pass
    // lands looks like: the pool refuses a cancelled call rather than starting one. This
    // was a one millisecond ceiling until RG122 held the engine — a read of this fixture
    // now answers inside one, so the ceiling stopped standing for a read that failed.
    const filled = await withNext(glanced, project, null, { signal: AbortSignal.abort() })

    expect(filled.state).toBe('read')
    expect(filled.counts).toEqual(glanced.counts)
    expect(filled.next).toBeNull()
  })
})
