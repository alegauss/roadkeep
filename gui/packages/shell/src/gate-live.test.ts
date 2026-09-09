import { appendFileSync } from 'node:fs'
import path from 'node:path'

import { createGateLedger, governedFiles, recordGate } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'
import { stampGoverned } from './governed-stamp'
import { rootKey } from './root-paths'

/**
 * The gate against a real project, driven by the files rather than by a redraw. What this
 * has to show is the sequence a screen actually goes through: unknown, then a verdict,
 * then that verdict going stale the moment a governed file is written.
 */

let fixture: Fixture
let governed: string[] = []

const stamp = () => stampGoverned(fixture.root, governed)

/** Run the gate once and put the verdict on the ledger, as the watcher would. */
async function runGate(ledger: ReturnType<typeof createGateLedger>): Promise<void> {
  const taken = stamp()
  const linted = await read(fixture.root, 'lint', {})
  ledger.note(fixture.root, recordGate(linted, taken, new Date().toISOString()))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 0 })

  governed = Object.values(governedFiles(await read(fixture.root, 'config', {})))
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG18: what a real project’s gate says, and when', () => {
  it('is unknown before anything has run', async () => {
    const ledger = createGateLedger(rootKey)

    // First launch. Not clean — nothing has been asked.
    expect(ledger.healthOf(fixture.root, stamp()).verdict).toBe('unknown')
    expect(ledger.stale(fixture.root, stamp())).toBe(true)
  })

  it('is a verdict once the gate has actually run', async () => {
    const ledger = createGateLedger(rootKey)
    await runGate(ledger)

    const health = ledger.healthOf(fixture.root, stamp())

    // The fixture is built by the write verbs, so it should be clean.
    expect(health.verdict).toBe('clean')
    expect(health.stale).toBe(false)
    expect(health.taken).not.toBeNull()
  })

  it('is not worth running again while the files have not moved', async () => {
    const ledger = createGateLedger(rootKey)
    await runGate(ledger)

    // The cost this whole arrangement avoids: seventeen lints per redraw.
    expect(ledger.stale(fixture.root, stamp())).toBe(false)
  })

  it('goes stale the moment a governed file is written', async () => {
    const ledger = createGateLedger(rootKey)
    await runGate(ledger)
    const before = ledger.healthOf(fixture.root, stamp())

    appendFileSync(path.join(fixture.root, 'docs', 'ROADMAP.md'), '\n')

    const after = ledger.healthOf(fixture.root, stamp())

    expect(before.stale).toBe(false)
    expect(after.stale).toBe(true)
    // Dated, not discarded: the verdict and the moment survive.
    expect(after.verdict).toBe(before.verdict)
    expect(after.taken).toBe(before.taken)
    expect(ledger.stale(fixture.root, stamp())).toBe(true)
  })

  it('reports drifted when the gate actually finds something', async () => {
    // A governed file edited by hand is exactly what the gate exists to catch, and this
    // fixture is a scratch directory, so doing it here costs nothing.
    appendFileSync(
      path.join(fixture.root, 'docs', 'ROADMAP.md'),
      '\n- 📋 **FX999** **a line no write path produced** — Written by hand to make the gate fail. → §FX999\n',
    )

    const ledger = createGateLedger(rootKey)
    await runGate(ledger)

    const health = ledger.healthOf(fixture.root, stamp())
    expect(health.verdict).toBe('drifted')
    expect(health.problems).toBeGreaterThan(0)
  })
})
