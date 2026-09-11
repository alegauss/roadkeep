import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { EMPTY_CATALOGUE, type ProjectCatalogue } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { cataloguePath, CATALOGUE_FILE, loadCatalogue, saveCatalogue } from './catalogue-file'
import { removeTree } from './scratch'

/**
 * RG164: the record, written beside the settings.
 *
 * What is held here is the round trip and every way of not having one: a launch with no file,
 * a file somebody broke, and a record written by a build that read it differently. None of
 * them is an error — the walk behind the record is what rebuilds it — so what this asserts is
 * that each answers the empty record rather than throwing.
 */
const scratches: string[] = []

function userData(): string {
  const at = mkdtempSync(path.join(tmpdir(), 'rk-catalogue-'))
  scratches.push(at)
  return at
}

const RECORD: ProjectCatalogue = {
  version: 1,
  roots: [{ path: 'D:\\code', depth: 2 }],
  projects: [
    {
      path: 'D:\\code\\alpha',
      aliases: [],
      commonDir: null,
      root: 'D:\\code',
      confirmed: '2026-09-11T10:00:00.000Z',
      presence: 'present',
    },
    {
      path: 'D:\\code\\beta',
      aliases: [],
      commonDir: null,
      root: 'D:\\code',
      confirmed: '2026-09-10T10:00:00.000Z',
      presence: 'missing',
    },
  ],
}

afterAll(() => {
  for (const at of scratches) removeTree(at)
})

describe('RG164: what this machine last found', () => {
  it('writes a record and reads the same one back', () => {
    const at = userData()

    expect(saveCatalogue(at, RECORD)).toBe(true)

    // Every project, the missing one included: forgetting it is what this file is for.
    expect(loadCatalogue(at)).toEqual(RECORD)
  })

  it('makes the directory when there is not one yet, which a first launch has', () => {
    const at = path.join(userData(), 'not-there-yet')

    expect(saveCatalogue(at, RECORD)).toBe(true)
    expect(loadCatalogue(at).projects).toHaveLength(2)
  })

  it('reads nothing as the empty record, since a first launch has no file', () => {
    expect(loadCatalogue(userData())).toEqual(EMPTY_CATALOGUE)
  })

  it('reads a broken file as the empty record rather than as a failure', () => {
    // A list the walk behind it rebuilds, so neither of these is worth a sentence anywhere.
    const broken = userData()
    writeFileSync(cataloguePath(broken), '{ not json at all', 'utf8')
    expect(loadCatalogue(broken)).toEqual(EMPTY_CATALOGUE)

    const older = userData()
    writeFileSync(cataloguePath(older), JSON.stringify({ ...RECORD, version: 99 }), 'utf8')
    expect(loadCatalogue(older)).toEqual(EMPTY_CATALOGUE)

    const wrong = userData()
    writeFileSync(cataloguePath(wrong), JSON.stringify({ version: 1, projects: 'no' }), 'utf8')
    expect(loadCatalogue(wrong)).toEqual(EMPTY_CATALOGUE)
  })

  it('leaves no temporary file behind, and writes where it says it does', () => {
    const at = userData()
    saveCatalogue(at, RECORD)

    expect(cataloguePath(at)).toBe(path.join(at, CATALOGUE_FILE))
    expect(readFileSync(cataloguePath(at), 'utf8').endsWith('\n')).toBe(true)
    expect(() => readFileSync(`${cataloguePath(at)}.writing`, 'utf8')).toThrow('ENOENT')
  })

  it('says so when it could not write, rather than throwing at a caller quitting', () => {
    // A path that cannot be a directory, because a file of that name is in the way.
    const at = userData()
    const blocked = path.join(at, 'in-the-way')
    writeFileSync(blocked, 'a file, not a directory', 'utf8')

    expect(saveCatalogue(blocked, RECORD)).toBe(false)
  })
})
