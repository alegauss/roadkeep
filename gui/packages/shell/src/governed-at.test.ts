import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { governedAt, type StatAt } from './governed-at'

/**
 * RG153: when each governed file last changed, beside the stream.
 *
 * The disk is a function here, so this holds the reading and not the filesystem: which paths
 * are asked about, which are refused, and what a file that is not there answers.
 */

const ROOT = path.resolve('/proj')
const GOVERNED = { roadmap: 'docs/ROADMAP.md', changelog: 'docs/CHANGELOG.md' }
const AT = new Date('2026-09-11T10:00:00.000Z')

const asked: string[] = []
const stat: StatAt = (file) => {
  asked.push(file)
  return file.endsWith('ROADMAP.md') ? { mtime: AT } : null
}

describe('RG153: the governed files, and when the disk last changed each', () => {
  it('answers the path the config spells and the time the disk holds', () => {
    const files = governedAt(ROOT, GOVERNED, stat)

    expect(files[0]).toEqual({
      role: 'roadmap',
      path: 'docs/ROADMAP.md',
      changed: AT.toISOString(),
      present: true,
    })
  })

  it('says a file that is not there is not there, rather than dropping the role', () => {
    // A project has a role before anything has written it, and a screen drawing four files
    // where the config declares five is the absence nobody notices.
    const files = governedAt(ROOT, GOVERNED, stat)

    expect(files).toHaveLength(2)
    expect(files[1]?.present).toBe(false)
    expect(files[1]?.changed).toBe('')
  })

  it('asks about a path under the root, resolved as this machine spells one', () => {
    asked.length = 0
    governedAt(ROOT, { roadmap: 'docs/ROADMAP.md' }, stat)

    expect(asked).toEqual([path.join(ROOT, 'docs', 'ROADMAP.md')])
  })

  it('refuses a path that leaves the root, rather than statting wherever it points', () => {
    // The roles are the project's own config, and one naming a path outside the project
    // would have this process read a file nobody in the window chose.
    asked.length = 0
    const files = governedAt(ROOT, { roadmap: '../elsewhere/ROADMAP.md' }, stat)

    expect(asked).toEqual([])
    expect(files[0]?.present).toBe(false)
    expect(files[0]?.path).toBe('../elsewhere/ROADMAP.md')
  })

  it('answers nothing for a project that governs nothing', () => {
    expect(governedAt(ROOT, {}, stat)).toEqual([])
  })
})
