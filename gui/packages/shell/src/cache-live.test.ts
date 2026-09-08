import { appendFileSync } from 'node:fs'
import path from 'node:path'

import {
  createCachingTransport,
  createClient,
  governedFiles,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { stampGoverned } from './governed-stamp'
import { createProcessTransport } from './process-transport'

/**
 * RG7 against a real project: the cache has to save actual interpreter starts, and it has
 * to stop saving them the moment a governed file moves. Both halves are only true together
 * — a cache that never expires is fast and wrong, and one that never hits is neither.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })

/** Wraps the real transport and counts how many calls actually reach it. */
function counted(inner: Transport): { transport: Transport; calls: () => number } {
  let calls = 0
  return {
    calls: () => calls,
    transport: {
      run(request: EngineRequest): Promise<EngineResult> {
        calls += 1
        return inner.run(request)
      },
    },
  }
}

let fixture: Fixture
let governed: string[] = []

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 1, deferred: 0 })

  const config = await createClient(engine).call(fixture.root, 'config', {}, { timeoutMs: CEILING })
  if (!config.ok || config.value.kind === 'refused') {
    throw new Error('config did not answer with a payload')
  }
  governed = Object.values(governedFiles(config.value.value))
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG7: the files a project declares', () => {
  it('are read off the engine rather than out of the toml', () => {
    // Five roles for a fixture scaffolded with --deferred. If this is empty the cache key
    // is a constant, which is a cache that never expires.
    expect(governed.length).toBeGreaterThanOrEqual(3)
    expect(governed.some((file) => file.includes('ROADMAP'))).toBe(true)
  })
})

describe('RG7: a read that does not happen twice', () => {
  it('serves a repeat without starting another interpreter', async () => {
    const { transport, calls } = counted(engine)
    const cache = createCachingTransport(transport, {
      stampFor: (root) => Promise.resolve(stampGoverned(root, governed)),
      cacheable: () => true,
    })
    const client = createClient(cache)

    const first = await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })
    const second = await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })

    expect(calls()).toBe(1)
    // The same answer, and a real one: a cache handing back a shape it invented would be
    // caught by the verb's own reader before the equality below could hide it.
    expect(first.ok && first.value.kind).toBe('payload')
    expect(second).toEqual(first)
  })

  it('reads again once a governed file has been written', async () => {
    const { transport, calls } = counted(engine)
    const cache = createCachingTransport(transport, {
      stampFor: (root) => Promise.resolve(stampGoverned(root, governed)),
      cacheable: () => true,
    })
    const client = createClient(cache)

    await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })
    // A write by anything at all — this app, a terminal, an agent — expires it the same
    // way, because what is keyed is the file and not who touched it.
    appendFileSync(path.join(fixture.root, 'docs', 'ROADMAP.md'), '\n')

    await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })

    expect(calls()).toBe(2)
  })
})
