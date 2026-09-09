import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { addRoot, withPresence, type ScanRoot } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { rootContains, rootExists, rootKey } from './root-paths'

const made: string[] = []

afterAll(() => {
  for (const root of made) rmSync(root, { recursive: true, force: true })
})

function folder(): string {
  const made_ = mkdtempSync(path.join(tmpdir(), 'rk-root-'))
  made.push(made_)
  return made_
}

const at = (p: string, depth = 2): ScanRoot => ({ path: p, depth })

describe('RG10: telling two paths apart on this platform', () => {
  it('resolves a relative path against where the app is running', () => {
    expect(path.isAbsolute(rootKey('.'))).toBe(true)
  })

  it('sees one folder spelled two ways as one', () => {
    const one = folder()
    expect(rootKey(one)).toBe(rootKey(path.join(one, 'sub', '..')))
  })

  it('agrees with the list operations that use it', () => {
    const one = folder()
    const roots = addRoot([at(one)], at(path.join(one, '.')), rootKey)

    // The whole reason `keyOf` is a parameter: `core` cannot know this answer.
    expect(roots).toHaveLength(1)
  })
})

describe('RG10: whether a root is there', () => {
  it('says yes for a folder', async () => {
    expect(await rootExists(folder())).toBe(true)
  })

  it('says no for a path that does not exist', async () => {
    expect(await rootExists(path.join(tmpdir(), 'rk-root-that-is-not-here'))).toBe(false)
  })

  it('says no for a file, which is not somewhere to look', async () => {
    const one = folder()
    const file = path.join(one, 'notes.md')
    writeFileSync(file, 'not a folder', 'utf8')

    expect(await rootExists(file)).toBe(false)
  })

  it('marks a missing root without dropping it', async () => {
    const marked = await withPresence(
      [at(folder()), at(path.join(tmpdir(), 'rk-root-gone'))],
      rootExists,
    )

    expect(marked.map((root) => root.presence)).toEqual(['present', 'missing'])
  })
})

describe('RG10: one root inside another', () => {
  it('is contained when it sits within the declared depth', () => {
    expect(rootContains(at('/code', 2), '/code/org/repo')).toBe(true)
  })

  it('is not contained when the depth does not reach it', () => {
    expect(rootContains(at('/code', 1), '/code/org/repo')).toBe(false)
  })

  it('is not contained when it is beside rather than below', () => {
    expect(rootContains(at('/code', 3), '/code-other/repo')).toBe(false)
  })

  it('is not contained when it is above', () => {
    expect(rootContains(at('/code/org', 3), '/code')).toBe(false)
  })

  it('counts a folder as containing itself', () => {
    expect(rootContains(at('/code', 0), '/code')).toBe(true)
  })
})
