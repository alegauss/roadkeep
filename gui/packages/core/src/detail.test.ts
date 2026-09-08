import { describe, expect, it } from 'vitest'

import { designOf, detailFrom, whyNotStartable } from './detail'
import { readBriefPayload, type BriefPayload } from './payloads'

/** Captured from a real `brief --json`, trimmed to the keys the shape declares. */
const RAW = {
  id: 'RG23',
  status: '🛠',
  block: 'D',
  shipped: false,
  file: 'docs/ROADMAP.md',
  line: 28,
  rendered: '- 🛠 **RG23** …',
  symptom: 'a task has no detail',
  why: 'brief joins everything into one read, and nothing calls it.',
  deps: ['RG21 ✅'],
  requires: [],
  ref: 'RG23',
  section: {
    anchor: 'RG23',
    title: 'One read, and the whole cost of starting',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 240,
    last: 248,
    words: 89,
    own_words: 89,
    body: 'The detail is the brief payload and nothing beside it.',
  },
  section_absence: '',
  readiness: 'ready',
  picked: 'lowest ready id',
  deps_resolved: [{ dep: 'RG21', kind: 'task', status: 'shipped', detail: 'in the changelog' }],
  unblocks: { count: 15, of: 49, transitive: ['RG24', 'RG25'], transitive_elided: 11 },
  non_goals: ['No Markdown parsed in this app', 'No write to a governed file'],
  non_goals_elided: 0,
  done_when: ['A task opens with everything starting it costs'],
  done_when_elided: 0,
  held: [],
  landed: [],
}

