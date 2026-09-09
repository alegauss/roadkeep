import { describe, expect, it } from 'vitest'

import {
  aNumber,
  aString,
  dictionaryOf,
  listOf,
  orMissing,
  orNull,
  readPayload,
  record,
} from './reading'

const WHERE = { verb: 'list', engineVersion: '0.2.358' }

describe('RG3: what a shape accepts', () => {
  it('reads the fields it declares', () => {
    const reader = record<{ id: string; line: number }>({ id: aString, line: aNumber })
    expect(reader({ id: 'RG1', line: 7 }, '')).toEqual({ ok: true, value: { id: 'RG1', line: 7 } })
  })

  it('ignores every key it does not declare', () => {
    // The payloads carry far more than this app reads, and every release adds more. A
    // reader that refused the extra would break on the next one.
    const reader = record<{ id: string }>({ id: aString })
    expect(reader({ id: 'RG1', symptom: 'x', deps: [], future: 1 }, '')).toEqual({
      ok: true,
      value: { id: 'RG1' },
    })
  })

  it('reads null as a value where the shape allows it', () => {
    // `standing`, `over` and `section` come back null in ordinary answers, so this is the
    // default reading rather than the exception.
    expect(orNull(aString)(null, 'standing')).toEqual({ ok: true, value: null })
  })

  it('tells a missing key from a null one', () => {
    expect(orMissing(aString, 'fallback')(undefined, 'x')).toEqual({ ok: true, value: 'fallback' })
    expect(orNull(aString)(undefined, 'x').ok).toBe(false)
  })

  it('reads an object whose keys are data', () => {
    expect(dictionaryOf(aNumber)({ '📋': 11, '💭': 48 }, 'markers')).toEqual({
      ok: true,
      value: { '📋': 11, '💭': 48 },
    })
  })
})

describe('RG3: what a shape refuses, and how it says so', () => {
  it('names the field, not just the payload', () => {
    const reader = record<{ id: string; line: number }>({ id: aString, line: aNumber })
    const parsed = reader({ id: 'RG1', line: 'seven' }, '')

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.path).toBe('line')
    expect(parsed.failure.expected).toBe('a number')
    expect(parsed.failure.got).toBe('"seven"')
  })

  it('names the element inside a list, by index', () => {
    const reader = record<{ tasks: { id: string }[] }>({
      tasks: listOf(record<{ id: string }>({ id: aString })),
    })
    const parsed = reader({ tasks: [{ id: 'RG1' }, { id: 'RG2' }, { id: 12 }] }, '')

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    // `tasks[2].id` is a path somebody can go and look at. "invalid payload" is not.
    expect(parsed.failure.path).toBe('tasks[2].id')
  })

  it('refuses a renamed key rather than reading undefined past it', () => {
    // The whole symptom: a key renamed upstream should be a red build here and not an
    // `undefined` on somebody's screen.
    const reader = record<{ symptom: string }>({ symptom: aString })
    const parsed = reader({ complaint: 'renamed upstream' }, '')

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.got).toBe('nothing')
  })

  it('refuses stdout that is not JSON at all', () => {
    const parsed = readPayload(record<{ x: string }>({ x: aString }), 'Traceback...', WHERE)

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.expected).toBe('JSON')
  })
})
