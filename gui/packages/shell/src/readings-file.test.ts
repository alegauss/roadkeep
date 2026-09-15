import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { NOTHING_REMEMBERED, READINGS_VERSION, remembering, type ProjectReading } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { loadReadings, READINGS_FILE, readingsPath, saveReadings } from './readings-file'
import { removeTree } from './scratch'

/**
 * RG251: what a verb printed, kept beside the record.
 *
 * `catalogue-file.test`'s shape and its reason: the round trip, and every way of not having
 * one. A launch with no file, a file somebody broke and one written by a build that read it
 * differently all answer nothing remembered — the reads behind the screen are what fill it —
 * so none of them is an error anybody has to see.
 */
const scratches: string[] = []

function userData(): string {
  const at = mkdtempSync(path.join(tmpdir(), 'rk-readings-'))
  scratches.push(at)
  return at
}

afterAll(() => {
  for (const at of scratches) removeTree(at)
})

const READING: ProjectReading = {
  root: '/code/alpha',
  stamp: 'stamp-a',
  read: '2026-09-15T10:00:00.000Z',
  governed: ['docs/ROADMAP.md', 'roadkeep.toml'],
  stats: null,
  pick: null,
  engines: null,
  declares: null,
  gate: null,
}

describe('RG251: the readings file', () => {
  it('reads back what it wrote', () => {
    const at = userData()
    const written = remembering(NOTHING_REMEMBERED, READING)

    expect(saveReadings(at, written)).toBe(true)
    const back = loadReadings(at)

    expect(back.version).toBe(READINGS_VERSION)
    expect(back.projects.map((one) => one.root)).toEqual(['/code/alpha'])
    expect(back.projects[0]?.governed).toEqual(READING.governed)
  })

  it('answers nothing remembered where there is no file, which is a first launch', () => {
    expect(loadReadings(userData())).toEqual(NOTHING_REMEMBERED)
  })

  it('answers nothing remembered for a file it cannot read, rather than throwing', () => {
    const at = userData()
    writeFileSync(readingsPath(at), 'half a fi', 'utf8')

    expect(loadReadings(at)).toEqual(NOTHING_REMEMBERED)
  })

  it('answers nothing remembered for a version this build does not know', () => {
    const at = userData()
    writeFileSync(
      readingsPath(at),
      JSON.stringify({ version: READINGS_VERSION + 1, projects: [READING] }),
      'utf8',
    )

    expect(loadReadings(at)).toEqual(NOTHING_REMEMBERED)
  })

  it('writes a file beside the record, readable and named for what it holds', () => {
    const at = userData()
    saveReadings(at, remembering(NOTHING_REMEMBERED, READING))

    expect(readingsPath(at)).toBe(path.join(at, READINGS_FILE))
    // Indented, as the record and the settings are: a file in a profile directory is one
    // somebody eventually opens.
    expect(readFileSync(readingsPath(at), 'utf8')).toContain('\n  "projects"')
  })

  it('says a write it could not make did not land', () => {
    // A file where the directory would be: the write cannot happen, nothing throws, and the
    // next launch reads every project the way it always did.
    const at = userData()
    const blocked = path.join(at, 'in-the-way')
    writeFileSync(blocked, 'a file, not a directory', 'utf8')

    expect(saveReadings(path.join(blocked, 'under-it'), NOTHING_REMEMBERED)).toBe(false)
  })
})
