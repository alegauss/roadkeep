import { describe, expect, it } from 'vitest'

import { disagrees, isModified, resolveEngine, type TransportFor } from './engine-resolution'
import { readEnginesPayload } from './engines'
import { EngineCallFailed, type EngineResult, type Transport } from './transport'

interface Answer {
  readonly version?: string
  readonly home?: string
  readonly revision?: string
  readonly onDisk?: string
  readonly invoke?: string
  readonly verdict?: string
  readonly agree?: boolean
  readonly split?: boolean
  readonly swapped?: boolean
}

function payloadFor(answer: Answer): string {
  return JSON.stringify({
    writing: {
      version: answer.version ?? '0.2.356',
      home: answer.home ?? '/engines/one',
      revision: answer.revision ?? 'abc1234',
      on_disk: answer.onDisk ?? answer.version ?? '0.2.356',
    },
    invoke: answer.invoke ?? '',
    declaration: '',
    verdict: answer.verdict ?? 'agreed',
    agree: answer.agree ?? true,
    readable: true,
    split: answer.split ?? false,
    swapped: answer.swapped ?? false,
  })
}

/**
 * A machine, described as a map from a command line to what running it does. Everything
 * absent is a command that cannot be started, which is the ordinary case for a candidate.
 */
function machine(installed: Record<string, Answer | 'not-an-engine'>): {
  transportFor: TransportFor
  asked: string[]
} {
  const asked: string[] = []
  const transportFor: TransportFor = (engine) => {
    const key = engine.join(' ')
    const transport: Transport = {
      run(): Promise<EngineResult> {
        asked.push(key)
        const answer = installed[key]
        if (answer === undefined) {
          return Promise.reject(new EngineCallFailed('unspawnable', `no ${key}`, 1))
        }
        const stdout = answer === 'not-an-engine' ? 'some other program' : payloadFor(answer)
        return Promise.resolve({ code: 0, stdout, stderr: '', durationMs: 1 })
      },
    }
    return transport
  }
  return { transportFor, asked }
}

const LAUNCHER = ['python', '/proj/.claude/hooks/roadkeep-launch.py']
const ON_PATH = ['roadkeep']

