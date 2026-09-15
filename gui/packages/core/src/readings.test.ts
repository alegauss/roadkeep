import { describe, expect, it } from 'vitest'

import type { RecordedProject } from './catalogue'
import { DECLARES_NOTHING, type PickPayload, type StatsPayload } from './payloads'
import {
  NOTHING_REMEMBERED,
  READINGS_VERSION,
  readingOf,
  readingsFrom,
  readingStands,
  rememberedRow,
  remembering,
  type ProjectReading,
} from './readings'

/**
 * RG251: what a verb printed, kept between launches.
 *
 * What is held is that a row is rebuilt from payloads rather than stored as a row, that an
 * entry is replaced per project and keeps the half a read did not answer, and that a file
 * written by another build is refused whole rather than drawn as current.
 */

const project: RecordedProject = {
  path: '/code/alpha',
  aliases: [],
  commonDir: null,
  root: '/code',
  confirmed: '',
  presence: 'present',
  branch: 'main',
  declared: DECLARES_NOTHING,
}

const STATS: StatsPayload = {
  file: 'docs/ROADMAP.md',
  total: 60,
  uncounted: 0,
  markers: { '📋': 11 },
  startable: { open: 60, startable: 58, waiting: 2, absent: [] },
  blocks: [],
}

const PICK: PickPayload = {
  pick: { id: 'RG45', block: 'G', status: '💭', symptom: 'nothing watches', ref: 'RG45' },
  tier: 'lowest-ready-id',
  reason: 'lowest ready id',
  ready: 26,
  blocked: 28,
  outside: 0,
  paused: 0,
}

const READ = '2026-09-15T10:00:00.000Z'

const reading = (over: Partial<ProjectReading> = {}): ProjectReading => ({
  root: '/code/alpha',
  stamp: 'stamp-a',
  read: READ,
  governed: ['docs/ROADMAP.md'],
  stats: STATS,
  pick: PICK,
  engines: null,
  declares: null,
  gate: null,
  ...over,
})

describe('RG251: a row rebuilt from what a verb printed', () => {
  it('draws the counts and the next line the payloads carry, and says when they were read', () => {
    const row = rememberedRow(project, reading())

    expect(row.state).toBe('remembered')
    expect(row.counts?.total).toBe(60)
    expect(row.next?.id).toBe('RG45')
    expect(row.read).toBe(READ)
    // The record's own fields are still the record's: a remembered row is not a stale name.
    expect(row.branch).toBe('main')
  })

  it('draws what a reading does not carry as nothing, never as a number of its own', () => {
    const row = rememberedRow(project, reading({ stats: null, pick: null }))

    expect(row.counts).toBeNull()
    expect(row.next).toBeNull()
  })
})

describe('RG251: folding one project’s answers in', () => {
  it('replaces that project and leaves the rest alone', () => {
    const kept = remembering(
      { version: READINGS_VERSION, projects: [reading(), reading({ root: '/code/beta' })] },
      reading({ read: '2026-09-15T11:00:00.000Z' }),
    )

    expect(kept.projects).toHaveLength(2)
    expect(readingOf(kept, '/code/alpha')?.read).toBe('2026-09-15T11:00:00.000Z')
    expect(readingOf(kept, '/code/beta')?.read).toBe(READ)
  })

  it('keeps the half this read did not answer, since stats and pick arrive apart', () => {
    const had = remembering(NOTHING_REMEMBERED, reading())

    const after = remembering(had, reading({ pick: null, read: 'later' }))

    expect(readingOf(after, '/code/alpha')?.pick).toEqual(PICK)
    expect(readingOf(after, '/code/alpha')?.read).toBe('later')
  })

  it('drops what it held where the files have moved under it', () => {
    const had = remembering(NOTHING_REMEMBERED, reading())

    const after = remembering(had, reading({ stamp: 'stamp-b', pick: null }))

    // The stamp is the whole guarantee: an answer read off files that changed is not an
    // answer about these files, and half of one is worse than none.
    expect(readingOf(after, '/code/alpha')?.pick).toBeNull()
    expect(readingOf(after, '/code/alpha')?.stats).toEqual(STATS)
  })

  it('compares roots the way the caller compares them', () => {
    const had = remembering(NOTHING_REMEMBERED, reading({ root: 'D:/code/alpha' }))

    const after = remembering(had, reading({ root: 'd:/CODE/alpha', read: 'later' }), (path) =>
      path.toLowerCase(),
    )

    expect(after.projects).toHaveLength(1)
  })
})

