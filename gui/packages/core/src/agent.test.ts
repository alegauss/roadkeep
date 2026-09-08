import { describe, expect, it } from 'vitest'

import { resolveAgent, saidOfAgent, versionIn, type TransportFor } from './agent'
import { EngineCallFailed, type EngineResult, type Transport } from './transport'

/** What a real `claude --version` printed on the machine this was written on. */
const SAID = '2.1.263 (Claude Code)'

function answering(byCommand: Record<string, Partial<EngineResult>>): {
  transportFor: TransportFor
  asked: string[][]
} {
  const asked: string[][] = []
  return {
    asked,
    transportFor: (command) => {
      const transport: Transport = {
        run(request) {
          asked.push([...command, ...request.argv])
          const answer = byCommand[command.join(' ')]
          if (answer === undefined) {
            return Promise.reject(new EngineCallFailed('unspawnable', 'not found', 2))
          }
          return Promise.resolve({ code: 0, stdout: '', stderr: '', durationMs: 4, ...answer })
        },
      }
      return transport
    },
  }
}

describe('RG43: the version out of a line of prose', () => {
  it('lifts a dotted version out of what --version printed', () => {
    // There is no `--json` here, so the line is all there is.
    expect(versionIn(SAID)).toBe('2.1.263')
    expect(versionIn('claude 3.0.0-beta.2 (Claude Code)')).toBe('3.0.0-beta.2')
  })

  it('answers nothing where the line held no version, rather than guessing', () => {
    expect(versionIn('Claude Code')).toBe('')
    expect(versionIn('')).toBe('')
    expect(versionIn('2.1')).toBe('')
  })
})

describe('RG43: resolving the command that runs a session', () => {
  it('takes the first candidate that answers, and records what it said', async () => {
    const { transportFor, asked } = answering({ claude: { stdout: `${SAID}\n` } })

    const resolution = await resolveAgent(transportFor, '/w', [['claude'], ['/opt/claude']])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') throw new Error('unreachable')
    expect(resolution.agent.command).toEqual(['claude'])
    expect(resolution.agent.version).toBe('2.1.263')
    expect(resolution.agent.said).toBe(SAID)
    // It stopped at the first answer rather than asking everything.
    expect(asked).toEqual([['claude', '--version']])
  })

  it('moves on from a candidate that cannot be spawned', async () => {
    const { transportFor, asked } = answering({ '/opt/claude': { stdout: SAID } })

    const resolution = await resolveAgent(transportFor, '/w', [['claude'], ['/opt/claude']])

    expect(resolution.kind === 'resolved' && resolution.agent.command).toEqual(['/opt/claude'])
    expect(asked).toHaveLength(2)
  })

  it('moves on from one that answers with a non-zero exit', async () => {
    // A command that ran and is not this one. The next candidate gets its turn.
    const { transportFor } = answering({
      claude: { code: 1, stdout: 'unknown option --version' },
      '/opt/claude': { stdout: SAID },
    })

    const resolution = await resolveAgent(transportFor, '/w', [['claude'], ['/opt/claude']])

    expect(resolution.kind === 'resolved' && resolution.agent.command).toEqual(['/opt/claude'])
  })

  it('resolves a build whose version it could not read, keeping the line', async () => {
    // The bargain: a version this app cannot parse loses a label and never the binary.
    const { transportFor } = answering({ claude: { stdout: 'Claude Code (dev build)' } })

    const resolution = await resolveAgent(transportFor, '/w', [['claude']])

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') throw new Error('unreachable')
    expect(resolution.agent.version).toBe('')
    expect(resolution.agent.said).toBe('Claude Code (dev build)')
    expect(saidOfAgent(resolution)).toBe('claude — Claude Code (dev build)')
  })
})

describe('RG43: a machine without one is a stated condition', () => {
  it('names everything it looked for, so the reason can be shown', async () => {
    // The difference between "no Claude Code here" and a spawn that failed with a number.
    const { transportFor } = answering({})

    const resolution = await resolveAgent(transportFor, '/w', [['claude'], ['/opt/claude']])

    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') throw new Error('unreachable')
    expect(resolution.tried).toEqual([['claude'], ['/opt/claude']])
    expect(resolution.reason).toContain('claude')
    expect(resolution.reason).toContain('/opt/claude')
    expect(saidOfAgent(resolution)).toBe(resolution.reason)
  })

  it('says so plainly when nothing was even offered to try', async () => {
    const { transportFor } = answering({})

    const resolution = await resolveAgent(transportFor, '/w', [])

    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') throw new Error('unreachable')
    expect(resolution.tried).toEqual([])
    expect(resolution.reason).toContain('no session can be started')
  })

  it('states what it found, for a screen to say before anybody asks', async () => {
    const { transportFor } = answering({ claude: { stdout: SAID } })

    expect(saidOfAgent(await resolveAgent(transportFor, '/w', [['claude']]))).toBe(
      'claude — 2.1.263',
    )
  })
})
