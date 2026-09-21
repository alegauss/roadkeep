import { describe, expect, it } from 'vitest'

import type { UnvalidatedEntry, UnvalidatedPayload } from './payloads'
import { awaiting, validationFrom } from './validation'

/**
 * RG293: one payload, four screens.
 *
 * An empty list is three of them and only `governed` and `placed` tell them apart, so the whole
 * of this is that the reader keeps them apart — a tab reading the list alone would draw *this
 * project never asked* and *everything has a verdict* as the same thing.
 */

const ROW = (id: string, block: string): UnvalidatedEntry => ({
  id,
  block,
  symptom: `${id} shipped and nobody looked`,
  line: 10,
  commit: null,
})

const PAYLOAD: UnvalidatedPayload = {
  file: 'docs/CHANGELOG.md',
  block: null,
  governed: true,
  placed: true,
  from: null,
  validated: 2,
  unvalidated: [ROW('AL1', 'A'), ROW('AL2', 'A'), ROW('AL9', 'B')],
}

describe('RG293: what awaits a person', () => {
  it('reads the rows newest first, which is the ledger read from its end', () => {
    const validation = validationFrom(PAYLOAD)

    expect(validation.kind).toBe('awaiting')
    if (validation.kind !== 'awaiting') throw new Error(validation.kind)
    expect(validation.rows.map((row) => row.id)).toEqual(['AL9', 'AL2', 'AL1'])
    expect(validation.validated).toBe(2)
    expect(awaiting(validation)).toBe(3)
  })

  it('leaves the payload as it was, since a listing is read more than once', () => {
    validationFrom(PAYLOAD)

    expect(PAYLOAD.unvalidated.map((row) => row.id)).toEqual(['AL1', 'AL2', 'AL9'])
  })

  it('tells the three empty lists apart, which is what only two fields can do', () => {
    // Not asked at all: this project declares no `[validation]`.
    expect(validationFrom({ ...PAYLOAD, governed: false, unvalidated: [] })).toEqual({
      kind: 'ungoverned',
    })
    // Asked, and the history cannot say where looking starts.
    expect(validationFrom({ ...PAYLOAD, placed: false, unvalidated: [] })).toEqual({
      kind: 'unplaced',
    })
    // Asked and answered, which is the screen the whole block exists to produce.
    expect(validationFrom({ ...PAYLOAD, unvalidated: [] })).toEqual({ kind: 'none', validated: 2 })
  })

  it('says nothing awaits anybody in every state but one', () => {
    for (const payload of [
      { ...PAYLOAD, governed: false, unvalidated: [] },
      { ...PAYLOAD, placed: false, unvalidated: [] },
      { ...PAYLOAD, unvalidated: [] },
    ]) {
      expect(awaiting(validationFrom(payload))).toBe(0)
    }
  })

  it('reads an ungoverned project as that even where a list somehow came back', () => {
    // The fields decide, not the length: a project that is not asking the question is not
    // asking it, whatever else the payload carries.
    expect(validationFrom({ ...PAYLOAD, governed: false }).kind).toBe('ungoverned')
  })
})
