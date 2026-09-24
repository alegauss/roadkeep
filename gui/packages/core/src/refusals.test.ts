import { describe, expect, it } from 'vitest'

import { readListPayload } from './payloads'
import { fieldsRefused, offerable, readAnswer, readExplanation, readRefusal } from './refusals'
import type { EngineResult } from './transport'

/** Captured from a real `add` whose symptom was over the project's limit. */
const REFUSED_FIELD = {
  refused: [
    {
      code: 'symptom.too-long',
      field: 'symptom',
      bound: '',
      message:
        '200 characters, limit is 120 (roadkeep.toml:19 [limits].symptom): delete 80 characters',
    },
  ],
  beside: '',
  about: '',
  said: 'roadkeep: refused, nothing written:\n  symptom: 200 characters…',
}

/** Captured from `show` on an id that does not exist: a refusal about no field at all. */
const REFUSED_WHOLE = {
  refused: [],
  beside: '',
  about: '',
  said: 'roadkeep: no task FX999 in docs/ROADMAP.md or docs/CHANGELOG.md: an id in neither file was never written or was retired (RK32)',
}

const EXPLAIN = {
  code: 'symptom.too-long',
  kind: 'compose',
  cause: 'past the limit; the symptom is the falsifiable claim, so shortening it is `restate`',
  varies: null,
  sequence: false,
  doors: [
    {
      argv: ['restate', '…', '--symptom', '…'],
      what: 'past the limit; the symptom is the falsifiable claim',
      complete: false,
      writes: true,
      call: { tool: 'mcp__roadkeep__restate', arguments: { id: '…', symptom: '…' } },
    },
  ],
}

const answered = (payload: unknown, code = 2): EngineResult => ({
  code,
  stdout: JSON.stringify(payload),
  stderr: '',
  durationMs: 1,
})

describe('RG5: a refusal read as data', () => {
  it('names the field that was refused, so a screen can mark that box', () => {
    const parsed = readRefusal(REFUSED_FIELD, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.refused[0]?.field).toBe('symptom')
    expect(parsed.value.refused[0]?.code).toBe('symptom.too-long')
  })

  it('marks nothing for a refusal that is about no field', () => {
    const parsed = readRefusal(REFUSED_WHOLE, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    // The prose names an id and two filenames. Recovering a field from it is exactly the
    // thing this must not do: it would highlight a box the engine never refused.
    expect(fieldsRefused(parsed.value)).toEqual([])
    expect(parsed.value.said).toContain('FX999')
  })

  it('keeps the prose for the case where nothing else resolves', () => {
    const parsed = readRefusal(REFUSED_WHOLE, '')
    expect(parsed.ok && parsed.value.said).toContain('was never written or was retired')
  })
})

describe('RG5: telling a refusal from an answer', () => {
  it('reads a refusal as a refusal', () => {
    const parsed = readAnswer(readListPayload, answered(REFUSED_FIELD))

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.kind).toBe('refused')
  })

  it('reads a payload as a payload even when the exit code is non-zero', () => {
    // `lint` exits 1 when it finds something, and that is the gate working. Reading it as
    // a refusal would turn every finding into an error nobody could act on.
    const payload = {
      file: 'docs/ROADMAP.md',
      total: 0,
      uncounted: [],
      standing: null,
      startable: null,
      over: null,
      tasks: [],
    }
    const parsed = readAnswer(readListPayload, answered(payload, 1))

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.kind).toBe('payload')
  })

  it('does not mistake a payload that happens to carry prose for a refusal', () => {
    // `said` alone is not the signal — `refused` has to be there as well, or a future
    // payload with a message field would start reading as an error.
    const parsed = readAnswer(readListPayload, answered({ said: 'a sentence' }))

    expect(parsed.ok).toBe(false)
  })

  it('fails readably when stdout is not JSON at all', () => {
    const parsed = readAnswer(readListPayload, {
      code: 1,
      stdout: 'Traceback (most recent call last):',
      stderr: '',
      durationMs: 1,
    })

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.expected).toBe('JSON')
  })

  it('says so when there was nothing on stdout at all', () => {
    const parsed = readAnswer(readListPayload, {
      code: 1,
      stdout: '',
      stderr: 'boom',
      durationMs: 1,
    })

    expect(parsed.ok).toBe(false)
    if (parsed.ok) return
    expect(parsed.failure.got).toBe('nothing on stdout')
  })
})

describe('RG5: the doors a code opens', () => {
  it('reads what explain publishes for a refusal code', () => {
    const parsed = readExplanation(EXPLAIN, '')

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    expect(parsed.value.code).toBe('symptom.too-long')
    expect(parsed.value.doors[0]?.argv).toEqual(['restate', '…', '--symptom', '…'])
    expect(parsed.value.doors[0]?.writes).toBe(true)
  })

  it('offers only the doors that can run as they stand', () => {
    const parsed = readExplanation(EXPLAIN, '')
    if (!parsed.ok) return

    // This one has an id and a symptom still to fill in, so it is something to show and
    // not something to press.
    expect(offerable(parsed.value.doors)).toEqual([])
  })

  it('offers a door that needs nothing filled in', () => {
    const parsed = readExplanation(
      { ...EXPLAIN, doors: [{ ...EXPLAIN.doors[0], complete: true }] },
      '',
    )
    if (!parsed.ok) return

    expect(offerable(parsed.value.doors)).toHaveLength(1)
  })
})
