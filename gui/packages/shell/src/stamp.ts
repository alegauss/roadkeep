import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { identityFrom, STAMP_VARS, type BuildIdentity } from '@rk/core'

/**
 * The packaging step that stamps a build with what it is.
 *
 * Run before the app is packaged and never by the app. `No git command run by this app`
 * binds the *app*: this is a build script, it runs in a checkout, and what it learns is
 * written into a file the app then reads with no process at all.
 *
 * **A build outside a checkout is stamped `unstamped`**, not guessed and not failed. The
 * ordinary reasons are a tarball, a CI export and a source copy somebody downloaded, and
 * none of them is an error — the build is simply one whose commit nobody can name.
 */

/** Where the stamp is written, relative to the repository root. */
export const STAMP_FILE = path.join('packages', 'shell', 'dist', 'stamp.json')

export interface Stamp {
  readonly version: string
  readonly commit: string
  readonly signed: string
}

/** The commit this tree is on, or the empty string where nothing can say. */
export function commitOf(root: string): string {
  try {
    return execFileSync('git', ['rev-parse', '--short', 'HEAD'], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
  } catch {
    // No git, no checkout, or a repository with no commits. All the same answer here.
    return ''
  }
}

/** The version the root package declares. */
export function versionOf(root: string): string {
  try {
    const manifest: unknown = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'))
    const version = (manifest as { version?: unknown }).version
    return typeof version === 'string' ? version : ''
  } catch {
    return ''
  }
}

/**
 * Write the stamp.
 *
 * `signed` is taken from the environment rather than decided here, because whether an
 * executable ended up signed is known by whatever did the signing — and today nothing
 * does, so it is `unsigned`.
 */
export function writeStamp(root: string, into: string = STAMP_FILE): Stamp {
  const stamp: Stamp = {
    version: versionOf(root),
    commit: commitOf(root),
    signed: process.env[STAMP_VARS.signed] ?? 'unsigned',
  }
  writeFileSync(path.resolve(root, into), `${JSON.stringify(stamp, null, 2)}\n`, 'utf8')
  return stamp
}

/**
 * What this build is, at run time.
 *
 * Reads the file the build step wrote, beside the compiled main process. No process is
 * spawned and no repository is looked for: a packaged app has neither, and the answer was
 * settled before it was packaged.
 *
 * A build with no stamp answers `unstamped` in every field rather than failing. That is
 * `npm start` from a working tree, and it is a real way to run this.
 */
export function readStamp(beside: string = import.meta.dirname, packaged = false): BuildIdentity {
  try {
    const raw: unknown = JSON.parse(readFileSync(path.join(beside, 'stamp.json'), 'utf8'))
    const stamp = raw as Partial<Stamp>
    return identityFrom({
      version: stamp.version,
      commit: stamp.commit,
      signed: stamp.signed,
      packaged,
    })
  } catch {
    return identityFrom({ packaged })
  }
}
