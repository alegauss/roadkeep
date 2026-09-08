import { describe, expect, it, vi } from 'vitest'

import { buildArgv, createClient } from './client'
import type { CancelSignal, EngineRequest, EngineResult, Transport } from './transport'

function recordingTransport(): { transport: Transport; calls: EngineRequest[] } {
  const calls: EngineRequest[] = []
  const answer: EngineResult = { code: 0, stdout: '{}', stderr: '', durationMs: 1 }
  return {
    calls,
    transport: {
      run(request) {
        calls.push(request)
        return Promise.resolve(answer)
      },
    },
  }
}

describe('RG1: the command line one call builds', () => {
  it('names the project before the verb, because the engine takes -C first', () => {
    expect(buildArgv('/w/proj', 'list', {})).toEqual(['-C', '/w/proj', 'list', '--json'])
  })

  it('always asks for the machine-readable form', () => {
    for (const argv of [
      buildArgv('/w', 'list', {}),
      buildArgv('/w', 'show', { id: 'RG1' }),
      buildArgv('/w', 'stats', {}),
      buildArgv('/w', 'brief', {}),
      buildArgv('/w', 'lint', {}),
    ]) {
      expect(argv).toContain('--json')
    }
  })

  it('RG69: spreads a two-word verb words, rather than splitting its key', () => {
    // The key is an identifier this app uses and the spelling is an array in
    // `VERB_WORDS`. Never a key with a space in it split back apart: argv is an array so
    // that nothing here ever turns a command line into arguments.
    expect(buildArgv('/w', 'nonGoalList', {})).toEqual(['-C', '/w', 'non-goal', 'list', '--json'])
    expect(buildArgv('/w', 'criterionList', { block: 'D' })).toEqual([
      '-C',
      '/w',
      'criterion',
      'list',
      '--block',
      'D',
      '--json',
    ])
  })

  it('RG69: keeps a one-word verb spelled by its own key, with no map entry', () => {
    // The ordinary case, and the reason the map is sparse: a verb absent from it is
    // spelled by its key, so eleven of thirteen rows do not exist.
    expect(buildArgv('/w', 'lint', {})).toEqual(['-C', '/w', 'lint', '--json'])
  })

  it('leaves out a flag whose input is absent rather than passing an empty one', () => {
    expect(buildArgv('/w', 'list', {})).not.toContain('--block')
    expect(buildArgv('/w', 'brief', {})).toEqual(['-C', '/w', 'brief', '--json'])
  })

  it('builds a verb with every flag it takes', () => {
    expect(buildArgv('/w', 'list', { block: 'C', role: 'changelog', marker: '📋' })).toEqual([
      '-C',
      '/w',
      'list',
      '--block',
      'C',
      '--role',
      'changelog',
      '--marker',
      '📋',
      '--json',
    ])
  })

  it('repeats a repeatable flag once per value', () => {
    expect(buildArgv('/w', 'brief', { have: ['signing-cert', 'macos-machine'] })).toEqual([
      '-C',
      '/w',
      'brief',
      '--have',
      'signing-cert',
      '--have',
      'macos-machine',
      '--json',
    ])
  })

  it('puts a positional id where the verb wants it, before its flags', () => {
    expect(buildArgv('/w', 'show', { id: 'RG12', noBody: true })).toEqual([
      '-C',
      '/w',
      'show',
      'RG12',
      '--no-body',
      '--json',
    ])
  })

  it('carries prose through as one element, untouched', () => {
    // The whole reason argv is an array. A root a person chose can hold a space, a quote
    // or a shell metacharacter, and every one of them has to arrive as itself.
    const root = 'C:\\Users\\a b\\proj "one" && echo pwned'
    expect(buildArgv(root, 'list', {})[1]).toBe(root)
  })
})

