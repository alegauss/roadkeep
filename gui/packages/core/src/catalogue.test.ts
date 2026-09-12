import { describe, expect, it } from 'vitest'

import {
  CATALOGUE_VERSION,
  catalogueFrom,
  EMPTY_CATALOGUE,
  present,
  reconcile,
  rowsFrom,
  type ProjectCatalogue,
  type RecordedProject,
} from './catalogue'
import type { ProjectFamily } from './families'
import type { ScanRoot } from './roots'
import { DECLARES_NOTHING } from './payloads'

const keyOf = (path: string) => path.toLowerCase()

/** One timestamp, so a fold's dates are the test's and not the clock's. */
const NOW = '2026-09-12T12:00:00.000Z'
const ROOTS: ScanRoot[] = [{ path: '/code', depth: 2 }]
const TUESDAY = '2026-09-01T10:00:00.000Z'
const FRIDAY = '2026-09-04T10:00:00.000Z'

const seen = (path: string, over: Partial<RecordedProject> = {}): RecordedProject => ({
  path,
  aliases: [],
  commonDir: null,
  root: '/code',
  confirmed: TUESDAY,
  presence: 'present',
  branch: '',
  declared: DECLARES_NOTHING,
  ...over,
})

const recordOf = (projects: RecordedProject[]): ProjectCatalogue => ({
  version: CATALOGUE_VERSION,
  roots: ROOTS,
  projects,
})

describe('RG14: turning a scan into rows', () => {
  it('gives one row per member and carries the family down', () => {
    const families: ProjectFamily[] = [
      {
        commonDir: '/code/turing/2026.3/.git',
        members: [
          { path: '/code/turing/2026.3', aliases: ['/code/turing/latest'], branch: '' },
          { path: '/code/turing/2026.2', aliases: [], branch: '' },
        ],
      },
      { commonDir: null, members: [{ path: '/code/plain', aliases: [], branch: '' }] },
    ]

    const rows = rowsFrom(families, () => '/code', FRIDAY)

    expect(rows.map((row) => row.path)).toEqual([
      '/code/turing/2026.3',
      '/code/turing/2026.2',
      '/code/plain',
    ])
    expect(rows[0]?.commonDir).toBe('/code/turing/2026.3/.git')
    expect(rows[0]?.aliases).toEqual(['/code/turing/latest'])
    expect(rows[2]?.commonDir).toBeNull()
  })
})

describe('RG14: a rescan is a diff', () => {
  it('reports nothing changed when nothing did', () => {
    const before = recordOf([seen('/code/a'), seen('/code/b')])

    const { changes } = reconcile(before, ROOTS, [seen('/code/a'), seen('/code/b')], keyOf, FRIDAY)

    expect(changes).toEqual([])
  })

  it('moves the confirmed time forward for a project still there', () => {
    const before = recordOf([seen('/code/a')])

    const { catalogue } = reconcile(before, ROOTS, [seen('/code/a')], keyOf, FRIDAY)

    expect(catalogue.projects[0]?.confirmed).toBe(FRIDAY)
  })

  it('appends a project that was not on the list', () => {
    const before = recordOf([seen('/code/a')])

    const { catalogue, changes } = reconcile(
      before,
      ROOTS,
      [seen('/code/a'), seen('/code/new')],
      keyOf,
      FRIDAY,
    )

    expect(changes).toEqual([{ kind: 'added', path: '/code/new' }])
    // Appended, not inserted: the thing somebody clicked yesterday stays where it was.
    expect(catalogue.projects.map((p) => p.path)).toEqual(['/code/a', '/code/new'])
  })

  it('keeps the record order rather than the scan order', () => {
    const before = recordOf([seen('/code/z'), seen('/code/a')])

    const { catalogue } = reconcile(
      before,
      ROOTS,
      [seen('/code/a'), seen('/code/z')],
      keyOf,
      FRIDAY,
    )

    expect(catalogue.projects.map((p) => p.path)).toEqual(['/code/z', '/code/a'])
  })

  it('refreshes the family of a project that moved between worktrees', () => {
    const before = recordOf([seen('/code/a', { commonDir: null, aliases: [] })])

    const { catalogue } = reconcile(
      before,
      ROOTS,
      [seen('/code/a', { commonDir: '/code/a/.git', aliases: ['/code/latest'] })],
      keyOf,
      FRIDAY,
    )

    expect(catalogue.projects[0]?.commonDir).toBe('/code/a/.git')
    expect(catalogue.projects[0]?.aliases).toEqual(['/code/latest'])
  })
})

