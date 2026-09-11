import { describe, expect, it } from 'vitest'

import { EVERY_SOURCE } from './bridge'

import type { BridgedRequest, BridgedResult, OpenedProject, RendererBridge } from './bridge'
import { buildArgv, buildCall } from './client'
import { openProject } from './opening'
import {
  bridgedRun,
  bridgedTransport,
  isTopic,
  heardBy,
  keyOfEvent,
  openedFrom,
  openOver,
  requestFrom,
  withheldBecause,
} from './serving'
import {
  EngineCallFailed,
  type CancelSignal,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from './transport'
import type { VerbInputs, VerbName } from './verbs'
import { composeWrite } from './writing'

/**
 * RG143: one process running what another composed, both halves, with no process at all.
 *
 * The guard is asked about command lines the client and the write table really build, and
 * about the ones a renderer that stopped being this app's would send instead. The crossing
 * is asked through a stub bridge, since what is held is the round trip of a failure and a
 * cancellation, and neither needs IPC to be wrong.
 */

const ROOT = '/work/project'
const literal = (left: string, right: string): boolean => left === right

/** A cancellation this package can build, as `pool.test.ts` builds one: it has no `AbortController`. */
function cancellation(cancelled = false): { signal: CancelSignal; cancel: () => void } {
  const listeners = new Set<() => void>()
  let aborted = cancelled
  return {
    cancel() {
      aborted = true
      for (const listener of listeners) listener()
    },
    signal: {
      get aborted() {
        return aborted
      },
      addEventListener: (_type, listener) => listeners.add(listener),
      removeEventListener: (_type, listener) => listeners.delete(listener),
    },
  }
}

function read<K extends VerbName>(verb: K, input: VerbInputs[K]): EngineRequest {
  return { root: ROOT, argv: buildArgv(ROOT, verb, input), call: buildCall(verb, input) }
}

function argv(...parts: string[]): EngineRequest {
  return { root: ROOT, argv: ['-C', ROOT, ...parts, '--json'] }
}

describe('RG143: what a carrier runs for another process', () => {
  it('runs a read the client composed, argv and tool call both', () => {
    expect(withheldBecause(read('list', { block: 'A', marker: '📋' }), literal)).toBeNull()
    expect(withheldBecause(read('brief', { id: 'RG1', claim: true }), literal)).toBeNull()
  })

  it('runs a read spelled in two words', () => {
    expect(withheldBecause(read('nonGoalList', {}), literal)).toBeNull()
  })

  it('runs a write the table composed, a two-word one included', () => {
    const add = composeWrite(ROOT, 'add', { block: 'A', symptom: 'a symptom', why: 'A why.' })
    const section = composeWrite(ROOT, 'sectionAdd', { anchor: 'RG1', title: 'A title' })

    expect(withheldBecause({ root: ROOT, argv: add.argv }, literal)).toBeNull()
    expect(withheldBecause({ root: ROOT, argv: section.argv }, literal)).toBeNull()
  })

  it('keeps prose that opens on a dash as prose, which a list-shaped body does', () => {
    // argparse reads a part with a space in it as a value, so this is the body it looks like.
    const add = composeWrite(ROOT, 'add', {
      block: 'A',
      symptom: 'a symptom',
      why: 'A why.',
      section: 'Its design',
      sectionBody: '- one thing\n- and another',
    })

    expect(withheldBecause({ root: ROOT, argv: add.argv }, literal)).toBeNull()
  })
})

describe('RG143: what a carrier refuses, before anything starts', () => {
  it('refuses a command line about another folder than the one it names', () => {
    const elsewhere = { root: ROOT, argv: ['-C', '/somewhere/else', 'list', '--json'] }

    expect(withheldBecause(elsewhere, literal)).toContain(ROOT)
  })

  it('compares the two spellings with the rule it was handed, never its own', () => {
    const shouted = { root: ROOT, argv: ['-C', ROOT.toUpperCase(), 'list', '--json'] }
    const folding = (left: string, right: string) => left.toLowerCase() === right.toLowerCase()

    expect(withheldBecause(shouted, literal)).not.toBeNull()
    expect(withheldBecause(shouted, folding)).toBeNull()
  })

  it('refuses a command line that does not ask for JSON', () => {
    expect(withheldBecause({ root: ROOT, argv: ['-C', ROOT, 'list'] }, literal)).toContain('JSON')
  })

  it('refuses a verb neither table holds', () => {
    expect(withheldBecause(argv('install'), literal)).toContain('`install`')
  })

  it('refuses an option the builder never emits', () => {
    expect(withheldBecause(argv('list', '--all'), literal)).toContain('--all')
  })

  it('refuses an abbreviation of one it does, which argparse would expand', () => {
    expect(withheldBecause(argv('list', '--bl', 'A'), literal)).toContain('--bl')
    // Spelled whole with its value joined, it is the option the table emits.
    expect(withheldBecause(argv('list', '--block=A'), literal)).toBeNull()
  })

  it('refuses an option that names a file, though the table emits that one', () => {
    // `section add --body-file` is in the write table, and from a process with no filesystem
    // it copies any file on the machine into a governed doc, to be read back with `show`.
    const named = argv('section', 'add', 'RG1', '--title', 'T', '--body-file', '/etc/passwd')
    // argparse splits on `=` before it asks whether the part has a space, so the head names it.
    const joined = argv('section', 'add', 'RG1', '--title', 'T', '--body-file=/a b.md')

    expect(withheldBecause(named, literal)).toContain('--body-file')
    expect(withheldBecause(joined, literal)).toContain('--body-file')
  })

  it('refuses a tool argument that names a file, for the same reason', () => {
    const request = argv('section', 'add', 'RG1', '--title', 'T')
    const call = { tool: 'section_add', arguments: { anchor: 'RG1', title: 'T', body_file: '/x' } }

    expect(withheldBecause({ ...request, call }, literal)).toContain('body_file')
  })

  it('refuses a second root slipped in after the verb', () => {
    expect(withheldBecause(argv('list', '-C', '/somewhere/else'), literal)).toContain('-C')
  })

  it('refuses a tool call naming another verb than its command line', () => {
    // A held engine runs the call and ignores the argv, so the call is what has to agree.
    const crossed = { ...read('list', {}), call: { tool: 'ship', arguments: { id: 'RG1' } } }

    expect(withheldBecause(crossed, literal)).toContain('`ship`')
  })

  it('refuses a tool argument the verb input never has', () => {
    const request = read('list', { block: 'A' })
    const widened = { ...request, call: { tool: 'list', arguments: { block: 'A', every: true } } }

    expect(withheldBecause(widened, literal)).toContain('`every`')
  })
})

describe('RG144: a subscription, as the renderer names one', () => {
  it('knows the topics the table holds, and nothing else', () => {
    expect(isTopic('governed')).toBe(true)
    expect(isTopic('session')).toBe(true)
    expect(isTopic('toString')).toBe(false)
    expect(isTopic(3)).toBe(false)
  })

  it('reads the key an event belongs to, which is how one channel carries every source', () => {
    expect(keyOfEvent('governed', { root: '/proj' })).toBe('/proj')
    expect(keyOfEvent('session', { session: 's1', index: 0, line: '{}' })).toBe('s1')
  })
})

describe('RG143: a request as the renderer sent it', () => {
  it('reads the argv, the tool call and the ceiling', () => {
    const sent = { argv: ['-C', ROOT, 'list', '--json'], call: buildCall('list', {}), timeoutMs: 5 }

    expect(requestFrom(sent)).toEqual(sent)
  })

  it('leaves out what was not sent, rather than carrying it as undefined', () => {
    expect(requestFrom({ argv: ['-C', ROOT, 'list', '--json'] })).toEqual({
      argv: ['-C', ROOT, 'list', '--json'],
    })
  })

  it.each([
    ['not an object', 'list'],
    ['an argv that is not strings', { argv: ['-C', 3] }],
    ['a call with no tool', { argv: [], call: { arguments: {} } }],
    ['a ceiling that is not a number', { argv: [], timeoutMs: 'soon' }],
  ])('refuses %s', (_what, sent) => {
    expect(requestFrom(sent)).toBeNull()
  })
})

describe('RG143: a failure, across a crossing a class cannot make', () => {
  const RESULT: EngineResult = { code: 1, stdout: '{}', stderr: 'said', durationMs: 7 }

  it('answers the result, a non-zero exit included, as a result', async () => {
    expect(await bridgedRun(() => Promise.resolve(RESULT))).toEqual({ kind: 'ran', result: RESULT })
  })

  it('takes a failed call apart into its fields', async () => {
    const answer = await bridgedRun(() =>
      Promise.reject(new EngineCallFailed('timeout', 'ran past 5ms', 5)),
    )

    expect(answer).toEqual({
      kind: 'failed',
      reason: 'timeout',
      message: 'ran past 5ms',
      durationMs: 5,
    })
  })

  it('names anything else thrown as a call that never started', async () => {
    const answer = await bridgedRun(() => Promise.reject(new Error('no such file')))

    expect(answer).toMatchObject({ kind: 'failed', reason: 'unspawnable', message: 'no such file' })
  })

  it('puts the class back together on the far side', async () => {
    const failed: BridgedResult = {
      kind: 'failed',
      reason: 'withheld',
      message: 'no',
      durationMs: 0,
    }
    const transport = bridgedTransport({ run: () => Promise.resolve(failed) })

    const thrown = await transport.run(read('list', {})).catch((cause: unknown) => cause)

    expect(thrown).toBeInstanceOf(EngineCallFailed)
    expect(thrown).toMatchObject({ reason: 'withheld', message: 'no' })
  })

  it('sends the root as the method argument and never the signal', async () => {
    const crossed: { root: string; request: BridgedRequest }[] = []
    const transport = bridgedTransport({
      run: (root, request) => {
        crossed.push({ root, request })
        return Promise.resolve({ kind: 'ran', result: RESULT })
      },
    })

    const result = await transport.run({ ...read('list', {}), signal: cancellation().signal })

    expect(result).toEqual(RESULT)
    expect(crossed[0]?.root).toBe(ROOT)
    expect(Object.keys(crossed[0]?.request ?? {}).sort()).toEqual(['argv', 'call'])
  })

  it('refuses a call already cancelled without asking the carrier', async () => {
    let asked = 0
    const transport = bridgedTransport({
      run: () => {
        asked += 1
        return Promise.resolve({ kind: 'ran', result: RESULT })
      },
    })

    const thrown = await transport
      .run({ ...read('list', {}), signal: cancellation(true).signal })
      .catch((cause: unknown) => cause)

    expect(thrown).toMatchObject({ reason: 'aborted' })
    expect(asked).toBe(0)
  })

  it('abandons a call cancelled in flight, which is what a screen that redrew wants', async () => {
    const stop = cancellation()
    const transport = bridgedTransport({ run: () => new Promise(() => undefined) })

    const pending = transport.run({ ...read('list', {}), signal: stop.signal })
    stop.cancel()

    await expect(pending).rejects.toMatchObject({ reason: 'aborted' })
  })
})

const ENGINES = JSON.stringify({
  writing: { version: '0.2.400', home: '/engines/one', revision: 'abc1234', on_disk: '0.2.400' },
  invoke: 'python /proj/launch.py',
  declaration: '',
  verdict: 'agreed',
  agree: true,
  readable: true,
  split: false,
  swapped: false,
})

const CONFIG = JSON.stringify({
  version: '0.2.400',
  source: 'roadkeep.toml',
  keys: [{ table: 'files', key: 'roadmap', declared: true, set: '"docs/ROADMAP.md"' }],
})

const NON_GOALS = JSON.stringify({
  file: 'docs/ROADMAP.md',
  governed: true,
  non_goals: ['No store of its own'],
  non_goals_elided: 0,
  non_goals_quoted: {},
  non_goals_why: { 'No store of its own': 'A cache is a second answer.' },
})

/** A machine answering by verb, as `opening.test.ts` builds one. */
const machine: Transport = {
  run(request) {
    const said: Record<string, string> = {
      engines: ENGINES,
      config: CONFIG,
      commands: JSON.stringify({ version: '0.2.400', source: null, commands: [] }),
      'non-goal': NON_GOALS,
    }
    const answer = said[request.argv[2] ?? '']
    if (answer === undefined) return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
    return Promise.resolve({ code: 0, stdout: answer, stderr: '', durationMs: 1 })
  },
}

describe('RG143: an opening, carried across', () => {
  it('keeps every fact of an open project and none of its functions', async () => {
    const opening = await openProject('/proj', [['python', '/proj/launch.py']], () => machine, {
      unheld: () => 'this build publishes no mcp surface',
    })

    const carried = openedFrom(opening)

    expect(carried.kind).toBe('open')
    if (carried.kind !== 'open') return
    expect(carried.engine.payload.writing.version).toBe('0.2.400')
    expect(carried.governed).toEqual({ roadmap: 'docs/ROADMAP.md' })
    expect(carried.unheld).toBe('this build publishes no mcp surface')
    // A structured clone refuses a function, so one left here is an IPC call that throws.
    expect(Object.values(carried).some((value) => typeof value === 'function')).toBe(false)
  })

  it('carries a way of not opening unchanged, since it is plain data already', async () => {
    const opening = await openProject('/proj', [], () => machine)

    expect(openedFrom(opening)).toEqual(opening)
  })

  it('builds a project the renderer reads through, every call crossing as run', async () => {
    const opened = openedFrom(
      await openProject('/proj', [['python', '/proj/launch.py']], () => machine),
    )
    const crossed: string[][] = []
    const bridge: Pick<RendererBridge, 'open' | 'run'> = {
      open: () => Promise.resolve(opened),
      run: async (root, request) => {
        crossed.push([...request.argv])
        return bridgedRun(() => machine.run({ ...request, root }))
      },
    }

    const reached = await openOver(bridge, '/proj')
    if (reached.kind !== 'open') throw new Error(`did not open: ${reached.kind}`)
    const answer = await reached.project.client.call('/proj', 'nonGoalList', {})

    expect(answer.kind).toBe('read')
    if (answer.kind !== 'read') return
    expect(answer.value.nonGoalsWhy?.['No store of its own']).toBe('A cache is a second answer.')
    expect(crossed).toEqual([buildArgv('/proj', 'nonGoalList', {})])
    expect(reached.project.engine.payload.writing.home).toBe('/engines/one')
  })

  it('answers a withheld folder as withheld, with nothing to read through', async () => {
    const withheld: OpenedProject = { kind: 'withheld', root: '/x', reason: 'not catalogued' }
    const bridge: Pick<RendererBridge, 'open' | 'run'> = {
      open: () => Promise.resolve(withheld),
      run: () => Promise.reject(new Error('never asked')),
    }

    expect(await openOver(bridge, '/x')).toEqual(withheld)
  })
})

describe('RG178: whether an event is one a listener asked for', () => {
  const line = { session: 's1', index: 0, line: '{}' }

  it('is heard by the key it came from, which is what one screen asks for', () => {
    expect(heardBy('session', line, 's1')).toBe(true)
    expect(heardBy('session', line, 's2')).toBe(false)
  })

  it('is heard by the key that means every source, whatever its own key is', () => {
    // The reason this is a function and not a comparison at the listener: an event carries
    // the key of the source it came from and never the one somebody subscribed with, so a
    // listener asking for all of them would compare its own `*` and hear nothing.
    expect(heardBy('session', line, EVERY_SOURCE)).toBe(true)
    expect(heardBy('governed', { root: '/proj' }, EVERY_SOURCE)).toBe(true)
  })
})
