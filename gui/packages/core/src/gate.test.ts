import { describe, expect, it } from 'vitest'

import {
  createGateLedger,
  gateHealth,
  needsGate,
  recordGate,
  UNKNOWN_GATE,
  type GateRecord,
} from './gate'
import type { LintPayload } from './payloads'

const keyOf = (path: string) => path.toLowerCase()
const TUESDAY = '2026-09-01T10:00:00.000Z'
const FRIDAY = '2026-09-04T10:00:00.000Z'

const lint = (clean: boolean, problems = 0): LintPayload => ({
  root: '/code/a',
  clean,
  checked: ['docs/ROADMAP.md'],
  lines: 60,
  sections: 55,
  problems,
  codes: {},
  findings: [],
  notes: [],
})

describe('RG18: unknown is a state of its own', () => {
  it('is what a project with no run shows', () => {
    expect(gateHealth(undefined, 'stamp-a')).toEqual(UNKNOWN_GATE)
  })

  it('is not clean', () => {
    // A row showing clean because nothing had run would be saying the opposite of what it
    // knows, and "this project is fine" is exactly the claim somebody acts on.
    expect(UNKNOWN_GATE.verdict).not.toBe('clean')
    expect(UNKNOWN_GATE.verdict).toBe('unknown')
  })

  it('reports no moment, because there was none', () => {
    expect(UNKNOWN_GATE.taken).toBeNull()
    expect(UNKNOWN_GATE.stale).toBe(false)
  })
})

describe('RG18: a verdict that has been earned', () => {
  it('records clean when the gate found nothing', () => {
    const held = recordGate(lint(true), 'stamp-a', TUESDAY)

    expect(held).toEqual({ verdict: 'clean', problems: 0, taken: TUESDAY, stamp: 'stamp-a' })
  })

  it('records drifted with how much, when it found something', () => {
    const held = recordGate(lint(false, 3), 'stamp-a', TUESDAY)

    expect(held.verdict).toBe('drifted')
    expect(held.problems).toBe(3)
  })

  it('is fresh while the files have not moved', () => {
    const held = recordGate(lint(true), 'stamp-a', TUESDAY)

    expect(gateHealth(held, 'stamp-a')).toEqual({
      verdict: 'clean',
      problems: 0,
      taken: TUESDAY,
      stale: false,
    })
  })
})

describe('RG18: a verdict the files have outrun', () => {
  it('says it is stale rather than being thrown away', () => {
    const held = recordGate(lint(false, 2), 'stamp-a', TUESDAY)

    const health = gateHealth(held, 'stamp-b')

    expect(health.stale).toBe(true)
    expect(health.verdict).toBe('drifted')
    // Dated, not discarded: three findings an hour ago is more interesting than nothing.
    expect(health.problems).toBe(2)
    expect(health.taken).toBe(TUESDAY)
  })

  it('does not become unknown just because it aged', () => {
    const held = recordGate(lint(true), 'stamp-a', TUESDAY)

    expect(gateHealth(held, 'stamp-b').verdict).toBe('clean')
  })
})

describe('RG18: whether the gate is worth running', () => {
  it('is worth running when nothing is on record', () => {
    expect(needsGate(undefined, 'stamp-a')).toBe(true)
  })

  it('is worth running when the files moved', () => {
    expect(needsGate(recordGate(lint(true), 'stamp-a', TUESDAY), 'stamp-b')).toBe(true)
  })

  it('is not worth running again for the same files', () => {
    // The whole reason this is not driven by the screen: seventeen lints per redraw.
    expect(needsGate(recordGate(lint(true), 'stamp-a', TUESDAY), 'stamp-a')).toBe(false)
  })
})

describe('RG18: the verdicts held for a portfolio', () => {
  it('answers unknown for a project it has never seen', () => {
    const ledger = createGateLedger(keyOf)

    expect(ledger.healthOf('/code/a', 'stamp-a').verdict).toBe('unknown')
    expect(ledger.size).toBe(0)
  })

  it('keeps a verdict per project', () => {
    const ledger = createGateLedger(keyOf)
    ledger.note('/code/a', recordGate(lint(true), 'a1', TUESDAY))
    ledger.note('/code/b', recordGate(lint(false, 4), 'b1', TUESDAY))

    expect(ledger.healthOf('/code/a', 'a1').verdict).toBe('clean')
    expect(ledger.healthOf('/code/b', 'b1').problems).toBe(4)
    expect(ledger.size).toBe(2)
  })

  it('matches one project spelled two ways', () => {
    const ledger = createGateLedger(keyOf)
    ledger.note('D:\\Git\\App', recordGate(lint(true), 'a1', TUESDAY))

    expect(ledger.healthOf('d:\\git\\app', 'a1').verdict).toBe('clean')
  })

  it('says a project is stale once its files move', () => {
    const ledger = createGateLedger(keyOf)
    ledger.note('/code/a', recordGate(lint(true), 'a1', TUESDAY))

    expect(ledger.stale('/code/a', 'a1')).toBe(false)
    expect(ledger.stale('/code/a', 'a2')).toBe(true)
  })

  it('replaces a verdict when a fresh one arrives', () => {
    const ledger = createGateLedger(keyOf)
    ledger.note('/code/a', recordGate(lint(false, 3), 'a1', TUESDAY))
    ledger.note('/code/a', recordGate(lint(true), 'a2', FRIDAY))

    expect(ledger.healthOf('/code/a', 'a2')).toEqual({
      verdict: 'clean',
      problems: 0,
      taken: FRIDAY,
      stale: false,
    })
  })

  it('forgets a project that left the list', () => {
    const ledger = createGateLedger(keyOf)
    ledger.note('/code/a', recordGate(lint(true), 'a1', TUESDAY))
    ledger.forget('/code/a')

    expect(ledger.healthOf('/code/a', 'a1').verdict).toBe('unknown')
  })
})

describe('RG18: nothing is kept between launches', () => {
  it('starts empty, because a saved verdict is stale in the one way this cannot detect', () => {
    // The stamp a saved verdict was taken against would still match itself, so a file
    // changed while the app was closed would read as fresh. Better to be unknown.
    const first = createGateLedger(keyOf)
    first.note('/code/a', recordGate(lint(true), 'a1', TUESDAY))

    const afterRestart = createGateLedger(keyOf)
    expect(afterRestart.size).toBe(0)
    expect(afterRestart.healthOf('/code/a', 'a1').verdict).toBe('unknown')
  })
})

describe('RG18: what a record refuses to be', () => {
  it('cannot record unknown, which is the absence of a record', () => {
    const held: GateRecord = recordGate(lint(true), 'a1', TUESDAY)

    // A type-level guarantee worth an assertion: `unknown` is not a verdict a run can
    // produce, so it can only ever mean "nothing ran".
    expect(['clean', 'drifted']).toContain(held.verdict)
  })
})
