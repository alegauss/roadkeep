import { describe, expect, it } from 'vitest'

import type { RecordedProject } from './catalogue'
import type { EnginesPayload } from './engines'
import type { Unreadable } from './limits'
import { gateHealth, recordGate, UNKNOWN_GATE } from './gate'
import type { PickPayload, StatsPayload } from './payloads'
import { folderName, pendingRow, readRow, tally, unreadableRow } from './portfolio'

const project: RecordedProject = {
  path: '/code/viglet/turing/2026.3',
  aliases: ['/code/viglet/turing/latest'],
  commonDir: '/code/viglet/turing/2026.3/.git',
  root: '/code',
  confirmed: '2026-09-01T10:00:00.000Z',
  presence: 'present',
}

const STATS: StatsPayload = {
  file: 'docs/ROADMAP.md',
  total: 60,
  uncounted: 0,
  markers: { '📋': 11, '💭': 48, '🛠': 1 },
  startable: { open: 60, startable: 58, waiting: 2, absent: [] },
  blocks: [],
}

const PICK: PickPayload = {
  pick: { id: 'RG45', block: 'G', status: '💭', symptom: 'nothing watches the files', ref: 'RG45' },
  tier: 'lowest-ready-id',
  reason: 'lowest ready id',
  ready: 26,
  blocked: 28,
  outside: 2,
  paused: 0,
}

const DRIFTED = recordGate(
  {
    root: '/code/viglet/turing/2026.3',
    clean: false,
    checked: ['docs/ROADMAP.md'],
    lines: 60,
    sections: 55,
    problems: 3,
    codes: {},
    findings: [],
    notes: [],
  },
  'stamp-a',
  '2026-09-01T10:00:00.000Z',
)

const ENGINES: EnginesPayload = {
  writing: { version: '0.2.360', home: '/engines/one', revision: 'abc1234', onDisk: '0.2.360' },
  invoke: 'roadkeep',
  declaration: '',
  verdict: 'agreed',
  agree: true,
  readable: true,
  split: false,
  swapped: false,
}

describe('RG16: what a row is made of', () => {
  it('takes its name from the folder and keeps the path and the aliases', () => {
    const row = readRow(project, {})

    expect(row.name).toBe('2026.3')
    expect(row.path).toBe(project.path)
    expect(row.aliases).toEqual(['/code/viglet/turing/latest'])
    expect(row.commonDir).toBe(project.commonDir)
  })

  it.each([
    ['/code/app', 'app'],
    ['D:\\Git\\viglet\\shio', 'shio'],
    ['/code/app/', 'app'],
    ['app', 'app'],
  ])('reads the folder name out of %s', (path, expected) => {
    expect(folderName(path)).toBe(expected)
  })

  it('carries the counts a verb printed, unchanged', () => {
    const row = readRow(project, { stats: STATS })

    // Every number on this screen is one a verb printed. Not one of them is recomputed.
    expect(row.counts?.total).toBe(60)
    expect(row.counts?.markers).toEqual(STATS.markers)
    expect(row.counts?.startable).toBe(58)
    expect(row.counts?.waiting).toBe(2)
  })

  it('carries the line pick chose and which tier answered', () => {
    const row = readRow(project, { pick: PICK })

    expect(row.next?.id).toBe('RG45')
    expect(row.next?.tier).toBe('lowest-ready-id')
    expect(row.next?.ready).toBe(26)
  })

  it('carries a backlog with nothing to pick, without inventing an id', () => {
    const row = readRow(project, { pick: { ...PICK, pick: null } })

    expect(row.next?.id).toBeNull()
    expect(row.next?.symptom).toBe('')
  })

  it('carries the gate verdict on record, dated', () => {
    const row = readRow(project, { gate: gateHealth(DRIFTED, 'stamp-a') })

    expect(row.gate).toEqual({
      verdict: 'drifted',
      problems: 3,
      taken: '2026-09-01T10:00:00.000Z',
      stale: false,
    })
  })

  it('shows a gate nobody has run as unknown rather than as clean', () => {
    const row = readRow(project, { gate: UNKNOWN_GATE })

    expect(row.gate?.verdict).toBe('unknown')
    expect(row.gate?.verdict).not.toBe('clean')
  })

  it('shows a verdict the files have outrun as stale', () => {
    const row = readRow(project, { gate: gateHealth(DRIFTED, 'stamp-b') })

    expect(row.gate?.stale).toBe(true)
    expect(row.gate?.verdict).toBe('drifted')
  })

  it('carries which copy of roadkeep answered', () => {
    const row = readRow(project, { engines: ENGINES })

    expect(row.engine?.version).toBe('0.2.360')
    expect(row.engine?.home).toBe('/engines/one')
    expect(row.engine?.verdict).toBe('agreed')
    expect(row.engine?.agree).toBe(true)
  })

  it('says when the copy that answered is a working tree', () => {
    // The answers are that tree's, `lint` says so out loud, and a row that smoothed it
    // over would attribute one person's edits to a project.
    const row = readRow(project, {
      engines: { ...ENGINES, writing: { ...ENGINES.writing, revision: 'abc1234 modified' } },
    })

    expect(row.engine?.modified).toBe(true)
  })

  it('says when the copies disagree', () => {
    const row = readRow(project, { engines: { ...ENGINES, split: true } })

    expect(row.engine?.agree).toBe(false)
  })
})