describe('RG14: a project the rescan did not find', () => {
  it('is marked missing and kept', () => {
    // Deleted and not-mounted look identical from here, and only one of them is a
    // removal. This app does not get to decide which happened.
    const before = recordOf([seen('/code/a'), seen('/on-a-usb-stick/b')])

    const { catalogue, changes } = reconcile(before, ROOTS, [seen('/code/a')], keyOf, FRIDAY)

    expect(catalogue.projects).toHaveLength(2)
    expect(catalogue.projects[1]?.presence).toBe('missing')
    expect(changes).toEqual([{ kind: 'missing', path: '/on-a-usb-stick/b' }])
  })

  it('keeps the time it was last actually seen', () => {
    // Moving `confirmed` for a project nobody found would say it is still there.
    const before = recordOf([seen('/gone', { confirmed: TUESDAY })])

    const { catalogue } = reconcile(before, ROOTS, [], keyOf, FRIDAY)

    expect(catalogue.projects[0]?.confirmed).toBe(TUESDAY)
  })

  it('reports it as missing once, not on every launch after', () => {
    const before = recordOf([seen('/gone', { presence: 'missing' })])

    expect(reconcile(before, ROOTS, [], keyOf, FRIDAY).changes).toEqual([])
  })

  it('says so when it comes back', () => {
    const before = recordOf([seen('/back', { presence: 'missing', confirmed: TUESDAY })])

    const { catalogue, changes } = reconcile(before, ROOTS, [seen('/back')], keyOf, FRIDAY)

    expect(changes).toEqual([{ kind: 'returned', path: '/back' }])
    expect(catalogue.projects[0]?.presence).toBe('present')
    expect(catalogue.projects[0]?.confirmed).toBe(FRIDAY)
  })

  it('is left out of what is worth reading, without leaving the list', () => {
    const before = recordOf([seen('/here'), seen('/gone', { presence: 'missing' })])

    expect(present(before).map((p) => p.path)).toEqual(['/here'])
    expect(before.projects).toHaveLength(2)
  })
})

describe('RG14: the first launch', () => {
  it('starts from an empty record and fills it', () => {
    const { catalogue, changes } = reconcile(
      EMPTY_CATALOGUE,
      ROOTS,
      [seen('/code/a')],
      keyOf,
      FRIDAY,
    )

    expect(changes).toEqual([{ kind: 'added', path: '/code/a' }])
    expect(catalogue.roots).toEqual(ROOTS)
  })
})

describe('RG14: reading a record back', () => {
  it('round-trips what it wrote', () => {
    const before = recordOf([seen('/code/a', { aliases: ['/code/latest'] })])

    expect(catalogueFrom(JSON.stringify(before))).toEqual(before)
  })

  it('answers nothing for a record of a shape this build does not know', () => {
    // Drawing an older shape as though it were current is worse than rebuilding it: the
    // scan running behind is about to replace it anyway.
    const before = { ...recordOf([seen('/code/a')]), version: 99 }

    expect(catalogueFrom(JSON.stringify(before))).toBeNull()
  })

  it.each([
    ['not json', 'nonsense'],
    ['a record with no projects key', '{"version":1,"roots":[]}'],
  ])('answers nothing for %s', (_case, text) => {
    expect(catalogueFrom(text)).toBeNull()
  })

  it('refuses a presence it does not recognise, naming the field', () => {
    const broken = JSON.stringify({
      version: CATALOGUE_VERSION,
      roots: [],
      projects: [{ ...seen('/code/a'), presence: 'maybe' }],
    })

    expect(catalogueFrom(broken)).toBeNull()
  })
})

describe('RG203: a missing project keeps its name', () => {
  const named = (path: string, name: string, presence: 'present' | 'missing'): RecordedProject => ({
    path,
    aliases: [],
    commonDir: null,
    root: '/code',
    confirmed: '2026-09-01T10:00:00.000Z',
    presence,
    branch: '',
    declared: { ...DECLARES_NOTHING, name },
  })

  const scanned = (path: string): RecordedProject => ({
    ...named(path, '', 'present'),
    confirmed: '',
  })

  it('keeps what a project last declared when the scan cannot find it', () => {
    const held = {
      version: CATALOGUE_VERSION,
      roots: [],
      projects: [named('/code/a', 'Turing', 'present')],
    }

    const { catalogue } = reconcile(held, [], [], keyOf, NOW)

    expect(catalogue.projects[0]?.presence).toBe('missing')
    // The moment a row goes grey is the worst one for it to change identity: *last seen on
    // Tuesday* about a name nobody recognises says nothing.
    expect(catalogue.projects[0]?.declared.name).toBe('Turing')
  })

  it('keeps it across a scan that does find it, since a walk reads no config', () => {
    const held = {
      version: CATALOGUE_VERSION,
      roots: [],
      projects: [named('/code/a', 'Turing', 'present')],
    }

    const { catalogue } = reconcile(held, [], [scanned('/code/a')], keyOf, NOW)

    expect(catalogue.projects[0]?.presence).toBe('present')
    expect(catalogue.projects[0]?.declared.name).toBe('Turing')
  })

  it('knows nothing about a project it has just found', () => {
    // The declaration is read when a project opens, not when it is walked over.
    const { catalogue } = reconcile(EMPTY_CATALOGUE, [], [scanned('/code/new')], keyOf, NOW)

    expect(catalogue.projects[0]?.declared).toEqual(DECLARES_NOTHING)
  })
})
