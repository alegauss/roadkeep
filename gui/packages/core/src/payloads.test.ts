import { describe, expect, it } from 'vitest'

import {
  narrowingOfList,
  narrowingOfStats,
  readListPayload,
  readLintPayload,
  readShowPayload,
  readStatsPayload,
} from './payloads'

/**
 * Captured from a real `roadkeep <verb> --json`, trimmed to the keys these shapes declare
 * plus a few they do not, so the "extra keys are allowed" rule is exercised by the same
 * fixtures. Whether the real command still prints this is RG4's question, asked against a
 * live engine; these hold the shapes themselves.
 */
const LIST = {
  file: 'docs/ROADMAP.md',
  total: 9,
  uncounted: [],
  standing: { block: 'A', state: 'live', sentence: 'Block A has 9 open', open: 9, recorded: 2, paused: 0 },
  startable: { open: 9, startable: 9, waiting: 0, absent: [] },
  over: null,
  tasks: [
    {
      id: 'RG3',
      status: '🛠',
      block: 'A',
      symptom: 'a payload arrives as any',
      why: 'The shape comes off a build this app did not choose.',
      deps: ['RG1 ✅'],
      ref: 'RG3',
      line: 7,
      length: 274,
    },
  ],
}

const STATS = {
  file: 'docs/ROADMAP.md',
  total: 60,
  uncounted: 0,
  markers: { '📋': 11, '💭': 48, '🛠': 1 },
  startable: {
    open: 60,
    startable: 58,
    waiting: 2,
    absent: [{ requirement: 'signing-cert', lines: 1 }],
  },
  blocks: [{ block: 'A', counted: 9, uncounted: 0, markers: { '📋': 3 } }],
}

const SHOW = {
  id: 'RG3',
  status: '🛠',
  block: 'A',
  shipped: false,
  file: 'docs/ROADMAP.md',
  line: 7,
  rendered: '- 🛠 **RG3** …',
  lines: ['- 🛠 **RG3** …'],
  wrapped: false,
  symptom: 'a payload arrives as any',
  why: 'The shape comes off a build this app did not choose.',
  deps: ['RG1 ✅'],
  requires: [],
  ref: 'RG3',
  section: {
    anchor: 'RG3',
    title: 'Types that come off the tool, not off a guess',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 5,
    last: 29,
    words: 247,
    own_words: 247,
    body: 'A payload is JSON with no published schema…',
  },
  section_absence: '',
  paths: [],
}

const LINT = {
  root: 'D:/Git/alegauss/roadkeep-gui',
  clean: true,
  fixed: [],
  kept: [],
  refused: [],
  checked: ['docs/ROADMAP.md'],
  lines: 67,
  sections: 62,
  budgets: 0,
  problems: 0,
  codes: {},
  findings: [],
  notes: [
    {
      code: 'engine.disagreement',
      file: '.',
      line: null,
      id: null,
      message: 'this gate is 0.2.349…',
      remedy: { kind: 'read', doors: [] },
    },
  ],
}

describe('RG3: the shapes this app reads', () => {
  it('reads a listing, its standing and its task lines', () => {
    const parsed = readListPayload(LIST, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.standing?.sentence).toBe('Block A has 9 open')
    expect(parsed.value.tasks[0]?.id).toBe('RG3')
    expect(parsed.value.tasks[0]?.deps).toEqual(['RG1 ✅'])
  })

  it('reads counts keyed by a marker set it cannot know in advance', () => {
    const parsed = readStatsPayload(STATS, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.markers['💭']).toBe(48)
    expect(parsed.value.startable?.waiting).toBe(2)
    expect(parsed.value.blocks[0]?.block).toBe('A')
  })

  it('reads the same key as two different types under two verbs', () => {
    // `uncounted` is a list of lines under `list` and a count under `stats`. One shared
    // shape would have quietly read one of them wrong.
    const listed = readListPayload(LIST, '')
    const counted = readStatsPayload(STATS, '')

    expect(listed.ok && Array.isArray(listed.value.uncounted)).toBe(true)
    expect(counted.ok && typeof counted.value.uncounted).toBe('number')
  })

  it('reads a task with its rationale section', () => {
    const parsed = readShowPayload(SHOW, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.section?.words).toBe(247)
    expect(parsed.value.sectionAbsence).toBe('')
  })

  it('reads a section whose prose was not asked for', () => {
    // `show --no-body` keeps the section and drops what it says. Null, not empty: a
    // section that exists and says nothing is a defect and this is not.
    const parsed = readShowPayload({ ...SHOW, section: { ...SHOW.section, body: null } }, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.section?.body).toBeNull()
    expect(parsed.value.section?.file).toContain('IMPROVEMENTS.md')
  })

  it('reads a ledger line, which points at no rationale', () => {
    // Shipping deletes the design, so `ref` comes back null. A shape written as `string`
    // read the roadmap fine and failed on the changelog.
    const parsed = readListPayload(
      { ...LIST, tasks: [{ ...LIST.tasks[0], status: '✅', ref: null }] },
      '',
    )

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.tasks[0]?.ref).toBeNull()
  })

  it('reads a pointer that resolves to nothing as a state, not a failure', () => {
    const parsed = readShowPayload(
      { ...SHOW, section: null, section_absence: 'no section under RG3' },
      '',
    )

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.section).toBeNull()
    expect(parsed.value.sectionAbsence).toContain('no section')
  })

  it('reads the gate, including the notes it makes without failing', () => {
    const parsed = readLintPayload(LINT, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.clean).toBe(true)
    expect(parsed.value.notes[0]?.code).toBe('engine.disagreement')
    expect(parsed.value.notes[0]?.line).toBeNull()
  })

  it('refuses a task line whose symptom was renamed', () => {
    const parsed = readListPayload(
      { ...LIST, tasks: [{ ...LIST.tasks[0], symptom: undefined }] },
      '',
    )

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.path).toBe('tasks[0].symptom')
  })
})

describe('RG3: an answer that is narrower than the file', () => {
  it('says a listing is complete when nothing was left out', () => {
    const parsed = readListPayload(LIST, '')
    expect(parsed.ok && narrowingOfList(parsed.value).complete).toBe(true)
  })

  it('says a listing is narrowed when lines were not accepted, and why', () => {
    // Rendering this as a complete answer shows less than there is and says nothing about
    // it, which leaves the reader no way to know.
    const parsed = readListPayload({ ...LIST, uncounted: ['- ?? **RG99** …'] }, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    const narrowing = narrowingOfList(parsed.value)
    expect(narrowing.complete).toBe(false)
    expect(narrowing.reasons[0]).toContain('1 marker-bearing line')
  })

  it('says the same about a count', () => {
    const parsed = readStatsPayload({ ...STATS, uncounted: 3 }, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(narrowingOfStats(parsed.value).complete).toBe(false)
    expect(narrowingOfStats(parsed.value).reasons[0]).toContain('3 marker-bearing line')
  })
})
