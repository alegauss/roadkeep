import path from 'node:path'

import { resolveEngine } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { COMMITTED_LAUNCHER, engineCandidates } from './engine-candidates'
import { createProcessTransport } from './process-transport'

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

describe('RG2: what is worth trying, and in what order', () => {
  it('offers this repository its own committed launcher first', () => {
    const candidates = engineCandidates(REPO)

    expect(candidates[0]).toEqual(['python', path.join(REPO, COMMITTED_LAUNCHER)])
  })

  it('offers a roadkeep on PATH last, never first', () => {
    const candidates = engineCandidates(REPO)

    // It is the one thing `engines` exists to say a project may not be running, so it is
    // a fallback and never the answer while the project declares something of its own.
    expect(candidates.at(-1)).toEqual(['roadkeep'])
    expect(candidates[0]).not.toEqual(['roadkeep'])
  })

  it('offers only PATH for a directory with no launcher', () => {
    expect(engineCandidates(path.join(REPO, 'packages'))).toEqual([['roadkeep']])
  })

  it('lets the interpreter and the PATH name be said rather than assumed', () => {
    const candidates = engineCandidates(REPO, { python: 'python3', onPath: 'rk' })

    expect(candidates[0]?.[0]).toBe('python3')
    expect(candidates.at(-1)).toEqual(['rk'])
  })
})

describe('RG2: resolving this repository against a live engine', () => {
  it('names the copy that writes for it, with its version and where it lives', async () => {
    const resolution = await resolveEngine(
      (engine) =>
        createProcessTransport({
          command: engine[0] ?? '',
          prefixArgs: engine.slice(1),
        }),
      REPO,
      engineCandidates(REPO),
      { timeoutMs: 30000 },
    )

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') return

    // This is the criterion: the copy that answered is on screen, not merely found.
    expect(resolution.engine.payload.writing.version).toMatch(/^\d+\.\d+\.\d+/)
    expect(resolution.engine.payload.writing.home).not.toBe('')
    expect(resolution.engine.payload.verdict).not.toBe('')
    expect(resolution.engine.engine.length).toBeGreaterThan(0)
  })

  it('resolves nothing, with a reason, when every candidate is missing', async () => {
    const resolution = await resolveEngine(
      (engine) =>
        createProcessTransport({
          command: engine[0] ?? '',
          prefixArgs: engine.slice(1),
        }),
      REPO,
      [['no-such-engine-anywhere']],
      { timeoutMs: 30000 },
    )

    // A machine with no Python is a real state and not a crash.
    expect(resolution.kind).toBe('unresolved')
    if (resolution.kind !== 'unresolved') return
    expect(resolution.reason).toContain('unknown')
  })
})