describe('RG1: what the client hands the transport', () => {
  it('sends the root as well as the argv, so the transport can set a working directory', async () => {
    const { transport, calls } = recordingTransport()
    await createClient(transport).call('/w/proj', 'stats', {})

    expect(calls).toHaveLength(1)
    expect(calls[0]?.root).toBe('/w/proj')
    expect(calls[0]?.argv).toEqual(['-C', '/w/proj', 'stats', '--json'])
  })

  it('passes a ceiling and a cancellation through untouched', async () => {
    const { transport, calls } = recordingTransport()
    // Hand-made rather than an `AbortSignal`, which this package cannot name: it has
    // neither the DOM nor Node in scope. That the real one satisfies `CancelSignal`
    // anyway is asserted in `shell`, where a real one exists.
    const signal: CancelSignal = {
      aborted: false,
      addEventListener: () => {},
      removeEventListener: () => {},
    }
    await createClient(transport).call('/w', 'lint', {}, { timeoutMs: 4000, signal })

    expect(calls[0]?.timeoutMs).toBe(4000)
    expect(calls[0]?.signal).toBe(signal)
  })

  it('omits what the caller did not ask for instead of sending undefined', async () => {
    const { transport, calls } = recordingTransport()
    await createClient(transport).call('/w', 'lint', {})

    expect(Object.hasOwn(calls[0] ?? {}, 'timeoutMs')).toBe(false)
    expect(Object.hasOwn(calls[0] ?? {}, 'signal')).toBe(false)
  })
})

describe('RG66: the shape a verb declares, applied by the call itself', () => {
  /** One answer, as a transport that always says it. */
  const answering = (stdout: string, code = 0): Transport => ({
    run: vi.fn((): Promise<EngineResult> =>
      Promise.resolve({ code, stdout, stderr: '', durationMs: 7 }),
    ),
  })

  const LINTED = JSON.stringify({
    root: '/w',
    clean: false,
    checked: ['docs/ROADMAP.md'],
    lines: 12,
    sections: 3,
    problems: 1,
    findings: [],
  })

  it('hands back the payload rather than stdout for somebody to interpret', async () => {
    const answer = await createClient(answering(LINTED)).call('/w', 'lint', {})

    expect(answer.ok).toBe(true)
    if (!answer.ok || answer.value.kind !== 'payload') return
    expect(answer.value.value.clean).toBe(false)
    expect(answer.value.value.checked).toEqual(['docs/ROADMAP.md'])
  })

  it('reads a non-zero exit as an answer, because `lint` exits 1 by design', async () => {
    const answer = await createClient(answering(LINTED, 1)).call('/w', 'lint', {})

    // The exit code never reaches this decision: `said` is what tells a refusal apart, and
    // reading the code as a verdict is how a gate's own findings become an error.
    expect(answer.ok && answer.value.kind).toBe('payload')
  })

  it('tells a refusal from a payload without the caller asking', async () => {
    const refused = JSON.stringify({
      refused: [{ code: 'id.unknown', field: 'id', message: 'no such line' }],
      said: 'roadkeep: RG9999 is not a line here',
    })
    const answer = await createClient(answering(refused, 2)).call('/w', 'show', { id: 'RG9999' })

    expect(answer.ok).toBe(true)
    if (!answer.ok || answer.value.kind !== 'refused') return
    expect(answer.value.refusal.refused[0]?.code).toBe('id.unknown')
  })

  it('names the field it could not read, rather than handing back a string', async () => {
    const answer = await createClient(answering(LINTED.replace('false', '"no"'))).call(
      '/w',
      'lint',
      {},
    )

    expect(answer.ok).toBe(false)
    if (answer.ok) return
    expect(answer.failure.path).toBe('clean')
    expect(answer.failure.expected).toBe('a boolean')
  })

  it('reads each verb with its own shape and never a neighbour’s', async () => {
    // A `pick` payload is not a `list` payload. Before the two tables were joined the
    // reader came from the call site, so reading one with the other's shape compiled.
    const picked = JSON.stringify({
      pick: null,
      tier: '',
      reason: 'nothing is ready',
      ready: 0,
      blocked: 0,
      outside: 0,
      paused: 0,
    })
    const client = createClient(answering(picked))

    const asPick = await client.call('/w', 'pick', {})
    const asList = await client.call('/w', 'list', {})

    expect(asPick.ok).toBe(true)
    expect(asList.ok).toBe(false)
  })
})
