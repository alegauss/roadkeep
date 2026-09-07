import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { DEFAULT_POLICY } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { lookWith, scanRoots } from './scan-fs'

/**
 * A real tree on a real disk, with the decoys that make the walk worth bounding: a marker
 * inside `node_modules`, one inside `.git`, one nested inside a project already found, and
 * one past the depth the root declared.
 */
let root = ''

function make(relative: string, contents?: string): void {
  const full = path.join(root, relative)
  if (contents === undefined) {
    mkdirSync(full, { recursive: true })
    return
  }
  mkdirSync(path.dirname(full), { recursive: true })
  writeFileSync(full, contents, 'utf8')
}

beforeAll(() => {
  root = mkdtempSync(path.join(tmpdir(), 'rk-scan-'))

  make('org/alpha/roadkeep.toml', 'prefix = "AL"')
  make('org/beta/roadkeep.toml', 'prefix = "BE"')
  make('org/alpha/node_modules/dep/roadkeep.toml', 'prefix = "NO"')
  make('org/alpha/packages/inner/roadkeep.toml', 'prefix = "NO"')
  make('.hidden/gamma/roadkeep.toml', 'prefix = "NO"')
  make('org/alpha/.git/modules/x/roadkeep.toml', 'prefix = "NO"')
  make('very/deep/down/here/delta/roadkeep.toml', 'prefix = "NO"')
  make('org/empty')
  // A directory named like the marker is not a project: the marker is a file.
  make('org/decoy/roadkeep.toml')
})

afterAll(() => {
  rmSync(root, { recursive: true, force: true })
})

describe('RG11: a real walk over a real tree', () => {
  it('finds the projects and none of the decoys', () => {
    const result = scanRoots([{ path: root, depth: 3 }])
    const found = result.found.map((entry) => path.relative(root, entry.path).replaceAll('\\', '/'))

    expect(found.sort()).toEqual(['org/alpha', 'org/beta'])
  })

  it('does not enter a project it already found', () => {
    const found = scanRoots([{ path: root, depth: 5 }]).found.map((entry) =>
      path.relative(root, entry.path).replaceAll('\\', '/'),
    )

    expect(found).not.toContain('org/alpha/packages/inner')
  })

  it('does not go past the depth the root declared', () => {
    // `very/deep/down/here/delta` is five below the root. Four does not reach it and five
    // does, which is the bound doing its job in both directions.
    const at = (depth: number) =>
      scanRoots([{ path: root, depth }]).found.map((entry) =>
        path.relative(root, entry.path).replaceAll('\\', '/'),
      )

    expect(at(4)).not.toContain('very/deep/down/here/delta')
    expect(at(5)).toContain('very/deep/down/here/delta')
  })

  it('reads a handful of directories rather than the whole tree', () => {
    // The number is the point. Without the bounds this tree has three decoys behind
    // directories the walk should never open.
    const result = scanRoots([{ path: root, depth: 3 }])

    expect(result.looked).toBeLessThan(15)
    expect(result.unreadable).toEqual([])
  })
})

describe('RG11: what one look at a directory answers', () => {
  it('says a directory holding the marker is a project', () => {
    const listing = lookWith()(path.join(root, 'org', 'alpha'))

    expect(listing?.isProject).toBe(true)
  })

  it('does not mistake a directory named like the marker for one', () => {
    const listing = lookWith()(path.join(root, 'org', 'decoy'))

    expect(listing?.isProject).toBe(false)
  })

  it('lists the child directories and not the files', () => {
    const listing = lookWith()(path.join(root, 'org'))

    expect(listing?.children.map((child) => child.name).sort()).toEqual([
      'alpha',
      'beta',
      'decoy',
      'empty',
    ])
  })

  it('answers null for a directory that cannot be read', () => {
    expect(lookWith()(path.join(root, 'not-here-at-all'))).toBeNull()
  })

  it('looks for the marker the policy names', () => {
    const listing = lookWith({ ...DEFAULT_POLICY, marker: 'nothing.toml' })(
      path.join(root, 'org', 'alpha'),
    )

    expect(listing?.isProject).toBe(false)
  })
})
