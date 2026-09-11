import { describe, expect, it } from 'vitest'

import { attemptRead, DEFAULT_LIMITS, explainUnreadable, withLimits } from './limits'
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

    expect(!read.ok && read.unreadable.reason).toBe('unspawnable')
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

describe('RG79: the half of an answer nobody was reading', () => {
  /** Captured from a cached older build refusing this project's config: exit 0, no stdout. */
  const REFUSED_CONFIG =
    "roadkeep: roadkeep.toml: unknown key 'install.wired' (allowed: install.enforced, " +
    'install.pinned) — read by roadkeep 0.2.4 (35f315b, ~/.cache/roadkeep-src)'

  it('carries what the engine wrote, where the answer was not a payload', async () => {
    // Exit 0, nothing on stdout, and the whole explanation on stderr. Before this, the
    // reader was told `expected JSON, found ""` and the cause went in the bin.
    const read = await attemptRead(
      answering({ code: 0, stdout: '', stderr: `${REFUSED_CONFIG}\n` }),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.said).toBe(REFUSED_CONFIG)
    // And it leads the message, because the argv names the symptom and this names the cause.
    expect(read.unreadable.message).toBe(REFUSED_CONFIG)
  })

  it('falls back to the argv where the engine said nothing at all', async () => {
    const read = await attemptRead(answering({ stdout: 'not json' }), request, readListPayload)

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.said).toBe('')
    expect(read.unreadable.message).toContain('list')
    expect(read.unreadable.message).toContain('not JSON')
  })

  it('carries it beside a shape that did not match, without replacing that message', async () => {
    // Here the answer *was* JSON and the shape was wrong, so the reader's own sentence is
    // the useful one — but a warning on stderr is still worth having.
    const read = await attemptRead(
      answering({ stdout: '{"file": 7}', stderr: 'roadkeep: a deprecation notice' }),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.said).toBe('roadkeep: a deprecation notice')
    expect(read.unreadable.message).toContain('expected')
  })

  it('has nothing to carry when the call never ran', async () => {
    const read = await attemptRead(
      failing(new EngineCallFailed('unspawnable', 'python is not on PATH', 4)),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.said).toBe('')
  })

  it('bounds it, because stderr is not a field anybody promised a size for', async () => {
    const read = await attemptRead(
      answering({ stdout: '', stderr: 'x'.repeat(5000) }),
      request,
      readListPayload,
    )

    expect(read.ok).toBe(false)
    if (read.ok) return
    expect(read.unreadable.said).toHaveLength(2001)
    expect(read.unreadable.said.endsWith('…')).toBe(true)
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

describe('RG99: the state as a sentence', () => {
  it('blames the version gap and names the engine, not the project', () => {
    // A shape this build does not recognise means this app is behind the one that answered,
    // and naming that version is what turns a message into something somebody can do.
    const said = explainUnreadable(
      {
        reason: 'unreadable-payload',
        message: 'tasks[2].symptom: expected a string, found nothing',
        code: '',
        fields: {},
        elapsedMs: 12,
        argv: ['-C', '/w', 'list', '--json'],
        said: '',
      },
      { verb: 'list', engineVersion: '0.2.358' },
    )

    expect(said).toContain('tasks[2].symptom')
    expect(said).toContain('a string')
    expect(said).toContain('roadkeep 0.2.358')
    expect(said).toContain('behind')
  })

  it('still says something useful when no version is known', () => {
    const said = explainUnreadable(
      {
        reason: 'unreadable-payload',
        message: 'the answer: expected an object, found null',
        code: '',
        fields: {},
        elapsedMs: 3,
        argv: ['-C', '/w', 'stats', '--json'],
        said: '',
      },
      { verb: 'stats', engineVersion: '' },
    )

    expect(said).toContain('`stats`')
    expect(said).toContain('unknown version')
  })

  it('does not blame the version for a call that never happened', () => {
    // A timeout says nothing about which build answered, because none did. Telling somebody
    // they are behind the engine sends them to read a changelog for a hung process.
    const said = explainUnreadable(
      {
        reason: 'timeout',
        message: 'it ran past 15000ms',
        code: '',
        fields: {},
        elapsedMs: 15000,
        argv: ['-C', '/w', 'list', '--json'],
        said: '',
      },
      { verb: 'list', engineVersion: '0.2.358' },
    )

    expect(said).toContain('ran past')
    expect(said).not.toContain('behind')
  })
})
