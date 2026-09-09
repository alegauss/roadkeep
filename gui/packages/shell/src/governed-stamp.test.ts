import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { stampGoverned } from './governed-stamp'

import { removeTree } from './scratch'

const made: string[] = []

function project(files: Record<string, string>): string {
  const root = mkdtempSync(path.join(tmpdir(), 'rk-stamp-'))
  made.push(root)
  for (const [name, contents] of Object.entries(files)) {
    writeFileSync(path.join(root, name), contents, 'utf8')
  }
  return root
}

afterAll(() => {
  for (const root of made) removeTree(root)
})

describe('RG7: stamping a project', () => {
  it('is the same twice when nothing moved', async () => {
    const root = project({ 'roadkeep.toml': 'prefix = "FX"', 'ROADMAP.md': '# a' })

    expect(await stampGoverned(root, ['ROADMAP.md'])).toBe(
      await stampGoverned(root, ['ROADMAP.md']),
    )
  })

  it('changes when a governed file changes', async () => {
    const root = project({ 'roadkeep.toml': 'prefix = "FX"', 'ROADMAP.md': '# a' })
    const before = await stampGoverned(root, ['ROADMAP.md'])

    writeFileSync(path.join(root, 'ROADMAP.md'), '# a much longer roadmap', 'utf8')

    expect(await stampGoverned(root, ['ROADMAP.md'])).not.toBe(before)
  })

  it('changes when the config changes, because that changes which files are governed', async () => {
    const root = project({ 'roadkeep.toml': 'prefix = "FX"', 'ROADMAP.md': '# a' })
    const before = await stampGoverned(root, ['ROADMAP.md'])

    writeFileSync(path.join(root, 'roadkeep.toml'), 'prefix = "FX"\ndeferred = true', 'utf8')

    expect(await stampGoverned(root, ['ROADMAP.md'])).not.toBe(before)
  })

  it('does not change when an ungoverned file changes', async () => {
    const root = project({ 'roadkeep.toml': 'prefix = "FX"', 'ROADMAP.md': '# a' })
    const before = await stampGoverned(root, ['ROADMAP.md'])

    writeFileSync(path.join(root, 'NOTES.md'), 'not governed', 'utf8')

    expect(await stampGoverned(root, ['ROADMAP.md'])).toBe(before)
  })

  it('treats a file that is not there as a state, not an error', async () => {
    const root = project({ 'roadkeep.toml': 'prefix = "FX"' })

    const before = await stampGoverned(root, ['DEFERRED.md'])
    expect(before).toContain('absent')

    // And it stops being absent the moment somebody writes it.
    writeFileSync(path.join(root, 'DEFERRED.md'), '# set aside', 'utf8')
    expect(await stampGoverned(root, ['DEFERRED.md'])).not.toBe(before)
  })

  it('does not depend on the order the files were named in', async () => {
    const root = project({
      'roadkeep.toml': 'prefix = "FX"',
      'ROADMAP.md': '# a',
      'CHANGELOG.md': '# b',
    })

    expect(await stampGoverned(root, ['ROADMAP.md', 'CHANGELOG.md'])).toBe(
      await stampGoverned(root, ['CHANGELOG.md', 'ROADMAP.md']),
    )
  })
})