describe('RG251: reading a file back', () => {
  it('reads what it wrote', () => {
    const written = remembering(NOTHING_REMEMBERED, reading())

    const back = readingsFrom(JSON.stringify(written))

    // Field by field rather than whole: a payload comes back through its own reader, which
    // fills what the engine leaves out — so the answer is the shape this app reads, not the
    // bytes it happened to write.
    const one = readingOf(back ?? NOTHING_REMEMBERED, '/code/alpha')
    expect(one?.stamp).toBe('stamp-a')
    expect(one?.read).toBe(READ)
    expect(one?.governed).toEqual(['docs/ROADMAP.md'])
    expect(one?.stats).toEqual(STATS)
    expect(one?.pick?.pick?.id).toBe('RG45')
  })

  it('refuses a version this build does not know, rather than drawing it', () => {
    const written = { ...remembering(NOTHING_REMEMBERED, reading()), version: READINGS_VERSION + 1 }

    expect(readingsFrom(JSON.stringify(written))).toBeNull()
  })

  it('refuses a shape it cannot read, and text that is not JSON at all', () => {
    expect(readingsFrom('{"version":1,"projects":[{"stamp":"a"}]}')).toBeNull()
    expect(readingsFrom('not json')).toBeNull()
  })
})

describe('RG252: whether a remembered reading still answers', () => {
  const ENGINES = {
    writing: { version: '0.2.473', home: '/engines/one', revision: 'abc1234', onDisk: '0.2.473' },
    invoke: 'python /code/launch.py',
    declaration: '',
    verdict: 'agreed',
    agree: true,
    readable: true,
    split: false,
    swapped: false,
  }
  const kept = reading({ engines: ENGINES })

  it('stands where the files and the copy that would answer are both the ones it came from', () => {
    expect(readingStands(kept, ENGINES, 'stamp-a')).toBe('stands')
    // What that build read about the machine is not what it would answer about this project.
    expect(readingStands(kept, { ...ENGINES, verdict: 'split', agree: false }, 'stamp-a')).toBe(
      'stands',
    )
  })

  it('says the files moved where the stamp is not the one it was read off', () => {
    expect(readingStands(kept, ENGINES, 'stamp-b')).toBe('files-moved')
    // Nothing stamped it, so nothing can check it.
    expect(readingStands(kept, ENGINES, '')).toBe('files-moved')
  })

  it('says the engine moved where another copy would answer now', () => {
    // An upgrade while the app was closed changes answers without moving a file, which is
    // what `No engine the reader cannot name` is about.
    const upgraded = { ...ENGINES, writing: { ...ENGINES.writing, version: '0.2.480' } }
    expect(readingStands(kept, upgraded, 'stamp-a')).toBe('engine-moved')

    const elsewhere = { ...ENGINES, invoke: 'roadkeep' }
    expect(readingStands(kept, elsewhere, 'stamp-a')).toBe('engine-moved')

    // And where nothing resolved at all, there is no copy to agree with.
    expect(readingStands(kept, null, 'stamp-a')).toBe('engine-moved')
  })

  it('says nothing is remembered where there is no entry, no stamp or no engine', () => {
    expect(readingStands(null, ENGINES, 'stamp-a')).toBe('nothing-remembered')
    expect(readingStands(reading({ stamp: '', engines: ENGINES }), ENGINES, 'x')).toBe(
      'nothing-remembered',
    )
    expect(readingStands(reading({ engines: null }), ENGINES, 'stamp-a')).toBe('nothing-remembered')
  })
})
