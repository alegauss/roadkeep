import { describe, expect, it } from 'vitest'

import { accountOf, deferred, leftPointing, resumed, retired, shipped } from './leaving'
import { readDeferPayload, readResumePayload, readRetirePayload, readShipPayload } from './payloads'
import type { Reader } from './reading'
import { composeWrite } from './writing'

/** Captured from a real `ship --json`. */
const SHIP = {
  id: 'FX1',
  changelog: {
    file: 'docs/CHANGELOG.md',
    line: 5,
    rendered: '- ✅ **FX1** **nothing answers question 1 yet** — The read now answers.',
  },
  roadmap: { file: 'docs/ROADMAP.md', removed: 5 },
  part: '',
  remainder: '',
  improvements: {
    file: 'docs/IMPROVEMENTS.md',
    dropped: { anchor: 'FX1', title: 'Why question 1 needs answering', first: 5, last: 9 },
    nested: [],
    recorded_in: null,
    superseded: null,
  },
  refreshed: [],
  checked: [],
  unmet: [],
  decisions: null,
}

/** Captured from a real `retire --json`. */
const RETIRE = {
  id: 'FX2',
  marker: '🗑',
  superseded_by: null,
  folded: '',
  changelog: {
    file: 'docs/CHANGELOG.md',
    line: 6,
    rendered: '- 🗑 **FX2** **nothing answers question 2 yet** — abandoned: The premise went.',
  },
  roadmap: { file: 'docs/ROADMAP.md', removed: 5 },
  dropped: 'FX2',
  dependents: [],
  refreshed: [],
}

/** Captured from a real `defer --json`. */
const DEFER = {
  id: 'FX3',
  marker: '⏸',
  deferred: {
    file: 'docs/DEFERRED.md',
    line: 5,
    rendered: '- ⏸ **FX3** (deps: —) **nothing answers question 3 yet** — set aside (…): …',
  },
  roadmap: { file: 'docs/ROADMAP.md', removed: 5 },
  carried: {
    anchor: '§FX3',
    role: 'improvements',
    file: 'docs/IMPROVEMENTS.md',
    absence: null,
  },
  dependents: [],
  refreshed: [],
  wrote: ['docs/DEFERRED.md', 'docs/ROADMAP.md'],
}

/** Captured from a real `resume --json`. */
const RESUME = {
  id: 'FX3',
  marker: '📋',
  roadmap: {
    file: 'docs/ROADMAP.md',
    line: 6,
    rendered: '- 📋 **FX3** (deps: —) **nothing answers question 3 yet** — The 3th read …',
  },
  deferred: { file: 'docs/DEFERRED.md', removed: 5 },
  was: 'Waiting on a decision that is not this project.',
  reconciled: false,
  refreshed: [],
  wrote: ['docs/ROADMAP.md', 'docs/DEFERRED.md'],
}

function read<T>(reader: Reader<T>, raw: unknown): T {
  const parsed = reader(raw, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG31: the four ways a line leaves', () => {
  it('accounts for every file a ship touched', () => {
    const departure = shipped(read(readShipPayload, SHIP))

    expect(departure.how).toBe('shipped')
    expect(departure.edits.map((edit) => edit.file)).toEqual([
      'docs/CHANGELOG.md',
      'docs/ROADMAP.md',
      'docs/IMPROVEMENTS.md',
    ])
    expect(departure.edits[0]?.wrote).toBe(5)
    expect(departure.edits[1]?.removed).toBe(5)
    expect(departure.stillOpen).toBe(false)
  })

  it('reads a partial ship as a line that is still open', () => {
    // Captured from a real `ship --part`: the roadmap key is a different shape here — the
    // line stayed, with a new marker, and nothing was removed. A reader taking only
    // `removed` would draw this as a closure. There is no `improvements` key either,
    // because the section survives a partial.
    const departure = shipped(
      read(readShipPayload, {
        id: 'FX1',
        part: 'the local half',
        remainder: 'The half that needs an account somebody has to buy.',
        changelog: {
          file: 'docs/CHANGELOG.md',
          line: 5,
          rendered:
            '- ✅ **FX1 (the local half)** **nothing answers…** — The local half answers now.',
        },
        roadmap: { file: 'docs/ROADMAP.md', line: 5, status: '⏳', open: true, marked: true },
        refreshed: [],
      }),
    )

    expect(departure.stillOpen).toBe(true)
    expect(departure.edits).toEqual([
      { file: 'docs/CHANGELOG.md', wrote: 5, removed: null },
      { file: 'docs/ROADMAP.md', wrote: 5, removed: null },
    ])
    expect(accountOf(departure)).toBe(
      'FX1 shipped: docs/CHANGELOG.md:5 written, docs/ROADMAP.md:5 written',
    )
  })

  it('reads a full ship as the line taken out, under the same key', () => {
    const departure = shipped(read(readShipPayload, SHIP))

    expect(departure.stillOpen).toBe(false)
    expect(departure.edits[1]).toEqual({ file: 'docs/ROADMAP.md', wrote: null, removed: 5 })
  })

  it('names the decision a ship filed, where one was named', () => {
    const departure = shipped(
      read(readShipPayload, {
        ...SHIP,
        decisions: { file: 'docs/DECISIONS.md', line: 12, rendered: '- A constraint.' },
      }),
    )

    expect(departure.edits.map((edit) => edit.file)).toContain('docs/DECISIONS.md')
  })

  it('accounts for a retire, which records a departure without a ship', () => {
    const departure = retired(read(readRetirePayload, RETIRE))

    expect(departure.how).toBe('retired')
    expect(departure.rendered).toContain('abandoned')
    expect(departure.stillOpen).toBe(false)
  })

  it('reads a defer as set aside and not closed', () => {
    // The id, the deps, the symptom and the section all survive a pause.
    const departure = deferred(read(readDeferPayload, DEFER))

    expect(departure.how).toBe('deferred')
    expect(departure.stillOpen).toBe(true)
    expect(departure.edits.map((edit) => edit.file)).toEqual([
      'docs/DEFERRED.md',
      'docs/ROADMAP.md',
    ])
  })

  it('reads a resume as the line coming back, with the reason it stood on', () => {
    const payload = read(readResumePayload, RESUME)
    const departure = resumed(payload)

    expect(departure.how).toBe('resumed')
    expect(departure.stillOpen).toBe(true)
    // The one place a pause's own sentence is published apart from the design's why.
    expect(payload.was).toBe('Waiting on a decision that is not this project.')
  })
})

