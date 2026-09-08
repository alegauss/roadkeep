import { describe, expect, it } from 'vitest'

import { buildArgv } from './client'
import { claimingBrief, handoverOf, heldBy, mayHandOver, saidOfHandover } from './handover'
import { readBriefPayload, type BriefPayload } from './payloads'

/** Captured from a real `brief <id> --claim --json`. */
const RAW = {
  id: 'RG41',
  status: '🛠',
  block: 'F',
  symptom: 'a line is handed over without being taken',
  why: 'brief --claim answers and moves the marker in one transaction.',
  deps: ['RG30 ✅', 'RG38 ✅'],
  requires: [],
  ref: 'RG41',
  section: null,
  section_absence: '',
  readiness: 'ready',
  picked: null,
  deps_resolved: [],
  unblocks: { count: 0, of: 43, transitive: [], transitive_elided: 0 },
  non_goals: [],
  non_goals_elided: 0,
  done_when: [],
  done_when_elided: 0,
  held: [],
  landed: [],
  claimed: { taken: true, from: '💭', to: '🛠' },
}

function brief(over: Record<string, unknown> = {}): BriefPayload {
  const parsed = readBriefPayload({ ...RAW, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG41: the read that takes the line', () => {
  it('asks for the claim in the same call that reads the brief', () => {
    // No window between reading and taking: the tier that chose the line and the
    // transaction that took it are one call.
    expect(buildArgv('/w', 'brief', claimingBrief())).toEqual([
      '-C',
      '/w',
      'brief',
      '--claim',
      '--json',
    ])
    expect(buildArgv('/w', 'brief', claimingBrief('RG41'))).toEqual([
      '-C',
      '/w',
      'brief',
      'RG41',
      '--claim',
      '--json',
    ])
  })

  it('reads what the claim did to the marker', () => {
    const handover = handoverOf(brief())

    expect(handover.taken).toBe(true)
    expect(handover.from).toBe('💭')
    expect(handover.to).toBe('🛠')
    expect(saidOfHandover(handover)).toBe('RG41 taken: 💭 → 🛠')
  })

  it('says a brief that only read was not a taking', () => {
    // `claimed` is null on a brief without the flag. A screen that read that as taken
    // would report a line as this session's when nothing moved.
    const handover = handoverOf(brief({ claimed: null }))

    expect(handover.taken).toBe(false)
    expect(saidOfHandover(handover)).toBe('RG41 was read and not taken')
  })

  it('says nothing moved where the line already carried the marker', () => {
    const handover = handoverOf(brief({ claimed: { taken: false, from: '🛠', to: '🛠' } }))

    expect(handover.taken).toBe(false)
  })
})

describe('RG41: a held line is named before a second session is offered it', () => {
  it('offers a ready line nobody is on', () => {
    expect(mayHandOver(handoverOf(brief()))).toBe(true)
    expect(heldBy(handoverOf(brief()))).toBe('')
  })

  it('withholds one somebody is on, and names them', () => {
    const handover = handoverOf(
      brief({
        held: [{ by: 'another session', since: '14m', state: 'held', paths: [] }],
      }),
    )

    expect(mayHandOver(handover)).toBe(false)
    expect(heldBy(handover)).toBe('RG41 is held by another session since 14m')
  })

  it('still names a holder that named nobody, rather than offering the line as free', () => {
    // A claim names nobody, so this is the ordinary case and not the exception.
    const handover = handoverOf(brief({ held: [{ by: '', since: '3m', state: '', paths: [] }] }))

    expect(heldBy(handover)).toBe('RG41 is held by another worker since 3m')
    expect(mayHandOver(handover)).toBe(false)
  })

  it('withholds a line the engine does not call ready, whatever its marker says', () => {
    // Readiness is carried, never worked out. RG74's point: the marker is not the claim
    // and neither is a proxy for the other.
    expect(mayHandOver(handoverOf(brief({ readiness: 'blocked' })))).toBe(false)
    expect(mayHandOver(handoverOf(brief({ readiness: 'waiting' })))).toBe(false)
  })

  it('reads a line carrying the working marker with nobody on it as offerable', () => {
    // Started and left, its claim expired. The marker alone must not make it look taken.
    const handover = handoverOf(brief({ status: '🛠', held: [], readiness: 'ready' }))

    expect(mayHandOver(handover)).toBe(true)
  })
})
