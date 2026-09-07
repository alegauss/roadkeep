import { describe, expect, it } from 'vitest'

import { aboutNoInput, movedFrom, openMarkers, saidOfMove } from './marking'
import {
  readConfigPayload,
  readStatusPayload,
  type ConfigPayload,
  type StatusPayload,
} from './payloads'
import { readRefusal, type Refusal } from './refusals'
import { composeWrite } from './writing'

/** Captured from a real `status <id> 🛠 --json`. */
const MOVED = {
  id: 'FX3',
  from: '📋',
  to: '🛠',
  changed: true,
  file: 'docs/ROADMAP.md',
  line: 6,
  rendered: '- 🛠 **FX3** (deps: —) **nothing answers question 3 yet** — …',
  refreshed: [],
  claim: 'claimed',
  wrote: ['docs/ROADMAP.md'],
}

function moved(over: Record<string, unknown> = {}): StatusPayload {
  const parsed = readStatusPayload({ ...MOVED, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function refusal(over: Record<string, unknown> = {}): Refusal {
  const parsed = readRefusal({ refused: [], beside: '', about: '', said: 'no.', ...over }, '')
  if (!parsed.ok) throw new Error('the fixture does not match the shape')
  return parsed.value
}

function config(keys: { address: string; set: string | null }[]): ConfigPayload {
  const parsed = readConfigPayload(
    {
      version: '0.2.388',
      source: 'roadkeep.toml',
      keys: keys.map((key) => ({
        table: key.address.split('.')[0],
        key: key.address.split('.')[1],
        address: key.address,
        declared: key.set !== null,
        set: key.set,
      })),
    },
    '',
  )
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG30: the markers offered are the ones the project declared', () => {
  it('reads the open set out of config rather than naming one', () => {
    // Four emoji in this repository and something else in the next one. A literal here is
    // the rule compiled into the client the non-goals refuse.
    const declared = config([
      { address: 'markers.open', set: '["📋", "💭", "⏳", "🛠"]' },
      { address: 'markers.shipped', set: '"✅"' },
    ])

    expect(openMarkers(declared)).toEqual(['📋', '💭', '⏳', '🛠'])
  })

  it('offers no shipped or retired marker, because those are other verbs', () => {
    const declared = config([
      { address: 'markers.open', set: '["📋"]' },
      { address: 'markers.shipped', set: '"✅"' },
      { address: 'markers.retired', set: '"🗑"' },
    ])

    expect(openMarkers(declared)).toEqual(['📋'])
  })

  it('offers nothing for a project that declares no open set', () => {
    expect(openMarkers(config([{ address: 'markers.shipped', set: '"✅"' }]))).toEqual([])
    expect(openMarkers(config([{ address: 'markers.open', set: null }]))).toEqual([])
  })

  it('takes a single marker the file spells without a list', () => {
    expect(openMarkers(config([{ address: 'markers.open', set: '"📋"' }]))).toEqual(['📋'])
  })
})

describe('RG30: a marker write is one command', () => {
  it('sends the id and the marker as the two arguments the verb takes', () => {
    const composed = composeWrite('/w', 'status', { id: 'RG30', marker: '🛠' })

    expect(composed.argv).toEqual(['-C', '/w', 'status', 'RG30', '🛠', '--json'])
  })
})

describe('RG30: what moved with the marker', () => {
  it('says the claim the write took, in the engine word', () => {
    const one = movedFrom(moved())

    expect(one.changed).toBe(true)
    expect(one.claim).toBe('claimed')
    expect(saidOfMove(one)).toBe('📋 → 🛠, and the line is yours')
  })

  it('says the claim it gave back when the marker moves off working', () => {
    const one = movedFrom(moved({ from: '🛠', to: '📋', claim: 'released' }))

    expect(one.claim).toBe('released')
    expect(saidOfMove(one)).toBe('🛠 → 📋, and the claim is given back')
  })

  it('says neither where the move touched no claim', () => {
    const one = movedFrom(moved({ from: '📋', to: '💭', claim: null }))

    expect(one.claim).toBe('neither')
    expect(saidOfMove(one)).toBe('📋 → 💭')
  })

  it('reads a word it has never seen as no claim change, rather than passing it on', () => {
    // The one field a screen branches on. A fourth answer should draw as no change and
    // never as a state with no rendering.
    expect(movedFrom(moved({ claim: 'reassigned' })).claim).toBe('neither')
  })

  it('reads a marker already set as an answer and not a failure', () => {
    // The line still followed its claim and still has a standing to report.
    const one = movedFrom(moved({ from: '🛠', to: '🛠', changed: false, claim: 'claimed' }))

    expect(one.changed).toBe(false)
    expect(saidOfMove(one)).toBe('already 🛠, and the line is yours')
  })

  it('carries the ids whose dep annotations were re-derived', () => {
    expect(movedFrom(moved({ refreshed: ['RG41', 'RG42'] })).refreshed).toEqual(['RG41', 'RG42'])
    expect(movedFrom(moved()).wrote).toEqual(['docs/ROADMAP.md'])
  })
})

describe('RG30: a refusal about a person, not an input', () => {
  it('marks no box when the engine named no field', () => {
    // A live claim names nobody and may be the caller's own, so there is nothing to
    // highlight — and a screen hunting for a field would pick one at random.
    const held = refusal({
      said: 'RG30 was claimed 14m ago and a claim names nobody, so it may be yours: read it without --claim, or move the marker off 🛠 to release it',
    })

    expect(aboutNoInput(held)).toBe(true)
    expect(held.said).toContain('may be yours')
  })

  it('marks the box when the engine did name a field', () => {
    const tooLong = refusal({
      refused: [{ code: 'symptom.too-long', field: 'symptom', bound: '', message: 'too long' }],
      said: 'refused',
    })

    expect(aboutNoInput(tooLong)).toBe(false)
  })

  it('asks whether a field was named, and never reads the sentence for one', () => {
    // The sentence mentions `symptom` and the engine named nothing. The answer is still
    // that there is no box: the code is the contract and the prose is not.
    const held = refusal({ said: 'the symptom is fine; somebody else holds this line' })

    expect(aboutNoInput(held)).toBe(true)
  })
})
