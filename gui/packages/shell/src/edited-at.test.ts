import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { EDITED_CEILING, editedAt } from './edited-at'
import type { StatAt } from './governed-at'
import { CASE_INSENSITIVE, withinRoot } from './root-paths'

/**
 * RG244: the files a session edited, asked of the disk.
 *
 * The disk is a function here, as in `governed-at.test.ts`, so what is held is the reading:
 * which paths are asked about, which are named and left alone, and what each answers.
 */

const ROOT = path.resolve('/proj')
const AT = new Date('2026-09-15T10:05:00.000Z')

function disk(): { stat: StatAt; asked: string[] } {
  const asked: string[] = []
  return {
    asked,
    stat: (file) => {
      asked.push(file)
      return file.endsWith('there.ts') ? { mtime: AT } : null
    },
  }
}

describe('RG244: an edited file, as the disk has it', () => {
  it('answers a path under the root with its time, shortened to the root with forward slashes', () => {
    const { stat } = disk()
    const absolute = path.join(ROOT, 'src', 'there.ts')

    expect(editedAt(ROOT, [absolute, 'src/there.ts'], stat)).toEqual([
      {
        path: absolute,
        shown: 'src/there.ts',
        inside: true,
        present: true,
        changed: AT.toISOString(),
      },
      {
        path: 'src/there.ts',
        shown: 'src/there.ts',
        inside: true,
        present: true,
        changed: AT.toISOString(),
      },
    ])
  })

  it('says a file that is not there is not there, and keeps its row', () => {
    const { stat } = disk()

    expect(editedAt(ROOT, ['src/gone.ts'], stat)).toEqual([
      { path: 'src/gone.ts', shown: 'src/gone.ts', inside: true, present: false, changed: '' },
    ])
  })

  it('names a path outside the root as spelled, and asks the disk nothing about it', () => {
    const { stat, asked } = disk()
    const memory = path.resolve('/home/a/.claude/memory/there.ts')

    const files = editedAt(ROOT, [memory, '../sibling/there.ts'], stat)

    expect(asked).toEqual([])
    expect(files).toEqual([
      { path: memory, shown: memory, inside: false, present: false, changed: '' },
      {
        path: '../sibling/there.ts',
        shown: '../sibling/there.ts',
        inside: false,
        present: false,
        changed: '',
      },
    ])
  })

  it('does not take a folder beside the root whose name starts the same for one under it', () => {
    expect(withinRoot(ROOT, path.resolve('/proj-other/there.ts'))).toBeNull()
    expect(withinRoot(ROOT, path.join(ROOT, 'there.ts'))).toBe(path.join(ROOT, 'there.ts'))
  })

  it.runIf(CASE_INSENSITIVE)('takes a path spelled in another case as under the root', () => {
    // An agent on Windows spells the drive as `d:` where the catalogue holds `D:`.
    const spelled = path.join(ROOT.toLowerCase(), 'src', 'there.ts')

    expect(editedAt(ROOT.toUpperCase(), [spelled], disk().stat)[0]).toMatchObject({
      inside: true,
      shown: 'src/there.ts',
    })
  })

  it('answers no more paths than its ceiling, whatever a page sends', () => {
    const { stat, asked } = disk()
    const many = Array.from({ length: EDITED_CEILING + 5 }, (_, at) => `src/${String(at)}.ts`)

    expect(editedAt(ROOT, many, stat)).toHaveLength(EDITED_CEILING)
    expect(asked).toHaveLength(EDITED_CEILING)
  })
})
