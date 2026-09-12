import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { groupProjects, isFamily } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { gitBranch, gitCommonDir, gitSite, realPathOf } from './git-worktree'
import { removeTree } from './scratch'
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
  it('answers null for a folder that is not a checkout at all', async () => {
    expect(await gitCommonDir(path.join(REPO, 'packages'))).toBeNull()
  })

  it('answers this repository own git directory', async () => {
    // A main worktree: `.git` is a directory and is itself the common one.
    const common = await gitCommonDir(REPO)

    expect(common).not.toBeNull()
    expect(path.basename(common ?? '')).toBe('.git')
  })

  it('answers null rather than throwing for a path that does not exist', async () => {
    expect(await gitCommonDir(path.join(REPO, 'no-such-folder'))).toBeNull()
  })
})

describe('RG12: resolving a link', () => {
  it('resolves a path to the folder it really is', async () => {
    expect(await realPathOf(path.join(REPO, 'packages', '..'))).toBe(await realPathOf(REPO))
  })

  it('gives back the path itself when it cannot be resolved', async () => {
    const missing = path.join(REPO, 'no-such-folder')
    expect(await realPathOf(missing)).toBe(path.resolve(missing))
  })
})

describe.skipIf(!worktreesPresent)('RG12: a real worktree family on this machine', () => {
  it('gives both versions the same common directory', async () => {
    const [main, old] = await Promise.all(versions.map(async (one) => gitCommonDir(one)))

    expect(main).not.toBeNull()
    expect(old).toBe(main)
  })

  it('resolves the junction onto the version it points at', async () => {
    expect(await realPathOf(junction)).toBe(await realPathOf(versions[0] ?? ''))
  })

  it('draws three paths as one family of two versions', async () => {
    const sites = await Promise.all(
      [...versions, junction].map(async (project) => ({
        path: project,
        ...(await gitSite(project)),
      })),
    )

    const families = groupProjects(sites, rootKey)

    expect(families).toHaveLength(1)
    expect(isFamily(families[0]!)).toBe(true)
    expect(families[0]?.members).toHaveLength(2)

    const newest = families[0]?.members.find((member) => member.path === versions[0])
    expect(newest?.aliases).toEqual([junction])
  })
})

describe.skipIf(worktreesPresent)('RG12: the worktree family this machine does not have', () => {
  it('is named rather than skipped silently', async () => {
    // A skip nobody reads is a test that stopped covering something. This says which
    // arrangement went unchecked and where it would be.
    expect(worktreesPresent).toBe(false)
  })
})

describe('RG199: which branch a checkout is on', () => {
  it('reads this repository’s own HEAD, which is a real checkout and not a fixture', async () => {
    const branch = await gitBranch(REPO)

    // Whatever branch this is read on, it is a name and not a sha: a repository somebody is
    // working in is on a branch, and the sha case has its own test below.
    expect(branch).not.toBe('')
    expect(branch).not.toMatch(/^[0-9a-f]{7}$/)
  })

  it.skipIf(!worktreesPresent)('tells two worktrees of one repository apart', async () => {
    // The whole reason this exists: a declared name is one word for a whole repository, so
    // every worktree of Turing renders as `Turing` and the branch is what says which.
    const [first, second] = await Promise.all(versions.map(gitBranch))

    expect(first).not.toBe('')
    expect(second).not.toBe('')
    expect(first).not.toBe(second)
  })

  it('answers empty for a folder that is not a checkout at all', async () => {
    // Not the same state as a checkout whose HEAD would not read, and the row draws nothing
    // for it rather than drawing a sha.
    expect(await gitBranch(path.join(REPO, 'docs'))).toBe('')
  })

  it('answers the short sha where HEAD is detached', async () => {
    // The one case no real checkout here is in — a bisect, a tag checkout, a shallow clone.
    // Fabricated deliberately and only for the *parse*: what this file refuses to invent is
    // git's worktree layout, and this is one documented line in one file.
    const at = mkdtempSync(path.join(tmpdir(), 'rk-detached-'))
    try {
      const sha = '0123456789abcdef0123456789abcdef01234567'
      mkdirSync(path.join(at, '.git'))
      writeFileSync(path.join(at, '.git', 'HEAD'), `${sha}\n`, 'utf8')

      expect(await gitBranch(at)).toBe('0123456')
    } finally {
      removeTree(at)
    }
  })

  it('carries the branch onto the site the scan groups by', async () => {
    const site = await gitSite(REPO)

    expect(site.branch).toBe(await gitBranch(REPO))
  })
})
