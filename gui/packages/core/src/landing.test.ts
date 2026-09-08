import { describe, expect, it } from 'vitest'

import { changeLine, landingBetween, saidButNotDone, type Reading } from './landing'
import { readBriefPayload } from './payloads'
import { readRefusal } from './refusals'

/** Captured from a real `brief --json` on an open line. */
const OPEN = {
  id: 'RG42',
  status: '🛠',
  shipped: false,
  block: 'F',
  symptom: 'what a session wrote is not watched',
  why: 'An agent ships through the same verbs a person does.',
  deps: ['RG38 ✅', 'RG45 ✅'],
  requires: [],
  ref: 'RG42',
  section: {
    anchor: 'RG42',
    title: 'What the session did, beside what it said',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 491,
    last: 499,
    words: 86,
    own_words: 86,
    body: 'An agent writes through the same verbs a person does.',
  },
  section_absence: '',
  readiness: 'ready',
  picked: null,
  deps_resolved: [],
  unblocks: { count: 0, of: 40, transitive: [], transitive_elided: 0 },
  non_goals: [],
  non_goals_elided: 0,
  done_when: [],
  done_when_elided: 0,
  held: [],
  landed: [],
}

function reading(over: Record<string, unknown> = {}): Reading {
  const parsed = readBriefPayload({ ...OPEN, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return { kind: 'read', payload: parsed.value }
}

function gone(said: string): Reading {
  const parsed = readRefusal({ refused: [], beside: '', about: '', said }, '')
  if (!parsed.ok) throw new Error('the fixture does not match the shape')
  return { kind: 'gone', refusal: parsed.value }
}

describe('RG42: one re-read answers all of it', () => {
  it('sees nothing where nothing moved', () => {
    const landing = landingBetween(reading(), reading())

    expect(landing.moved).toBe(false)
    expect(landing.changes).toEqual([])
  })

  it('sees the marker move', () => {
    const landing = landingBetween(reading({ status: '📋' }), reading({ status: '🛠' }))

    expect(landing.moved).toBe(true)
    expect(landing.changes).toEqual([{ kind: 'marker', from: '📋', to: '🛠' }])
    expect(changeLine(landing.changes[0]!)).toBe('📋 → 🛠')
  })

  it('sees the design appear, and the ship that deletes it', () => {
    const written = landingBetween(reading({ section: null }), reading())
    expect(changeLine(written.changes[0]!)).toBe('design written')

    const deleted = landingBetween(reading(), reading({ section: null }))
    expect(changeLine(deleted.changes[0]!)).toBe('design deleted')
  })

  it('sees the line leave for the ledger, off the engine own word', () => {
    // Carried, not inferred from the marker: a shipped id still briefs.
    const landing = landingBetween(
      reading(),
      reading({ shipped: true, status: '✅', section: null }),
    )

    expect(landing.changes.map((change) => change.kind)).toEqual([
      'marker',
      'shipped',
      'design',
    ])
    expect(changeLine(landing.changes[1]!)).toBe('shipped, and in the ledger')
  })

  it('sees a symptom restated and a why amended', () => {
    const landing = landingBetween(
      reading(),
      reading({ symptom: 'a different claim', why: 'A different sentence.' }),
    )

    expect(landing.changes.map((change) => change.kind)).toEqual(['symptom', 'why'])
    expect(changeLine(landing.changes[0]!)).toBe('symptom restated')
  })

  it('sees a dep added and one dropped, naming both', () => {
    const landing = landingBetween(
      reading({ deps: ['RG38 ✅'] }),
      reading({ deps: ['RG38 ✅', 'RG45 ✅'] }),
    )

    expect(landing.changes).toEqual([{ kind: 'deps', added: ['RG45 ✅'], dropped: [] }])
    expect(changeLine(landing.changes[0]!)).toBe('deps +RG45 ✅')

    const both = landingBetween(reading({ deps: ['RG1'] }), reading({ deps: ['RG2'] }))
    expect(changeLine(both.changes[0]!)).toBe('deps +RG2 -RG1')
  })
})

describe('RG42: a read that refuses is an answer too', () => {
  it('reads a line that stopped briefing as having left, in the engine sentence', () => {
    // Deferred, retired, renumbered away. Reading the sentence for meaning is not this
    // app's business; showing it is.
    const said = 'roadkeep: no task RG42 in docs/ROADMAP.md: RG42 is paused in docs/DEFERRED.md:5'
    const landing = landingBetween(reading(), gone(said))

    expect(landing.moved).toBe(true)
    expect(landing.changes).toEqual([{ kind: 'left', said }])
    expect(changeLine(landing.changes[0]!)).toBe(said)
  })

  it('reads a line that started briefing again as coming back', () => {
    const landing = landingBetween(gone('paused'), reading({ status: '📋' }))

    expect(landing.moved).toBe(true)
    expect(changeLine(landing.changes[0]!)).toBe('marker 📋')
    expect(landing.id).toBe('RG42')
  })
})

describe('RG42: beside the stream, not inside it', () => {
  it('names a session that said it shipped where the files did not', () => {
    // A session can report shipping a line it did not ship, and the files settle it.
    const landing = landingBetween(reading(), reading({ status: '⏳' }))

    expect(saidButNotDone(true, landing)).toBe(true)
  })

  it('agrees where the files agree', () => {
    const landing = landingBetween(reading(), reading({ shipped: true, status: '✅' }))

    expect(saidButNotDone(true, landing)).toBe(false)
  })

  it('claims nothing about a session that claimed nothing', () => {
    expect(saidButNotDone(false, landingBetween(reading(), reading()))).toBe(false)
  })
})
