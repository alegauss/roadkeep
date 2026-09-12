import { describe, expect, it } from 'vitest'

import { agentCandidates, agentOverride } from './agent-candidates'
import { CAPTURED_STREAM, scriptedLines } from './scripted-agent'

import { readFileSync } from 'node:fs'

/**
 * RG210: an agent somebody points an unpackaged window at, and the run it replays.
 */

describe('RG210: which agent a variable names', () => {
  it('reads a JSON argv, a path with a space staying one element', () => {
    expect(
      agentOverride('["C:\\\\Program Files\\\\nodejs\\\\node.exe","claude.mjs"]', false),
    ).toEqual(['C:\\Program Files\\nodejs\\node.exe', 'claude.mjs'])
  })

  it('is ignored by a packaged build, whatever it says', () => {
    // A shipped window never runs an agent a variable chose.
    expect(agentOverride('["node","claude.mjs"]', true)).toBeNull()
  })

  it('ignores anything that is not a non-empty list of words, rather than guessing', () => {
    for (const value of [
      undefined,
      '',
      'node claude.mjs',
      '[]',
      '[1]',
      '["node", ""]',
      '{"a":1}',
    ]) {
      expect(agentOverride(value, false)).toBeNull()
    }
  })

  it('goes before every other candidate, and changes nothing where there is none', () => {
    const home = 'Z:\\nobody-lives-here'

    expect(agentCandidates({ home, override: ['node', 'claude.mjs'] })).toEqual([
      ['node', 'claude.mjs'],
      ['claude'],
    ])
    expect(agentCandidates({ home, override: null })).toEqual([['claude']])
  })
})

describe('RG210: the run a scripted agent replays', () => {
  const captured = readFileSync(CAPTURED_STREAM, 'utf8')

  it('keeps the captured run and leaves out its result, so the session never reads as done', () => {
    const lines = scriptedLines(captured, 0)

    expect(lines.length).toBeGreaterThan(5)
    expect(
      lines.some((line) => line.includes('"type": "result"') || line.includes('"type":"result"')),
    ).toBe(false)
  })

  it('adds as many acts after it as it was asked for, with notes and calls among them', () => {
    const lines = scriptedLines(captured, 10)
    const tail = lines.slice(-10)

    expect(lines).toHaveLength(scriptedLines(captured, 0).length + 10)
    expect(tail.some((line) => line.includes('rate_limit_event'))).toBe(true)
    expect(tail.some((line) => line.includes('tool_use'))).toBe(true)
  })
})
