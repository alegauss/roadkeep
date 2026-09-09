import path from 'node:path'

import { staleBundle } from './freshness'

/**
 * Where this repository's source and its build output are, and the one call a test makes
 * before reading either (RG96).
 *
 * The lists are here rather than at each call site so that a package added to the build is
 * a package the freshness check knows about — two lists would agree until the third one
 * somebody forgets.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const PACKAGES = ['core', 'shell', 'ui'] as const

/** Everything a build reads. */
export const SOURCE_ROOTS: readonly string[] = [
  ...PACKAGES.map((name) => path.join(REPO, 'packages', name, 'src')),
  path.join(REPO, 'packages', 'ui', 'index.html'),
]

/** Everything a build writes that a test then reads. */
export const BUILD_DIRECTORIES: readonly string[] = [
  path.join(REPO, 'packages', 'shell', 'dist'),
  path.join(REPO, 'packages', 'ui', 'dist'),
]

/**
 * Refuse to answer about a bundle older than the tree, naming the command that fixes it.
 *
 * Called by the tests whose subject is on disk rather than in the source Vitest compiles:
 * the one that starts the built app, and the one that reads what the renderer shipped. A
 * throw and not a skip — a skipped test reads as *nothing to say here*, and what is true is
 * that this run cannot say anything yet.
 */
export function refuseIfStale(): void {
  const wrong = staleBundle(SOURCE_ROOTS, BUILD_DIRECTORIES)
  if (wrong !== '') throw new Error(`roadkeep-gui: ${wrong}`)
}