describe('RG2: which copy answers', () => {
  it('takes the first candidate that answers with an engines payload', async () => {
    const { transportFor, asked } = machine({
      'python /proj/.claude/hooks/roadkeep-launch.py': { version: '0.2.356' },
      roadkeep: { version: '0.1.0' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [LAUNCHER, ON_PATH])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.payload.writing.version).toBe('0.2.356')
    // The one on PATH is never even asked: it is the copy `engines` exists to warn about.
    expect(asked).toEqual(['python /proj/.claude/hooks/roadkeep-launch.py'])
  })

  it('moves on from a candidate that cannot be started', async () => {
    const { transportFor, asked } = machine({ roadkeep: { version: '0.2.356' } })

    const resolution = await resolveEngine(transportFor, '/proj', [LAUNCHER, ON_PATH])

    expect(resolution.kind).toBe('resolved')
    expect(asked).toEqual(['python /proj/.claude/hooks/roadkeep-launch.py', 'roadkeep'])
  })

  it('moves on from something that runs but is not roadkeep', async () => {
    const { transportFor } = machine({
      'python /proj/.claude/hooks/roadkeep-launch.py': 'not-an-engine',
      roadkeep: { version: '0.2.356' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [LAUNCHER, ON_PATH])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.engine).toEqual(ON_PATH)
  })
})

describe('RG2: a project that resolves nothing', () => {
  it('is unreadable with the reason, and never a crash', async () => {
    const { transportFor } = machine({})

    const resolution = await resolveEngine(transportFor, '/proj', [LAUNCHER, ON_PATH])

    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') return
    expect(resolution.reason).toContain('which roadkeep governs this project is unknown')
    // The reason has to name what was looked for, or it is a shrug on a screen.
    expect(resolution.tried).toEqual([LAUNCHER, ON_PATH])
  })

  it('says so differently when nothing was even offered', async () => {
    const { transportFor } = machine({})

    const resolution = await resolveEngine(transportFor, '/proj', [])

    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') return
    expect(resolution.reason).toContain('nothing was offered')
  })
})

describe('RG2: the copy the project actually declares', () => {
  it('switches to the command line invoke names, once it has been reached', async () => {
    const { transportFor, asked } = machine({
      roadkeep: { home: '/engines/plugin', invoke: 'python /plugins/roadkeep/launch.py' },
      'python /plugins/roadkeep/launch.py': {
        home: '/engines/plugin',
        version: '0.2.356',
        invoke: 'python /plugins/roadkeep/launch.py',
      },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.engine).toEqual(['python', '/plugins/roadkeep/launch.py'])
    expect(resolution.engine.reachedDeclared).toBe(true)
    expect(asked).toEqual(['roadkeep', 'python /plugins/roadkeep/launch.py'])
  })

  it('keeps the copy that answered, and says so, when the declared one cannot be reached', async () => {
    const { transportFor } = machine({
      roadkeep: { home: '/engines/one', invoke: 'python /gone/launch.py' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    // Answering from a copy nobody chose is bad; answering from the reachable one and
    // saying it is not the declared one is the honest half of the same situation.
    expect(resolution.engine.engine).toEqual(ON_PATH)
    expect(resolution.engine.reachedDeclared).toBe(false)
  })

  it('does not switch when the declared copy is a different home wearing the same name', async () => {
    const { transportFor } = machine({
      roadkeep: { home: '/engines/one', invoke: 'python /other/launch.py' },
      'python /other/launch.py': { home: '/engines/somewhere-else' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.engine).toEqual(ON_PATH)
    expect(resolution.engine.reachedDeclared).toBe(false)
  })

  it('asks once when invoke names the candidate that already answered', async () => {
    const { transportFor, asked } = machine({
      'python /proj/.claude/hooks/roadkeep-launch.py': {
        invoke: 'python /proj/.claude/hooks/roadkeep-launch.py',
      },
    })

    await resolveEngine(transportFor, '/proj', [LAUNCHER])

    expect(asked).toHaveLength(1)
  })

  it('does not chase an invoke it could not split', async () => {
    const { transportFor, asked } = machine({
      roadkeep: { invoke: 'python "C:\\Program Files\\rk' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH])

    expect(asked).toHaveLength(1)
    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.reachedDeclared).toBe(false)
  })
})

describe('RG65: one file spelled two ways', () => {
  const WINDOWS_LAUNCHER = ['python', 'D:\\proj\\.claude\\hooks\\roadkeep-launch.py']
  const POSIX_SPELLING = 'python D:/proj/.claude/hooks/roadkeep-launch.py'
  const foldSeparators = (left: string, right: string): boolean =>
    left.replace(/\\/g, '/') === right.replace(/\\/g, '/')

  it('costs a second interpreter start when nothing was told the spellings are one', async () => {
    const { transportFor, asked } = machine({
      'python D:\\proj\\.claude\\hooks\\roadkeep-launch.py': { invoke: POSIX_SPELLING },
    })

    await resolveEngine(transportFor, '/proj', [WINDOWS_LAUNCHER])

    // The default is the literal comparison, and this is exactly what it pays for.
    expect(asked).toHaveLength(2)
  })

  it('asks once when the caller says the two spellings name one file', async () => {
    const { transportFor, asked } = machine({
      'python D:\\proj\\.claude\\hooks\\roadkeep-launch.py': { invoke: POSIX_SPELLING },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [WINDOWS_LAUNCHER], {
      samePart: foldSeparators,
    })

    expect(asked).toHaveLength(1)
    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.reachedDeclared).toBe(true)
  })

  it('still reaches a copy that really is a different one', async () => {
    const { transportFor, asked } = machine({
      roadkeep: { home: '/engines/plugin', invoke: 'python /plugins/roadkeep/launch.py' },
      'python /plugins/roadkeep/launch.py': { home: '/engines/plugin' },
    })

    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH], {
      samePart: foldSeparators,
    })

    // A cheaper comparison is only worth having if it still buys the check: the second
    // call is what proves the declared copy exists, and a real difference still pays it.
    expect(asked).toHaveLength(2)
    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.engine).toEqual(['python', '/plugins/roadkeep/launch.py'])
  })

  it('keeps the length of a command line its own business', async () => {
    const { transportFor } = machine({
      roadkeep: { home: '/engines/one', invoke: 'python -X utf8 /gone/launch.py' },
    })

    // The caller answers what makes two *parts* equal. How many there have to be is the
    // shape of an argv, which stays here — a comparison cannot talk this into a match.
    const resolution = await resolveEngine(transportFor, '/proj', [ON_PATH], {
      samePart: () => true,
    })

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return
    expect(resolution.engine.reachedDeclared).toBe(false)
  })
})

describe('RG2: the states a screen has to tell apart', () => {
  it('sees a modified working tree', () => {
    const clean = readEnginesPayload(payloadFor({ revision: '2404ae02' }))
    const dirty = readEnginesPayload(payloadFor({ revision: '2404ae02 modified' }))

    expect(clean && isModified(clean)).toBe(false)
    expect(dirty && isModified(dirty)).toBe(true)
  })

  it.each([
    ['copies that disagree', { agree: false }],
    ['copies split across homes', { split: true }],
    ['a home swapped under the process', { swapped: true }],
  ])('sees %s', (_case, answer) => {
    const payload = readEnginesPayload(payloadFor(answer))
    expect(payload && disagrees(payload)).toBe(true)
  })

  it('reports agreement as agreement', () => {
    const payload = readEnginesPayload(payloadFor({}))
    expect(payload && disagrees(payload)).toBe(false)
  })
})
