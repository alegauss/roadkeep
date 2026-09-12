import { describe, expect, it } from 'vitest'

import type { RecordedProject } from './catalogue'
import { coldStart, type ColdStartProgress, type ColdStartStage } from './cold-start'
import type { StatsPayload } from './payloads'
import { EngineCallFailed } from './transport'
import { DECLARES_NOTHING } from './payloads'

const project = (path: string): RecordedProject => ({
  path,
  aliases: [],
  commonDir: null,
  root: '/code',
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
  branch: '',
  declared: DECLARES_NOTHING,
})

const PROJECTS = ['/code/a', '/code/b', '/code/c'].map(project)
const TUESDAY = '2026-09-01T10:00:00.000Z'

/**
 * Let every settled promise run. Ten microtask turns rather than a timer: everything
 * under test is promise-based with no I/O, so this is deterministic where a delay would
 * be a race, and `core` has no `setTimeout` in scope to race with anyway.
 */
async function flush(): Promise<void> {
  for (let turn = 0; turn < 10; turn += 1) await Promise.resolve()
}

const statsFor = (total: number): StatsPayload => ({
  file: 'docs/ROADMAP.md',
  total,
  uncounted: 0,
  markers: {},
  startable: null,
  blocks: [],
})

/**
 * A stage the test finishes by hand, one project at a time.
 *
 * Deferreds rather than timers, and not only because `core` has no `setTimeout` in scope:
 * a test that races two delays passes or fails on how busy the machine is, and the thing
 * being asserted here — that completion order does not reach the screen — is exactly what
 * a flaky ordering test would stop covering.
 */
function controlled(name = 'counts') {
  const waiting = new Map<string, (reads: object) => void>()
  const entered: string[] = []

  const stage: ColdStartStage = {
    name,
    read: (project_) => {
      entered.push(project_.path)
      return new Promise((resolve) => waiting.set(project_.path, resolve))
    },
  }

  return {
    stage,
    entered: () => entered,
    inFlight: () => waiting.size,
    finish(path: string, reads: object = { stats: statsFor(path.length) }) {
      const resolve = waiting.get(path)
      waiting.delete(path)
      resolve?.(reads)
    },
    finishAll() {
      for (const path of [...waiting.keys()]) this.finish(path)
    },
  }
}

describe('RG17: the order the screen fills in', () => {
  it('is the recorded order, whatever finishes first', async () => {
    // A list that reorders while somebody is reading it is worse than one that fills in
    // slowly: the row they were about to click moves for a reason they cannot see.
    const counts = controlled()
    const run = coldStart(PROJECTS, [counts.stage])
    await Promise.resolve()

    counts.finish('/code/c')
    counts.finish('/code/a')
    counts.finish('/code/b')

    expect((await run).map((row) => row.path)).toEqual(['/code/a', '/code/b', '/code/c'])
  })

  it('keeps the order in every progress report too', async () => {
    const counts = controlled()
    const seen: string[][] = []
    const run = coldStart(PROJECTS, [counts.stage], (progress) => {
      seen.push(progress.rows.map((row) => row.path))
    })
    await Promise.resolve()

    counts.finish('/code/b')
    counts.finish('/code/c')
    counts.finish('/code/a')
    await run

    expect(seen).toHaveLength(3)
    for (const order of seen) {
      expect(order).toEqual(['/code/a', '/code/b', '/code/c'])
    }
  })
})

describe('RG17: results as they arrive', () => {
  it('has a drawable screen before the reads finish', async () => {
    const counts = controlled()
    const states: string[][] = []
    const run = coldStart(PROJECTS, [counts.stage], (progress) => {
      states.push(progress.rows.map((row) => row.state))
    })
    await Promise.resolve()

    counts.finish('/code/b')
    await Promise.resolve()

    // One row read, two still pending. That is the whole claim.
    expect(states[0]).toEqual(['pending', 'read', 'pending'])

    counts.finishAll()
    await run
    expect(states.at(-1)).toEqual(['read', 'read', 'read'])
  })

  it('says what it is doing and how far it has got', async () => {
    const counts = controlled('counts')
    const progress: ColdStartProgress[] = []
    const run = coldStart(PROJECTS, [counts.stage], (entry) => progress.push(entry))
    await Promise.resolve()
    counts.finishAll()
    await run

    expect(progress.map((entry) => entry.done)).toEqual([1, 2, 3])
    expect(progress.every((entry) => entry.total === 3)).toBe(true)
    expect(progress.every((entry) => entry.stage === 'counts')).toBe(true)
  })

  it('hands every project to the stage at once rather than one after another', async () => {
    // Nothing here counts processes — the pool does. What this asserts is that the stage
    // is given every project before any of them has answered.
    const counts = controlled()
    const run = coldStart(PROJECTS, [counts.stage])
    await Promise.resolve()

    expect(counts.inFlight()).toBe(3)
    expect(counts.entered()).toEqual(['/code/a', '/code/b', '/code/c'])

    counts.finishAll()
    await run
  })
})

