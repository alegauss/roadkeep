import { describe, expect, it } from 'vitest'

import type { TaskLine } from './payloads'
import { coversEverything, search, type SearchableProject } from './search'

const line = (id: string, symptom: string, why: string): TaskLine => ({
  id,
  status: '📋',
  block: 'A',
  symptom,
  why,
  deps: [],
  ref: id,
  line: 1,
  length: 100,
})

const ROADKEEP: SearchableProject = {
  path: '/code/roadkeep-gui',
  name: 'roadkeep-gui',
  lines: [
    line('RG44', 'the renderer holds node powers', 'Context isolation off is a rewrite.'),
    line('RG45', 'nothing watches the governed files', 'A write leaves the screen stale.'),
  ],
}

const SHIO: SearchableProject = {
  path: '/code/shio',
  name: 'shio',
  lines: [line('SH12', 'the sidebar forgets its width', 'Nothing stores the panel size.')],
}

const UNREAD: SearchableProject = { path: '/code/turing', name: 'turing', lines: null }

describe('RG20: the three fields a person remembers', () => {
  it('finds a line by a word in its symptom', () => {
    const answer = search([ROADKEEP], 'renderer')

    expect(answer.hits).toHaveLength(1)
    expect(answer.hits[0]?.line.id).toBe('RG44')
    expect(answer.hits[0]?.matched).toEqual(['symptom'])
  })

  it('finds a line by a word in its why', () => {
    const answer = search([ROADKEEP], 'rewrite')

    expect(answer.hits[0]?.line.id).toBe('RG44')
    expect(answer.hits[0]?.matched).toEqual(['why'])
  })

  it('finds a line by its id', () => {
    const answer = search([ROADKEEP], 'RG45')

    expect(answer.hits[0]?.line.id).toBe('RG45')
    expect(answer.hits[0]?.matched).toEqual(['id'])
  })

  it('says every field a query touched', () => {
    // `watches` is in the symptom and `stale` in the why: one line, two reasons, and a
    // view can show which words put it there.
    const answer = search([ROADKEEP], 'watches stale')

    expect(answer.hits).toHaveLength(1)
    expect(answer.hits[0]?.matched).toEqual(['symptom', 'why'])
  })

  it('does not care about case', () => {
    expect(search([ROADKEEP], 'RENDERER').hits).toHaveLength(1)
    expect(search([ROADKEEP], 'rg44').hits).toHaveLength(1)
  })
})

describe('RG20: more than one word', () => {
  it('needs every term to appear somewhere', () => {
    expect(search([ROADKEEP], 'renderer node').hits).toHaveLength(1)
    expect(search([ROADKEEP], 'renderer sidebar').hits).toHaveLength(0)
  })

  it('lets the terms land in different fields', () => {
    expect(search([ROADKEEP], 'RG44 isolation').hits).toHaveLength(1)
  })

  it('ignores the whitespace somebody typed', () => {
    expect(search([ROADKEEP], '  renderer   node  ').hits).toHaveLength(1)
  })
})

describe('RG20: across every backlog at once', () => {
  it('searches all of them and says which project each hit came from', () => {
    const answer = search([ROADKEEP, SHIO], 'the')

    expect(answer.hits.map((hit) => hit.name)).toEqual([
      'roadkeep-gui',
      'roadkeep-gui',
      'shio',
    ])
    expect(answer.searched).toBe(2)
  })

  it('keeps the project order and then the file order', () => {
    // No relevance ranking: a score would be a number this app invented, sorted above
    // numbers a verb printed.
    const answer = search([SHIO, ROADKEEP], 'the')

    expect(answer.hits.map((hit) => hit.line.id)).toEqual(['SH12', 'RG44', 'RG45'])
  })
})

describe('RG20: the projects an answer does not cover', () => {
  it('names a project with nothing held rather than skipping it', () => {
    // An empty answer is exactly when somebody concludes the task does not exist, so an
    // answer covering eleven of seventeen backlogs has to say so.
    const answer = search([ROADKEEP, UNREAD], 'sidebar')

    expect(answer.hits).toHaveLength(0)
    expect(answer.unsearched).toEqual(['/code/turing'])
    expect(coversEverything(answer)).toBe(false)
  })

  it('says an answer is complete when everything was searched', () => {
    expect(coversEverything(search([ROADKEEP, SHIO], 'width'))).toBe(true)
  })

  it('counts only what it actually looked at', () => {
    const answer = search([ROADKEEP, SHIO, UNREAD], 'the')

    expect(answer.searched).toBe(2)
    expect(answer.unsearched).toHaveLength(1)
  })
})

describe('RG20: an empty query', () => {
  it('finds nothing rather than everything', () => {
    // A search box with nothing typed in it should show nothing, not nine hundred lines.
    expect(search([ROADKEEP, SHIO], '').hits).toEqual([])
    expect(search([ROADKEEP, SHIO], '   ').hits).toEqual([])
  })

  it('still reports what it would have covered', () => {
    const answer = search([ROADKEEP, UNREAD], '')

    expect(answer.searched).toBe(1)
    expect(answer.unsearched).toEqual(['/code/turing'])
  })
})

describe('RG20: nothing to search', () => {
  it('answers empty for no projects', () => {
    expect(search([], 'anything')).toEqual({
      query: 'anything',
      hits: [],
      unsearched: [],
      searched: 0,
    })
  })

  it('answers empty for a project with no lines at all', () => {
    const answer = search([{ path: '/code/new', name: 'new', lines: [] }], 'anything')

    expect(answer.hits).toEqual([])
    expect(answer.searched).toBe(1)
    expect(coversEverything(answer)).toBe(true)
  })
})
