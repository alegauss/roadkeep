import {
  coversEverything,
  createCachingTransport,
  createClient,
  search,
  type SearchableProject,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { liveEngine as counted, read, REPO } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * Search over two real backlogs. The point being checked is not that substring matching
 * works — the unit tests hold that — but that it runs over payloads already held and does
 * not go back to the engine, which is what makes it usable while somebody types.
 */

let calls = 0
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
  return (await read(projectPath, 'list', {}, { client })).tasks
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

/** Every word a line carries anywhere, which is more than what `search` reads and is meant to be. */
function wordsIn(line: unknown): string[] {
  return (
    JSON.stringify(line)
      .toLowerCase()
      .match(/[a-z]{2,}/g) ?? []
  )
}

/**
 * A word this repository's backlog has and the fixture's has not, taken from the data.
 *
 * Written down, it is a word that ships. This searched for `renderer` until the last line
 * whose symptom carried it left the roadmap for the changelog, and then failed for a reason
 * that had nothing to do with searching — the same lesson the id below already records.
 * Chosen against both backlogs because what is asserted is that every hit is this one's.
 */
function onlyHereWord(): string {
  const theirs = new Set((projects[1]?.lines ?? []).flatMap(wordsIn))
  for (const line of projects[0]?.lines ?? []) {
    for (const word of wordsIn(line)) {
      if (word.length > 5 && !theirs.has(word)) return word
    }
  }
  throw new Error('every word in this backlog is also in the fixture, which cannot be')
}

describe('RG20: searching two real backlogs', () => {
  it('finds a line in this repository by a word in its symptom', () => {
    const answer = search(projects, onlyHereWord())

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
    for (const query of [onlyHereWord(), 'gate', 'question', 'nothing at all matches this']) {
      search(projects, query)
    }

    // Free on a warm list. A search that spawned seventeen processes per keystroke is one
    // nobody would type into.
    expect(calls).toBe(before)
  })

  it('names a project it could not cover', () => {
    const answer = search(
      [...projects, { path: '/code/never-read', name: 'never-read', lines: null }],
      onlyHereWord(),
    )

    expect(answer.unsearched).toEqual(['/code/never-read'])
    expect(coversEverything(answer)).toBe(false)
    expect(answer.searched).toBe(2)
  })
})
