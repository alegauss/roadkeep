import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { commitOf, STAMP_FILE, versionOf, writeStamp } from './stamp'

import { removeTree } from './scratch'

/**
 * The build step, run for real. It writes a file and reads a checkout, so it is exercised
 * against real directories rather than a mock of one.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const scratch: string[] = []

function elsewhere(): string {
  const home = mkdtempSync(path.join(tmpdir(), 'rk-stamp-'))
  scratch.push(home)
  return home
}

afterAll(() => {
  for (const home of scratch) removeTree(home)
})

describe('RG46: the commit is stamped at build time', () => {
  it('reads the commit of the checkout it is built in', () => {
    // A build script running in a checkout, which is not the app running a git command.
    expect(commitOf(REPO)).toMatch(/^[0-9a-f]{7,}$/)
  })

  it('says nothing for a directory that is not a checkout, rather than guessing', () => {
    // A tarball, a CI export, a source copy somebody downloaded. None is an error.
    expect(commitOf(elsewhere())).toBe('')
  })

  it('reads the version the root package declares', () => {
    expect(versionOf(REPO)).toMatch(/^\d+\.\d+\.\d+/)
  })

  it('says nothing where there is no manifest to read', () => {
    expect(versionOf(elsewhere())).toBe('')
  })

  it('writes a stamp the app can read with no process at all', () => {
    const home = elsewhere()
    writeFileSync(path.join(home, 'package.json'), JSON.stringify({ version: '9.9.9' }))

    const written = writeStamp(home, 'stamp.json')
    const onDisk: unknown = JSON.parse(readFileSync(path.join(home, 'stamp.json'), 'utf8'))

    expect(written.version).toBe('9.9.9')
    expect(written.commit).toBe('')
    expect(written.signed).toBe('unsigned')
    expect(onDisk).toEqual(written)
  })

  it('puts the real stamp where the app looks for it', () => {
    // The path the packaged app reads, so a rename here fails rather than shipping a build
    // that cannot name itself.
    expect(STAMP_FILE).toBe(path.join('packages', 'shell', 'dist', 'stamp.json'))
  })
})

describe('RG46: a build that lost its posture is not packaged', () => {
  it('runs, stamps and says what the build is', () => {
    // The real step, in this checkout. It exits zero only because the posture holds.
    const said = execFileSync(
      process.execPath,
      [path.join(REPO, 'packages', 'shell', 'dist', 'stamp-build.js')],
      { cwd: REPO, encoding: 'utf8' },
    )

    expect(said).toContain('roadkeep-gui')
    expect(said).toContain('unsigned')
    expect(said.trim().split('\n')).toHaveLength(1)
  })

  it('leaves the stamp where a packaged app finds it', () => {
    const onDisk: unknown = JSON.parse(readFileSync(path.join(REPO, STAMP_FILE), 'utf8'))

    expect(onDisk).toHaveProperty('version')
    expect(onDisk).toHaveProperty('commit')
    expect(onDisk).toHaveProperty('signed')
  })
})
