import path from 'node:path'

import {
  coversEverything,
  createCachingTransport,
  createClient,
  readListPayload,
  readPayload,
  search,
  type SearchableProject,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * Search over two real backlogs. The point being checked is not that substring matching
 * works — the unit tests hold that — but that it runs over payloads already held and does
 * not go back to the engine, which is what makes it usable while somebody types.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

let calls = 0
const counted = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const engine = createCachingTransport(
  {
    run: (request) => {
      calls += 1
      return counted.run(request)
    },
  },
  { stampFor: () => Promise.resolve('live'), cacheable: () => false },
)
const client = createClient(engine)

let fixture: Fixture
let projects: SearchableProject[] = []

async function linesOf(projectPath: string) {
  const result = await client.call(projectPath, 'list', {}, { timeoutMs: CEILING })
  const parsed = readPayload(readListPayload, result.stdout, { verb: 'list', engineVersion: '' })
  if (!parsed.ok) throw new Error('list did not answer with a payload')
  return parsed.value.tasks
}

beforeAll(async () => {
  fixture = await buildFixture(counted, { open: 3, shipped: 1, deferred: 0 })
  projects = [
    { path: REPO, name: 'roadkeep-gui', lines: await linesOf(REPO) },
    { path: fixture.root, name: 'fixture', lines: await linesOf(fixture.root) },
  ]
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG20: searching two real backlogs', () => {
  it('finds a line in this repository by a word in its symptom', () => {
    const answer = search(projects, 'renderer')

    expect(answer.hits.length).toBeGreaterThan(0)
    expect(answer.hits.every((hit) => hit.project === REPO)).toBe(true)
    expect(coversEverything(answer)).toBe(true)
  })

  it('finds a line in the fixture, which is a different backlog', () => {
    const answer = search(projects, 'question')

    expect(answer.hits.length).toBeGreaterThan(0)
    expect(answer.hits.some((hit) => hit.project === fixture.root)).toBe(true)
  })

  it('finds a line by an id from either prefix', () => {
    // Taken from the data rather than written down: an id hardcoded here is one that
    // ships and leaves the roadmap for the changelog, and this test hardcoded RG44 on the
    // day RG44 shipped.
    for (const project of projects) {
      const first = project.lines?.[0]
      expect(first).toBeDefined()
      if (!first) continue

      const answer = search(projects, first.id)
      expect(answer.hits.map((hit) => hit.line.id)).toContain(first.id)
    }
  })

  it('costs no engine calls at all', () => {
    const before = calls
    for (const query of ['renderer', 'gate', 'question', 'nothing at all matches this']) {
      search(projects, query)
    }

    // Free on a warm list. A search that spawned seventeen processes per keystroke is one
    // nobody would type into.
    expect(calls).toBe(before)
  })

  it('names a project it could not cover', () => {
    const answer = search(
      [...projects, { path: '/code/never-read', name: 'never-read', lines: null }],
      'renderer',
    )

    expect(answer.unsearched).toEqual(['/code/never-read'])
    expect(coversEverything(answer)).toBe(false)
    expect(answer.searched).toBe(2)
  })
})
