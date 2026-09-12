import path from 'node:path'

import {
  DECLARES_NOTHING,
  candidateBoard,
  createGateLedger,
  pendingRow,
  recordGate,
  readRow,
  tally,
  type ProjectRow,
  type RecordedProject,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveClient as client, liveEngine as engine, read, REPO } from './live'
import { buildFixture, type Fixture } from './fixture'
import { rootKey } from './root-paths'

/**
 * A portfolio of two real projects: this repository and a fixture built by the engine.
 * Two is enough to make the point the whole block rests on — a screen over more than one
 * backlog — and every number on both rows has to have come off a payload.
 */

const recorded = (projectPath: string): RecordedProject => ({
  path: projectPath,
  aliases: [],
  commonDir: null,
  root: path.dirname(projectPath),
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
  branch: '',
  declared: DECLARES_NOTHING,
})

/** Read one project the way the portfolio would, and build its row. */
async function rowFor(projectPath: string): Promise<ProjectRow> {
  const [statsRead, pickRead, lintRead, enginesRead] = await Promise.all([
    client.call(projectPath, 'stats', {}, { timeoutMs: CEILING }),
    client.call(projectPath, 'pick', {}, { timeoutMs: CEILING }),
    client.call(projectPath, 'lint', {}, { timeoutMs: CEILING }),
    client.call(projectPath, 'engines', {}, { timeoutMs: CEILING }),
  ])

  // Named individually: "false" tells whoever reads a red suite nothing, and the three
  // reads fail for entirely different reasons.
  for (const [verb, answer] of [
    ['stats', statsRead],
    ['pick', pickRead],
    ['lint', lintRead],
  ] as const) {
    if (answer.kind === 'unreadable') {
      throw new Error(`${verb} on ${projectPath} did not read: ${answer.unreadable.message}`)
    }
    if (answer.kind === 'refused') {
      throw new Error(`${verb} on ${projectPath} was refused: ${answer.refusal.said}`)
    }
  }
  if (statsRead.kind !== 'read' || pickRead.kind !== 'read' || lintRead.kind !== 'read') {
    throw new Error('unreachable')
  }

  // The gate goes through the ledger rather than straight onto the row: a verdict is
  // dated against the files it was taken from, which is what lets a row say it is stale.
  const ledger = createGateLedger(rootKey)
  ledger.note(projectPath, recordGate(lintRead.value, 'live', new Date().toISOString()))

  return readRow(recorded(projectPath), {
    stats: statsRead.value,
    pick: pickRead.value,
    gate: ledger.healthOf(projectPath, 'live'),
    engines: enginesRead.kind === 'read' ? enginesRead.value : null,
  })
}

let fixture: Fixture
/**
 * A second backlog with a line to offer, under another prefix (RG141).
 *
 * The two candidates used to be this repository's and the fixture's, which held only while
 * something here was ready — and the day every open line waited on something, this row had
 * no candidate and the board had one.
 */
let other: Fixture
/** A backlog with nothing open at all, which is the answer RG141 found unread. */
let waiting: Fixture

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 1 })
  other = await buildFixture(engine, { open: 1, shipped: 0, deferred: 0, prefix: 'FY' })
  waiting = await buildFixture(engine, { open: 0, shipped: 1, deferred: 1 })
}, 180000)

afterAll(() => {
  fixture.dispose()
  other.dispose()
  waiting.dispose()
})

describe('RG16: rows over more than one project', () => {
  it('builds a row per project, each from its own payloads', async () => {
    const rows = [await rowFor(REPO), await rowFor(fixture.root)]

    expect(rows.map((row) => row.state)).toEqual(['read', 'read'])
    expect(rows[0]?.name).toBe(path.basename(REPO))
    expect(rows[0]?.counts?.total).toBeGreaterThan(0)
    expect(rows[1]?.counts?.total).toBeGreaterThan(0)
  })

  it('counts each backlog on its own, and not one read shared between rows', async () => {
    // Both sides are fixtures whose sizes are declared here (RG197). Comparing this
    // repository's total against a fixture's was the same claim measured against a number
    // that moves: it held until shipping brought the backlog down to the fixture's three,
    // and then failed on a day nothing about a row had changed.
    const rows = [await rowFor(fixture.root), await rowFor(other.root)]

    expect(rows.map((row) => row.state)).toEqual(['read', 'read'])
    expect(rows[0]?.counts?.total).not.toBe(rows[1]?.counts?.total)
  })

  it('carries a number no screen computed', async () => {
    const row = await rowFor(fixture.root)
    const printed = await read(fixture.root, 'stats', {})

    // The criterion, checked rather than asserted: the number on the row is the number
    // the verb printed, not one derived from it.
    expect(row.counts?.total).toBe(printed.total)
  })

  it('carries the gate and the engine that answered', async () => {
    const row = await rowFor(fixture.root)

    expect(['clean', 'drifted']).toContain(row.gate?.verdict)
    expect(row.gate?.stale).toBe(false)
    expect(row.gate?.taken).not.toBeNull()
    expect(row.engine?.version).toMatch(/^\d+\.\d+\.\d+/)
    expect(row.engine?.verdict).not.toBe('')
  })

  it('carries the next line for a fixture that has one', async () => {
    const row = await rowFor(fixture.root)

    expect(row.next?.id).toMatch(/^FX\d+$/)
    expect(row.next?.tier).not.toBe('')
  })

  it('lays two real candidates side by side with the tier each came from', async () => {
    const rows = [await rowFor(other.root), await rowFor(fixture.root)]
    const board = candidateBoard(rows)

    expect(board.candidates).toHaveLength(2)
    // Two different backlogs, two ids from two prefixes, each with roadkeep's own tier.
    expect(board.candidates[0]?.id).toMatch(/^FY\d+$/)
    expect(board.candidates[1]?.id).toMatch(/^FX\d+$/)
    expect(board.candidates.every((entry) => entry.tier !== '')).toBe(true)

    // And the order is the one they were given in, not one this app worked out.
    expect(board.candidates.map((entry) => entry.project)).toEqual([other.root, fixture.root])
  })

  it('reads a backlog with nothing ready as a row with no next line', async () => {
    // RG141: the engine answers `pick: null` beside `tier: null` here, and the reader held the
    // tier to a string — so a project whose whole backlog was waiting read as a broken one.
    const row = await rowFor(waiting.root)
    const board = candidateBoard([row, await rowFor(fixture.root)])

    expect(row.state).toBe('read')
    expect(row.next?.id).toBeNull()
    expect(board.nothingToPick).toEqual([waiting.root])
    expect(board.unanswered).toEqual([])
  })

  it('counts rows and nothing else', async () => {
    const rows = [await rowFor(REPO), pendingRow(recorded('/not/read/yet'))]

    expect(tally(rows)).toEqual({ projects: 2, read: 1, pending: 1, unreadable: 0 })
  })
})