describe('RG17: the cheap read first', () => {
  it('runs the stages in order and merges what each one filled', async () => {
    const order: string[] = []
    const counts: ColdStartStage = {
      name: 'counts',
      read: () => {
        order.push('counts')
        return Promise.resolve({ stats: statsFor(9) })
      },
    }
    const gate: ColdStartStage = {
      name: 'the gate',
      read: () => {
        order.push('gate')
        return Promise.resolve({
          gate: { verdict: 'clean' as const, problems: 0, taken: TUESDAY, stale: false },
        })
      },
    }

    const rows = await coldStart([project('/code/a')], [counts, gate])

    expect(order).toEqual(['counts', 'gate'])
    // Merged, not replaced: the shape arrives first and the detail joins it.
    expect(rows[0]?.counts?.total).toBe(9)
    expect(rows[0]?.gate?.verdict).toBe('clean')
  })

  it('does not start the second stage before the first has finished everywhere', async () => {
    const counts = controlled('counts')
    const gate = controlled('the gate')
    const run = coldStart(PROJECTS, [counts.stage, gate.stage])
    await flush()

    expect(counts.inFlight()).toBe(3)
    expect(gate.inFlight()).toBe(0)

    counts.finish('/code/a')
    await flush()
    // One project done is not the stage done: the cheap read has to land everywhere
    // before the expensive one starts anywhere, or the pool fills with both at once.
    expect(gate.inFlight()).toBe(0)

    counts.finishAll()
    await flush()
    expect(gate.inFlight()).toBe(3)

    gate.finishAll()
    await run
  })
})

describe('RG17: a project that will not answer', () => {
  it('becomes an unreadable row and does not stop the others', async () => {
    const stage: ColdStartStage = {
      name: 'counts',
      read: (project_) =>
        project_.path === '/code/b'
          ? Promise.reject(new EngineCallFailed('timeout', 'ran past 15000ms', 15001))
          : Promise.resolve({ stats: statsFor(4) }),
    }

    const rows = await coldStart(PROJECTS, [stage])

    expect(rows.map((row) => row.state)).toEqual(['read', 'unreadable', 'read'])
    expect(rows[1]?.unreadable?.reason).toBe('timeout')
    expect(rows[1]?.unreadable?.elapsedMs).toBe(15001)
  })

  it('is not put through the later stages', async () => {
    // Three more calls to a project that already could not answer is time taken from the
    // projects that can.
    const asked: string[] = []
    const failing: ColdStartStage = {
      name: 'counts',
      read: (project_) =>
        project_.path === '/code/b'
          ? Promise.reject(new EngineCallFailed('unspawnable', 'no engine', 2))
          : Promise.resolve({ stats: statsFor(4) }),
    }
    const later: ColdStartStage = {
      name: 'the gate',
      read: (project_) => {
        asked.push(project_.path)
        return Promise.resolve({})
      },
    }

    await coldStart(PROJECTS, [failing, later])

    expect(asked).toEqual(['/code/a', '/code/c'])
  })

  it('survives a stage throwing something that is not an engine failure', async () => {
    const stage: ColdStartStage = {
      name: 'counts',
      read: () => Promise.reject(new TypeError('reader is not a function')),
    }

    const rows = await coldStart([project('/code/a')], [stage])

    expect(rows[0]?.state).toBe('unreadable')
    expect(rows[0]?.unreadable?.message).toContain('reader is not a function')
  })
})

describe('RG17: nothing to read', () => {
  it('finishes immediately on an empty list', async () => {
    expect(await coldStart([], [controlled().stage])).toEqual([])
  })

  it('leaves every row pending when there are no stages', async () => {
    const rows = await coldStart(PROJECTS, [])
    expect(rows.every((row) => row.state === 'pending')).toBe(true)
  })
})
