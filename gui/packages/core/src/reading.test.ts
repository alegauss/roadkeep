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
  oneOrMany,
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

describe('RG179: a value that is either one thing or a list of them', () => {
  it('takes the one', () => {
    const read = oneOrMany(aString)('a why that was', 'was.why')

    expect(read).toEqual({ ok: true, value: 'a why that was' })
  })

  it('takes the list, and leaves it a list', () => {
    // Not joined: a sentence built here would be this app composing a field.
    const read = oneOrMany(aString)(['RG1', 'RG2'], 'was.deps')

    expect(read).toEqual({ ok: true, value: ['RG1', 'RG2'] })
  })

  it('takes an empty list, which is what a field that held nothing answers', () => {
    expect(oneOrMany(aString)([], 'was.requires')).toEqual({ ok: true, value: [] })
  })

  it('fails on anything that is neither, naming the path it was at', () => {
    const read = oneOrMany(aString)(7, 'was.deps')

    expect(read.ok).toBe(false)
    if (read.ok) throw new Error('unreachable')
    expect(read.failure.path).toBe('was.deps')
  })

  it('fails inside the list, at the element, rather than on the list itself', () => {
    const read = oneOrMany(aString)(['RG1', 7], 'was.deps')

    expect(read.ok).toBe(false)
    if (read.ok) throw new Error('unreachable')
    expect(read.failure.path).toBe('was.deps[1]')
  })
})

describe('RG188: the key an assignment swallows', () => {
  /** The word, built rather than typed: a source file carrying it is a source file with it. */
  const PROTO = ['__', 'proto', '__'].join('')

  it('keeps a key spelled __proto__, which a plain assignment drops', () => {
    const read = dictionaryOf(aNumber)({ [PROTO]: 3, todo: 1 }, 'markers')

    expect(read.ok).toBe(true)
    if (!read.ok) throw new Error('unreachable')
    expect(Object.keys(read.value).sort()).toEqual([PROTO, 'todo'])
    expect(read.value[PROTO]).toBe(3)
  })

  it('counts every value it read, so a total still adds up', () => {
    // What the defect cost: the marker chips are drawn from the entries and sit beside the
    // total the verb printed, so a dropped key is a screen that stops summing to itself.
    const read = dictionaryOf(aNumber)({ [PROTO]: 3, todo: 1 }, 'markers')
    if (!read.ok) throw new Error('unreachable')

    expect(Object.values(read.value).reduce((all, one) => all + one, 0)).toBe(4)
  })

  it('answers a value and not an inherited one, for a key read by name', () => {
    // `boundsFrom` reads `nonGoalsWhy[lead]` by key. Falling through to the prototype
    // survives a `?? ''` guard as an object and draws as `[object Object]`.
    const read = dictionaryOf(aString)({ lead: 'because' }, 'why')
    if (!read.ok) throw new Error('unreachable')

    expect(read.value[PROTO]).toBeUndefined()
    expect(typeof (read.value[PROTO] ?? '')).toBe('string')
  })
})
