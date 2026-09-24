import { readFile, realpath, stat } from 'node:fs/promises'
import path from 'node:path'

import { probing } from './probing'

/**
 * Which git directory a checkout shares, read off git's own files.
 *
 * Nothing here runs git — the non-goal "No git command run by this app" is about spawning
 * a binary this app does not own, and it holds for a good reason beyond taste: a scan over
 * seventeen checkouts would be seventeen more processes, on top of the engine calls the
 * whole of block A exists to make cheap. Everything needed is three files on disk and they
 * are git's documented layout.
 *
 * A **main** worktree has a `.git` directory, and that directory is the common one.
 *
 * A **linked** worktree has a `.git` *file* holding `gitdir: <path>`, pointing at
 * `<main>/.git/worktrees/<name>`. Inside that sits `commondir`, a relative path — `../..`
 * in every case observed — which resolves back to the main `.git`. Two worktrees of one
 * repository therefore answer with the same string, which is exactly the grouping wanted.
 */

/** Everything about a folder that decides which family it belongs to. */
export interface GitSite {
  readonly realPath: string
  readonly commonDir: string | null
  /** The branch this checkout is on, a short sha where detached, empty where neither. */
  readonly branch: string
}

/**
 * The folder with every junction and symlink resolved, or the path itself if it cannot be.
 *
 * Asynchronous and bounded since RG102, like everything else here: this is three reads per
 * project and it ran in the process the window's IPC goes through. The promises API resolves
 * the platform's own way, so there is no `.native` to ask for as there is on the sync one.
 */
export async function realPathOf(candidate: string): Promise<string> {
  return probing(async () => {
    try {
      return await realpath(path.resolve(candidate))
    } catch {
      return path.resolve(candidate)
    }
  })
}

export async function gitCommonDir(project: string): Promise<string | null> {
  const dotGit = path.join(path.resolve(project), '.git')

  let entry
  try {
    entry = await probing(async () => stat(dotGit))
  } catch {
    return null
  }

  if (entry.isDirectory()) {
    return realPathOf(dotGit)
  }
  if (!entry.isFile()) {
    return null
  }

  let pointer: string
  try {
    pointer = await probing(async () => readFile(dotGit, 'utf8'))
  } catch {
    return null
  }

  const named = /^gitdir:\s*(.+?)\s*$/m.exec(pointer)
  if (named?.[1] === undefined || named[1] === '') return null

  // The pointer may be relative to the worktree, which is how git writes it for a
  // checkout moved alongside its repository.
  const gitDir = path.resolve(path.dirname(dotGit), named[1])

  try {
    const common = (
      await probing(async () => readFile(path.join(gitDir, 'commondir'), 'utf8'))
    ).trim()
    if (common !== '') return realPathOf(path.resolve(gitDir, common))
  } catch {
    // No `commondir` means this is not a worktree's git directory after all. The pointer
    // still names something git owns, so it is the honest answer.
  }

  return realPathOf(gitDir)
}

/**
 * Where this checkout's own git directory is: `.git`, or what the `.git` file points at.
 *
 * The same two shapes `gitCommonDir` reads, stopping one step earlier — a linked worktree's
 * `HEAD` is its own and not the repository's, which is the whole of what this answers.
 */
async function gitDirOf(project: string): Promise<string | null> {
  const dotGit = path.join(path.resolve(project), '.git')

  let entry
  try {
    entry = await probing(async () => stat(dotGit))
  } catch {
    return null
  }
  if (entry.isDirectory()) return dotGit
  if (!entry.isFile()) return null

  let pointer: string
  try {
    pointer = await probing(async () => readFile(dotGit, 'utf8'))
  } catch {
    return null
  }
  const named = /^gitdir:\s*(.+?)\s*$/m.exec(pointer)
  if (named?.[1] === undefined || named[1] === '') return null
  return path.resolve(path.dirname(dotGit), named[1])
}

/**
 * Which branch a checkout is on, or the short sha where its `HEAD` is detached (RG199).
 *
 * `HEAD` is one line in git's own files — `ref: refs/heads/2026.3`, or a bare sha — read
 * the way the common directory already is. No spawn, no library, no second reading of a
 * format this app does not own.
 *
 * **A detached HEAD is not an error.** It is a bisect, a tag checkout, a shallow clone, so
 * the short sha is the answer rather than nothing. Empty means no branch to show at all: a
 * folder that is not a checkout, or a `HEAD` that would not read — and a row draws nothing
 * either way, which is not the same rendering as a sha.
 */
export async function gitBranch(project: string): Promise<string> {
  const gitDir = await gitDirOf(project)
  if (gitDir === null) return ''

  let head: string
  try {
    head = await probing(async () => readFile(path.join(gitDir, 'HEAD'), 'utf8'))
  } catch {
    return ''
  }

  const named = /^ref:\s*refs\/heads\/(.+?)\s*$/m.exec(head)
  if (named?.[1] !== undefined && named[1] !== '') return named[1]

  // Detached: git writes the sha alone. Shortened here for a row, which is a rendering
  // choice and not a reading of the format — the whole sha is what the file holds.
  const sha = head.trim()
  return /^[0-9a-f]{40}$/i.test(sha) ? sha.slice(0, 7) : ''
}

export async function gitSite(project: string): Promise<GitSite> {
  // Together rather than in turn: they read different files and the bound above decides how
  // many of those reach the disk at once.
  const [realPath, commonDir, branch] = await Promise.all([
    realPathOf(project),
    gitCommonDir(project),
    gitBranch(project),
  ])
  return { realPath, commonDir, branch }
}