describe('RG31: what a departure leaves behind', () => {
  it('names the lines still pointing at a retired id', () => {
    // The resolver reads a retired dep as never, so none of these becomes ready by
    // anything happening to this id.
    const departure = retired(read(readRetirePayload, { ...RETIRE, dependents: ['FX7', 'FX8'] }))

    expect(leftPointing(departure)).toContain('FX7, FX8')
    expect(leftPointing(departure)).toContain('2 line(s)')
  })

  it('says nothing where nothing pointed at it', () => {
    expect(leftPointing(retired(read(readRetirePayload, RETIRE)))).toBe('')
  })

  it('says what was written where, in the engine own file names', () => {
    expect(accountOf(shipped(read(readShipPayload, SHIP)))).toBe(
      'FX1 shipped: docs/CHANGELOG.md:5 written, docs/ROADMAP.md:5 removed, docs/IMPROVEMENTS.md:5 removed',
    )
  })

  it('says so plainly when a write touched nothing', () => {
    const departure = shipped(
      read(readShipPayload, { ...SHIP, changelog: null, roadmap: null, improvements: null }),
    )

    expect(accountOf(departure)).toBe('FX1: nothing was written')
  })
})

describe('RG31: each verb is one command, and the sentence is the person own', () => {
  it('composes a ship with the outcome and what the design left behind', () => {
    const composed = composeWrite('/w', 'ship', {
      id: 'RG31',
      why: 'The four doors exist.',
      recordedIn: 'packages/core/src/leaving.ts',
      checked: ['A write is one command, shown before it runs'],
    })

    expect(composed.argv).toEqual([
      '-C',
      '/w',
      'ship',
      'RG31',
      '--why',
      'The four doors exist.',
      '--recorded-in',
      'packages/core/src/leaving.ts',
      '--checked',
      'A write is one command, shown before it runs',
      '--json',
    ])
  })

  it('composes a partial ship with the half that landed and the rest', () => {
    const composed = composeWrite('/w', 'ship', {
      id: 'RG31',
      why: 'Half of it.',
      part: 'the store, read',
      remainder: 'The other half.',
    })

    expect(composed.argv).toContain('--part')
    expect(composed.argv).toContain('--remainder')
  })

  it('composes a retire as a replacement or an abandonment', () => {
    expect(composeWrite('/w', 'retire', { id: 'RG7', supersededBy: 'RG9' }).argv).toContain(
      '--superseded-by',
    )
    expect(composeWrite('/w', 'retire', { id: 'RG7', reason: 'It went.' }).argv).not.toContain(
      '--superseded-by',
    )
  })

  it('composes a defer and a resume with what each takes', () => {
    expect(composeWrite('/w', 'defer', { id: 'RG7', reason: 'Waiting.' }).argv).toEqual([
      '-C',
      '/w',
      'defer',
      'RG7',
      '--reason',
      'Waiting.',
      '--json',
    ])
    // The marker is optional: omitted, the project's first declared one is used, because
    // the store keeps one marker and which it was is not a fact any file held.
    expect(composeWrite('/w', 'resume', { id: 'RG7' }).argv).toEqual([
      '-C',
      '/w',
      'resume',
      'RG7',
      '--json',
    ])
  })
})
