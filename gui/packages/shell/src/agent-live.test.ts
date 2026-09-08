import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { resolveAgent, saidOfAgent } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { agentCandidates } from './agent-candidates'
import { createProcessTransport } from './process-transport'

/**
 * Resolving the real Claude Code on this machine.
 *
 * `--version` starts a process and prints a line; it is not a session and costs nothing,
 * which is what makes this the one part of the agent surface worth running for real.
 *
 * Where the machine has none, the unresolved answer is what is asserted — and that half is
 * made rather than waited for, since a machine without Claude Code is not something a test
 * run can arrange.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CEILING = 30000

const transportFor = (command: readonly string[]) =>
  createProcessTransport({ command: command[0] ?? '', prefixArgs: command.slice(1) })

const homes: string[] = []

afterAll(() => {
  for (const home of homes) rmSync(home, { recursive: true, force: true })
})

describe('RG43: what this machine has', () => {
  it('says which and what version, or names everything it looked for', async () => {
    // Both machines this runs on are real: a developer's has Claude Code installed and a CI
    // runner does not, and RG55 is where that stopped being a thing only one of them knew.
    // So the answer is asserted whole in either branch rather than one of them being
    // assumed — a test that skipped on the runner would be the promise nobody keeps.
    const resolution = await resolveAgent(transportFor, REPO, agentCandidates(), {
      timeoutMs: CEILING,
    })

    if (resolution.kind === 'resolved') {
      expect(resolution.agent.command.length).toBeGreaterThan(0)
      // A real version, not one written here: whatever this machine has installed.
      expect(resolution.agent.version).toMatch(/^\d+\.\d+\.\d+/)
      expect(resolution.agent.said).toContain(resolution.agent.version)
      expect(saidOfAgent(resolution)).toContain(resolution.agent.version)
      return
    }

    expect(resolution.tried).toEqual(agentCandidates())
    for (const candidate of agentCandidates()) {
      expect(resolution.reason).toContain(candidate.join(' '))
    }
    expect(saidOfAgent(resolution)).toBe(resolution.reason)
  })

  it('offers what is on PATH first, because that is whose settings a session uses', () => {
    // The one the person's own shell would run, and therefore the one their
    // authentication belongs to.
    const candidates = agentCandidates()

    expect(candidates[0]).toEqual(['claude'])
  })

  it('offers an install location only where the file is actually there', () => {
    // An empty home has nothing under it, so nothing but PATH is offered.
    const home = mkdtempSync(path.join(tmpdir(), 'rk-no-claude-'))
    homes.push(home)

    expect(agentCandidates({ home })).toEqual([['claude']])
  })

  it('bundles nothing, so no candidate points inside this app', () => {
    // A `claude` shipped here would sign somebody's work in with an account they did not
    // choose. A bare name is a PATH lookup and not a path at all, so only the candidates
    // that name a file are the ones this can be about.
    for (const candidate of agentCandidates()) {
      const first = candidate[0] ?? ''
      if (!first.includes(path.sep) && !first.includes('/')) continue
      expect(path.resolve(first).startsWith(REPO)).toBe(false)
    }
  })
})

describe('RG43: a machine without one', () => {
  it('is a stated condition naming what was looked for, not a spawn that failed', async () => {
    const missing = [[path.join(REPO, 'no-claude-here')], [path.join(REPO, 'nor-here', 'claude')]]

    const resolution = await resolveAgent(transportFor, REPO, missing, { timeoutMs: CEILING })

    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') throw new Error('unreachable')
    expect(resolution.tried).toEqual(missing)
    expect(resolution.reason).toContain('no-claude-here')
    expect(resolution.reason).toContain('nor-here')
    // Sentence-shaped, because it is meant to be shown before anybody asks for a session.
    expect(saidOfAgent(resolution)).toBe(resolution.reason)
  })

  it('falls past a candidate that ran and did not answer, to one that did', async () => {
    // Two real commands: node with an unknown flag exits non-zero, which is the "ran, and
    // is not this" case, and node with `--version` exits 0, which resolves. Both are here
    // rather than the machine's own Claude Code, because whether one is installed is not
    // what this is about — and on a runner there is none.
    const failing = [process.execPath, '--definitely-not-a-node-flag']
    const answering = [process.execPath]

    const resolution = await resolveAgent(transportFor, REPO, [failing, answering], {
      timeoutMs: CEILING,
    })

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') throw new Error('unreachable')
    expect(resolution.agent.command).toEqual(answering)

    // And the fallback, which this pair reaches for real: node prints `v24.10.0`, whose
    // `v` runs into the digits so there is no word boundary and no version is lifted. The
    // binary is kept and the whole line stands in for the label — the documented answer to
    // a version this app cannot parse, exercised here by a command that genuinely has one.
    expect(resolution.agent.version).toBe('')
    expect(resolution.agent.said).not.toBe('')
    expect(saidOfAgent(resolution)).toContain(resolution.agent.said)
  })
})
