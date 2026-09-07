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
    expect(buildArgv('/w', 'nonGoalList', {})).toEqual([
      '-C',
      '/w',
      'non-goal',
      'list',
      '--json',
    ])
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

  it('returns what the transport returned, parsing nothing', async () => {
    const run = vi.fn(
      (): Promise<EngineResult> =>
        Promise.resolve({ code: 1, stdout: '{"clean":false}', stderr: 'a warning', durationMs: 7 }),
    )
    const result = await createClient({ run }).call('/w', 'lint', {})

    // A non-zero exit is an answer: `lint` exits 1 by design. The client does not read it
    // as a failure, and it does not turn stdout into an object either - that is RG3's.
    expect(result).toEqual({ code: 1, stdout: '{"clean":false}', stderr: 'a warning', durationMs: 7 })
  })
})
