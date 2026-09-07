import { describe, expect, it } from 'vitest'

import { attemptRead, DEFAULT_LIMITS, withLimits } from './limits'
import { readListPayload } from './payloads'
import { aString, record } from './reading'
import { EngineCallFailed, type EngineResult, type Transport } from './transport'

const answering = (result: Partial<EngineResult>): Transport => ({
  run: () => Promise.resolve({ code: 0, stdout: '{}', stderr: '', durationMs: 5, ...result }),
})

const failing = (failure: EngineCallFailed): Transport => ({
  run: () => Promise.reject(failure),
})

const request = { root: '/p', argv: ['-C', '/p', 'list', '--json'] }

describe('RG8: the two numbers a person may change', () => {
  it('uses the defaults when nothing is said', () => {
    expect(withLimits()).toEqual(DEFAULT_LIMITS)
  })

  it('takes a raised deadline, because a slow disk is a real machine', () => {
    expect(withLimits({ timeoutMs: 120000 }).timeoutMs).toBe(120000)
  })

  it('clamps rather than ignoring something unusable', () => {
    // Silently substituting a default for a number somebody typed is how a setting stops
    // being a setting. Clamping keeps the intent and bounds the damage.
    expect(withLimits({ timeoutMs: 5 }).timeoutMs).toBe(1000)
    expect(withLimits({ width: 0 }).width).toBe(1)
    expect(withLimits({ width: 9999 }).width).toBe(32)
    expect(withLimits({ timeoutMs: Number.NaN }).timeoutMs).toBe(1000)
  })

  it('takes a whole number of calls', () => {
    expect(withLimits({ width: 3.7 }).width).toBe(3)
  })
})

describe('RG8: a project that could not be read', () => {
  it('is a state carrying the elapsed time and the argv', async () => {
    const read = await attemptRead(
      failing(new EngineCallFailed('timeout', 'the engine ran past 15000ms', 15003)),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    // "Unreadable" alone is not something anybody can act on. Fifteen seconds spent on a
    // command you can see is the difference between a bug report and a shrug.
    expect(read.unreadable.reason).toBe('timeout')
    expect(read.unreadable.elapsedMs).toBe(15003)
    expect(read.unreadable.argv).toEqual(request.argv)
  })

  it('is a state when the engine could not start at all', async () => {
    const read = await attemptRead(
      failing(new EngineCallFailed('unspawnable', 'python is not on PATH', 4)),
      request,
      readListPayload,
    )

    expect(read.ok === false && read.unreadable.reason).toBe('unspawnable')
  })

  it('is a state when the answer is not JSON', async () => {
    const read = await attemptRead(
      answering({ stdout: 'Traceback (most recent call last):' }),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.reason).toBe('unreadable-payload')
    expect(read.unreadable.message).toContain('not JSON')
  })

  it('is a state when the answer is JSON of the wrong shape, naming the field', async () => {
    const read = await attemptRead(
      answering({ stdout: '{"file":"docs/ROADMAP.md"}' }),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.message).toContain('total')
  })

  it('does not swallow something that is not a call failing', async () => {
    // A programming error inside this app is not a project being unreadable, and turning
    // one into the other is how a bug becomes a permanent grey row on a screen.
    const broken: Transport = {
      run: () => Promise.reject(new TypeError('reader is not a function')),
    }

    await expect(attemptRead(broken, request, readListPayload)).rejects.toBeInstanceOf(TypeError)
  })
})

describe('RG8: a project that was read', () => {
  it('comes back with its value and how long it took', async () => {
    const read = await attemptRead(
      answering({ stdout: '{"name":"ok"}', durationMs: 361 }),
      request,
      record<{ name: string }>({ name: aString }),
    )

    expect(read.ok).toBe(true)
    if (!read.ok) return
    expect(read.value.name).toBe('ok')
    expect(read.durationMs).toBe(361)
  })
})