describe('RG16: a project not read yet', () => {
  it('is pending, with every payload field still absent', () => {
    // Zero open tasks and not-yet-known look identical on a screen and mean opposite
    // things, and the one that gets believed is the wrong one.
    const row = pendingRow(project)

    expect(row.state).toBe('pending')
    expect(row.counts).toBeNull()
    expect(row.next).toBeNull()
    expect(row.gate).toBeNull()
    expect(row.engine).toBeNull()
  })

  it('still has enough to draw a row with', () => {
    const row = pendingRow(project)

    expect(row.name).toBe('2026.3')
    expect(row.aliases).toHaveLength(1)
  })

  it('leaves a field null when only some reads came back', () => {
    const row = readRow(project, { stats: STATS })

    expect(row.counts).not.toBeNull()
    // Null and unknown are different: null is "this row has no gate on it yet", unknown
    // is "the ledger was asked and has never seen a run".
    expect(row.gate).toBeNull()
  })
})

describe('RG16: a project that could not be read', () => {
  it('says so, with the reason and the argv', () => {
    const unreadable: Unreadable = {
      reason: 'timeout',
      message: 'the engine ran past 15000ms',
      elapsedMs: 15002,
      argv: ['-C', project.path, 'stats', '--json'],
      said: '',
    }

    const row = unreadableRow(project, unreadable)

    expect(row.state).toBe('unreadable')
    expect(row.unreadable?.reason).toBe('timeout')
    expect(row.counts).toBeNull()
  })
})

describe('RG16: how the screen stands', () => {
  const rows = [
    readRow(project, { stats: STATS }),
    pendingRow({ ...project, path: '/code/b' }),
    unreadableRow({ ...project, path: '/code/c' }, {
      reason: 'unspawnable',
      message: 'no python',
      said: '',
      elapsedMs: 3,
      argv: [],
    }),
  ]

  it('counts the rows', () => {
    expect(tally(rows)).toEqual({ projects: 3, read: 1, pending: 1, unreadable: 1 })
  })

  it('adds nothing up across projects', () => {
    // The guard, and the reason this test is worth its length: a total open count over
    // seventeen backlogs is the one number on the screen no `roadkeep` command could
    // print, which makes it the one somebody would quote and nobody could check. If a
    // field is ever added here, this fails.
    expect(Object.keys(tally(rows)).sort()).toEqual([
      'pending',
      'projects',
      'read',
      'unreadable',
    ])
  })
})
