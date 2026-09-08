import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import {
  catalogueFrom,
  EMPTY_CATALOGUE,
  groupProjects,
  present,
  reconcile,
  rowsFrom,
  type ScanRoot,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { gitSite } from './git-worktree'
import { rootKey } from './root-paths'
import { scanRoots } from './scan-fs'

/**
 * The whole of block B end to end on a real tree: walk it, group what was found, fold that
 * into a record, then delete a project and do it again. The second pass is the one that
 * matters — a rescan is a diff, and what a diff does with a folder that went away is the
 * decision this task exists to make.
 */
let root = ''
let roots: ScanRoot[] = []

function project(relative: string): void {
  const full = path.join(root, relative)
  mkdirSync(full, { recursive: true })
  writeFileSync(path.join(full, 'roadkeep.toml'), 'prefix = "FX"', 'utf8')
}

/** Walk and fold, the way a launch would. */
async function rescan(previous = EMPTY_CATALOGUE, now = '2026-09-01T10:00:00.000Z') {
  const scanned = await scanRoots(roots)
  const families = groupProjects(
    scanned.found.map((entry) => ({ path: entry.path, ...gitSite(entry.path) })),
    rootKey,
  )
  const rootOf = (candidate: string) =>
    scanned.found.find((entry) => rootKey(entry.path) === rootKey(candidate))?.root ?? ''

  return reconcile(previous, roots, rowsFrom(families, rootOf, now), rootKey, now)
}

beforeAll(async () => {
  root = mkdtempSync(path.join(tmpdir(), 'rk-catalogue-'))
  roots = [{ path: root, depth: 2 }]
  project('org/alpha')
  project('org/beta')
})

afterAll(() => {
  rmSync(root, { recursive: true, force: true })
})

describe('RG14: a record built from a real walk', () => {
  it('finds the projects and records where each came from', async () => {
    const { catalogue, changes } = await rescan()

    expect(catalogue.projects).toHaveLength(2)
    expect(changes.every((change) => change.kind === 'added')).toBe(true)
    expect(catalogue.projects.every((entry) => entry.root === root)).toBe(true)
    expect(catalogue.roots).toEqual(roots)
  })

  it('changes nothing on a second pass over an unchanged tree', async () => {
    const first = (await rescan()).catalogue
    const second = await rescan(first, '2026-09-04T10:00:00.000Z')

    expect(second.changes).toEqual([])
    expect(second.catalogue.projects.map((entry) => entry.path)).toEqual(
      first.projects.map((entry) => entry.path),
    )
  })

  it('marks a deleted project missing and keeps it', async () => {
    const first = (await rescan()).catalogue
    rmSync(path.join(root, 'org', 'beta'), { recursive: true, force: true })

    const second = await rescan(first, '2026-09-04T10:00:00.000Z')

    expect(second.changes).toHaveLength(1)
    expect(second.changes[0]?.kind).toBe('missing')
    // Still on the list, and no longer worth reading.
    expect(second.catalogue.projects).toHaveLength(2)
    expect(present(second.catalogue)).toHaveLength(1)

    // And it says when it was last actually there.
    const gone = second.catalogue.projects.find((entry) => entry.presence === 'missing')
    expect(gone?.confirmed).toBe('2026-09-01T10:00:00.000Z')
  })

  it('brings it back when the folder returns', async () => {
    // Its own project, and the whole cycle in one test: a sibling's leftovers are not a
    // fixture, and a test that reads one passes for a reason nobody chose.
    project('org/gamma')
    const withGamma = (await rescan(EMPTY_CATALOGUE, '2026-09-01T10:00:00.000Z')).catalogue
    expect(withGamma.projects.some((entry) => entry.path.endsWith('gamma'))).toBe(true)

    rmSync(path.join(root, 'org', 'gamma'), { recursive: true, force: true })
    const gone = (await rescan(withGamma, '2026-09-04T10:00:00.000Z')).catalogue

    project('org/gamma')
    const back = await rescan(gone, '2026-09-05T10:00:00.000Z')

    expect(back.changes).toContainEqual({
      kind: 'returned',
      path: path.join(root, 'org', 'gamma'),
    })
    expect(back.catalogue.projects.find((entry) => entry.path.endsWith('gamma'))?.confirmed).toBe(
      '2026-09-05T10:00:00.000Z',
    )
  })

  it('survives being written down and read back', async () => {
    const { catalogue } = await rescan()

    // The record is JSON on disk once RG47 gives it a file. Until then this is what says
    // the shape is one that round-trips.
    expect(catalogueFrom(JSON.stringify(catalogue))).toEqual(catalogue)
  })
})
