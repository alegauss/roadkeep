import path from 'node:path'

import {
  attemptRead,
  buildArgv,
  coldStart,
  createPooledTransport,
  readEnginesPayload,
  readLintPayload,
  readPickPayload,
  readStatsPayload,
  tally,
  type ColdStartProgress,
  type ColdStartStage,
  type RecordedProject,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { machineWidth } from './machine'
import { createProcessTransport } from './process-transport'

/**
 * A cold start over real projects: no cache, every read a fresh interpreter, all of it
 * through the same pool every other read goes through.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const pooled = createPooledTransport(engine, { width: machineWidth() })

const recorded = (projectPath: string): RecordedProject => ({
  path: projectPath,
  aliases: [],
  commonDir: null,
  root: path.dirname(projectPath),
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
})

/** One stage: read one verb through the pool and turn it into the row's fields. */
function stage<K extends 'stats' | 'pick' | 'lint' | 'engines'>(
  name: string,
  verb: K,
  fill: (stdout: string) => object,
): ColdStartStage {
  return {
    name,
    read: async (project) => {
      const result = await pooled.run({
        root: project.path,
        argv: buildArgv(project.path, verb, {} as never),
        timeoutMs: CEILING,
      })
      return fill(result.stdout)
    },
  }
}

const COUNTS = stage('counts', 'stats', (stdout) => {
  const parsed = readStatsPayload(JSON.parse(stdout), '')
  return parsed.ok ? { stats: parsed.value } : {}
})

const DETAIL: ColdStartStage[] = [
  stage('the next line', 'pick', (stdout) => {
    const parsed = readPickPayload(JSON.parse(stdout), '')
    return parsed.ok ? { pick: parsed.value } : {}
  }),
  stage('the gate', 'lint', (stdout) => {
    const parsed = readLintPayload(JSON.parse(stdout), '')
    return parsed.ok ? { lint: parsed.value } : {}
  }),
  stage('the engine', 'engines', (stdout) => {
    const parsed = readEnginesPayload(JSON.parse(stdout), '')
    return parsed.ok ? { engines: parsed.value } : {}
  }),
]

let fixture: Fixture
let projects: RecordedProject[] = []

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 0 })
  projects = [recorded(REPO), recorded(fixture.root)]
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG17: a cold start over real projects', () => {
  it('fills every row and reports as it goes', async () => {
    const progress: ColdStartProgress[] = []
    const rows = await coldStart(projects, [COUNTS, ...DETAIL], (entry) => progress.push(entry))

    expect(tally(rows)).toMatchObject({ projects: 2, read: 2, unreadable: 0 })

    // It said what it was doing, stage by stage, and never went backwards.
    expect(progress.map((entry) => entry.stage)).toContain('counts')
    expect(progress.map((entry) => entry.stage)).toContain('the gate')
    expect(progress.at(-1)?.done).toBe(progress.at(-1)?.total)
  }, 180000)

  it('draws the shape before the detail', async () => {
    const afterCounts: ColdStartProgress[] = []
    await coldStart(projects, [COUNTS, ...DETAIL], (entry) => {
      if (entry.stage === 'counts') afterCounts.push(entry)
    })

    // Counts arrive first, so a list is scannable before the expensive reads land.
    const last = afterCounts.at(-1)
    expect(last?.rows.every((row) => row.counts !== null)).toBe(true)
    expect(last?.rows.every((row) => row.gate === null)).toBe(true)
  }, 180000)

  it('keeps the recorded order through a real fan-out', async () => {
    const rows = await coldStart(projects, [COUNTS])

    expect(rows.map((row) => row.path)).toEqual(projects.map((project) => project.path))
  }, 180000)

  it('turns a project with no engine into an unreadable row and keeps the rest', async () => {
    const broken = createPooledTransport(
      createProcessTransport({ command: 'no-such-engine-anywhere' }),
      { width: 2 },
    )
    const failing: ColdStartStage = {
      name: 'counts',
      read: async (project) => {
        const read = await attemptRead(
          broken,
          { root: project.path, argv: buildArgv(project.path, 'stats', {}), timeoutMs: 5000 },
          readStatsPayload,
        )
        if (!read.ok) throw read.unreadable
        return { stats: read.value }
      },
    }

    const rows = await coldStart([projects[0]!], [failing])

    expect(rows[0]?.state).toBe('unreadable')
    expect(rows[0]?.unreadable?.reason).toBe('unspawnable')
  }, 60000)
})