function brief(over: Record<string, unknown> = {}): BriefPayload {
  const parsed = readBriefPayload({ ...RAW, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG23: one read carries the whole cost of starting', () => {
  it('reads a real brief without composing anything', () => {
    const detail = detailFrom(brief())

    expect(detail.payload.id).toBe('RG23')
    expect(detail.payload.why).toContain('one read')
    expect(detail.payload.doneWhen).toHaveLength(1)
    expect(detail.payload.nonGoals).toHaveLength(2)
  })

  it('carries each dep with what resolves it, not just an id', () => {
    const detail = detailFrom(brief())

    expect(detail.payload.depsResolved[0]).toEqual({
      dep: 'RG21',
      kind: 'task',
      status: 'shipped',
      detail: 'in the changelog',
    })
  })

  it('carries what shipping it would unblock', () => {
    const detail = detailFrom(brief())

    expect(detail.payload.unblocks?.count).toBe(15)
    expect(detail.payload.unblocks?.transitiveElided).toBe(11)
  })

  it('carries the design section whole', () => {
    const detail = detailFrom(brief())

    expect(detail.hasDesign).toBe(true)
    expect(designOf(detail)).toBe('The detail is the brief payload and nothing beside it.')
  })

  it('shows the prose exactly as the file stores it', () => {
    // Not parsed, not re-wrapped. Parsing Markdown is a non-goal, and re-wrapping prose
    // written to a column is how a design stops reading the way it was written.
    const body = 'A line.\n\nAnother paragraph, with **bold** and a `code span` in it.\n'
    const detail = detailFrom(brief({ section: { ...RAW.section, body } }))

    expect(designOf(detail)).toBe(body)
  })
})

describe('RG23: readiness is never derived', () => {
  it('takes the engine word rather than working one out', () => {
    expect(detailFrom(brief({ readiness: 'ready' })).startable).toBe(true)
    expect(detailFrom(brief({ readiness: 'blocked' })).startable).toBe(false)
    expect(detailFrom(brief({ readiness: 'waiting' })).startable).toBe(false)
  })

  it('does not call a line ready because its deps look settled', () => {
    // Every dep shipped, and the engine still says blocked. The engine wins: it knows
    // about deps outside this backlog and this app does not.
    const detail = detailFrom(brief({ readiness: 'blocked' }))

    expect(detail.blocking).toEqual([])
    expect(detail.startable).toBe(false)
  })

  it('names the deps that are not settled', () => {
    const detail = detailFrom(
      brief({
        readiness: 'blocked',
        deps_resolved: [
          { dep: 'RG21', kind: 'task', status: 'shipped', detail: '' },
          { dep: 'RG40', kind: 'task', status: 'open', detail: 'in the roadmap' },
          { dep: 'roadkeep RK1631', kind: 'outside', status: 'unknown', detail: '' },
        ],
      }),
    )

    expect(detail.blocking).toEqual(['RG40', 'roadkeep RK1631'])
  })

  it('counts a retired dep as settled, because the resolver reads it as never', () => {
    // Treating retirement as still-blocking holds a line back for a task that is never
    // coming.
    const detail = detailFrom(
      brief({
        deps_resolved: [{ dep: 'RG70', kind: 'task', status: 'retired', detail: '' }],
      }),
    )

    expect(detail.blocking).toEqual([])
  })
})

describe('RG23: whether anybody is holding it', () => {
  it('is not startable while a worker holds it', () => {
    const detail = detailFrom(
      brief({
        held: [{ by: 'another session', since: '10 minutes ago', state: 'held', paths: [] }],
      }),
    )

    expect(detail.startable).toBe(false)
    expect(whyNotStartable(detail)).toContain('another session')
  })

  it('says nothing when the line is free', () => {
    expect(whyNotStartable(detailFrom(brief()))).toBe('')
  })

  it('names what it is waiting on when nobody holds it', () => {
    const detail = detailFrom(
      brief({
        readiness: 'blocked',
        deps_resolved: [{ dep: 'RG40', kind: 'task', status: 'open', detail: '' }],
      }),
    )

    expect(whyNotStartable(detail)).toBe('waiting on RG40')
  })

  it('names an absent requirement when that is what is missing', () => {
    const detail = detailFrom(brief({ readiness: 'waiting', requires: ['signing-cert'] }))

    expect(whyNotStartable(detail)).toBe('needs signing-cert')
  })

  it('falls back to the engine own word when it cannot say more', () => {
    const detail = detailFrom(brief({ readiness: 'set aside', deps_resolved: [] }))

    expect(whyNotStartable(detail)).toBe('set aside')
  })
})

describe('RG23: a brief that left something out', () => {
  it('is complete only when nothing at all was elided', () => {
    const detail = detailFrom(brief({ unblocks: { ...RAW.unblocks, transitive_elided: 0 } }))

    expect(detail.narrowing.complete).toBe(true)
    expect(detail.narrowing.reasons).toEqual([])
  })

  it('says so when the non-goals were sampled rather than listed', () => {
    // A screen drawing the listed non-goals as the whole list shows a constraint set
    // missing exactly the entries nobody thought to look for.
    const detail = detailFrom(
      brief({ non_goals_elided: 4, unblocks: { ...RAW.unblocks, transitive_elided: 0 } }),
    )

    expect(detail.narrowing.complete).toBe(false)
    expect(detail.narrowing.reasons[0]).toContain('4 non-goal')
  })

  it('says so when what it unblocks was sampled', () => {
    // The ordinary case for a well-connected line: two ids listed and eleven not. A
    // screen showing the two as the set would understate the blast radius of a ship.
    const detail = detailFrom(brief())

    expect(detail.payload.unblocks?.transitive).toHaveLength(2)
    expect(detail.payload.unblocks?.transitiveElided).toBe(11)
    expect(detail.narrowing.complete).toBe(false)
    expect(detail.narrowing.reasons.join(' ')).toContain('11 id')
  })
})

describe('RG23: whether there was a choice to explain', () => {
  it('carries the reason when the engine chose the line', () => {
    expect(detailFrom(brief()).payload.picked).toBe('lowest ready id')
  })

  it('is null when the caller named an id, because nothing was chosen', () => {
    // Not an empty string. A shape expecting one failed on every id this app looks up by
    // name, which is most of them.
    expect(detailFrom(brief({ picked: null })).payload.picked).toBeNull()
  })
})

describe('RG23: a line whose pointer resolves to nothing', () => {
  it('has no design and carries the engine sentence about it', () => {
    const detail = detailFrom(
      brief({ section: null, section_absence: 'no section under RG23 in docs/IMPROVEMENTS.md' }),
    )

    expect(detail.hasDesign).toBe(false)
    expect(designOf(detail)).toBeNull()
    expect(detail.payload.sectionAbsence).toContain('no section')
  })
})
