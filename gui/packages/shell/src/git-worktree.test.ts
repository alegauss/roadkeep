import { existsSync } from 'node:fs'
import path from 'node:path'

import { groupProjects, isFamily } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { gitCommonDir, gitSite, realPathOf } from './git-worktree'
import { rootKey } from './root-paths'

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/**
 * The arrangement this task exists for, on the machine it was written on: Turing kept as a
 * worktree per version under a `latest` junction. It is read rather than fabricated,
 * because a fixture built by this test would be this app's idea of a worktree and the whole
 * question is whether git's real layout is read correctly. Where it is absent the tests
 * that need it say so instead of passing quietly.
 */
const TURING = 'D:/Git/viglet/turing'
const versions = ['2026.3', '2026.2'].map((name) => path.join(TURING, name))
const junction = path.join(TURING, 'latest')
const worktreesPresent = versions.every((p) => existsSync(p)) && existsSync(junction)

describe('RG12: reading the git directory a checkout shares', () => {
  it('answers null for a folder that is not a checkout at all', () => {
    expect(gitCommonDir(path.join(REPO, 'packages'))).toBeNull()
  })

  it('answers this repository own git directory', () => {
    // A main worktree: `.git` is a directory and is itself the common one.
    const common = gitCommonDir(REPO)

    expect(common).not.toBeNull()
    expect(path.basename(common ?? '')).toBe('.git')
  })

  it('answers null rather than throwing for a path that does not exist', () => {
    expect(gitCommonDir(path.join(REPO, 'no-such-folder'))).toBeNull()
  })
})

describe('RG12: resolving a link', () => {
  it('resolves a path to the folder it really is', () => {
    expect(realPathOf(path.join(REPO, 'packages', '..'))).toBe(realPathOf(REPO))
  })

  it('gives back the path itself when it cannot be resolved', () => {
    const missing = path.join(REPO, 'no-such-folder')
    expect(realPathOf(missing)).toBe(path.resolve(missing))
  })
})

describe.skipIf(!worktreesPresent)('RG12: a real worktree family on this machine', () => {
  it('gives both versions the same common directory', () => {
    const [main, old] = versions.map(gitCommonDir)

    expect(main).not.toBeNull()
    expect(old).toBe(main)
  })

  it('resolves the junction onto the version it points at', () => {
    expect(realPathOf(junction)).toBe(realPathOf(versions[0] ?? ''))
  })

  it('draws three paths as one family of two versions', () => {
    const sites = [...versions, junction].map((project) => ({
      path: project,
      ...gitSite(project),
    }))

    const families = groupProjects(sites, rootKey)

    expect(families).toHaveLength(1)
    expect(isFamily(families[0]!)).toBe(true)
    expect(families[0]?.members).toHaveLength(2)

    const newest = families[0]?.members.find((member) => member.path === versions[0])
    expect(newest?.aliases).toEqual([junction])
  })
})

describe.skipIf(worktreesPresent)('RG12: the worktree family this machine does not have', () => {
  it('is named rather than skipped silently', () => {
    // A skip nobody reads is a test that stopped covering something. This says which
    // arrangement went unchecked and where it would be.
    expect(worktreesPresent).toBe(false)
  })
})
