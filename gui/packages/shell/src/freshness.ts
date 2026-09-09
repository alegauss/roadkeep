import { readdirSync, statSync } from 'node:fs'
import path from 'node:path'

/**
 * Whether the bundle a test is about is the code the tree holds (RG96).
 *
 * Most of this suite compiles from source through Vitest, so a run is a statement about the
 * working tree. A handful of tests are not: they start the built app, or read what the
 * renderer actually shipped, and their subject is whatever the last build left on disk. Run
 * after a source edit and no rebuild, those tests answer about code nobody is looking at —
 * and they answer *green*, which is the bad direction for a false one.
 *
 * **It notices rather than rebuilding.** A test that quietly rebuilt would make one test
 * cost what a build costs and would hide the fact that the developer's loop had drifted; a
 * suite that always built would slow every run for the sake of a few files. Comparing two
 * timestamps costs a walk and turns a false green into a sentence naming `npm run build`.
 *
 * **Modification times and not hashes.** The question is *did somebody edit source after the
 * last build*, which is what an mtime answers directly. A hash would answer a different and
 * harder question — whether the edit changed anything the bundle contains — and would need
 * the build's own graph to do it.
 */

/** What a build reads. Anything else changing does not make a bundle wrong. */
const BUILT_FROM = new Set(['.ts', '.tsx', '.css', '.html'])

/**
 * And what it does not, though it sits beside what it does.
 *
 * A test file is under `src` and is in no bundle, so editing one cannot make the build
 * wrong — and editing one is the most common thing anybody does before running the live
 * suite, which would make this fire on almost every run and be turned off within a week.
 *
 * The line is drawn here and not at *is this reachable from an entry point*, which needs
 * the build's own graph. So a test instrument that is not itself a test — a fixture, a fake
 * — still counts, and the cost of that is a rebuild nobody needed. Erring that way is
 * deliberate: the failure this exists to stop is the answer that comes back green.
 */
function isTest(file: string): boolean {
  return file.includes('.test.')
}

/** Directories a walk never enters, being output or somebody else's. */
const SKIPPED = new Set(['dist', 'dist-types', 'node_modules'])

interface Newest {
  readonly at: number
  readonly file: string
}

const NOTHING: Newest = { at: 0, file: '' }

function newestUnder(root: string, keep: (file: string) => boolean): Newest {
  let found = NOTHING

  const walk = (directory: string): void => {
    let entries
    try {
      entries = readdirSync(directory, { withFileTypes: true })
    } catch {
      // Not there, or not readable. A directory that cannot be walked contributes nothing,
      // which is the same answer as an empty one and is not this function's to report.
      return
    }

    for (const entry of entries) {
      const full = path.join(directory, entry.name)
      if (entry.isDirectory()) {
        if (!SKIPPED.has(entry.name)) walk(full)
        continue
      }
      if (!keep(entry.name)) continue

      const at = statSync(full).mtimeMs
      if (at > found.at) found = { at, file: full }
    }
  }

  walk(root)
  return found
}

/** The newest source file under these roots, by modification time. */
export function newestSource(roots: readonly string[]): Newest {
  const keep = (file: string) => BUILT_FROM.has(path.extname(file)) && !isTest(file)
  return roots
    .map((root) => newestUnder(root, keep))
    .reduce((newest, one) => (one.at > newest.at ? one : newest), NOTHING)
}

/** The newest file in a build's output, which is when that build finished. */
export function newestBuilt(directories: readonly string[]): Newest {
  return directories
    .map((directory) => newestUnder(directory, () => true))
    .reduce((newest, one) => (one.at > newest.at ? one : newest), NOTHING)
}

/**
 * What is wrong with the bundle, said as a sentence, or the empty string.
 *
 * A sentence rather than a boolean because the whole value here is what a reader is told:
 * *this failed because the bundle is older than a file you edited, and here is the command*
 * is a different message from a window that would not open.
 */
export function staleBundle(
  sourceRoots: readonly string[],
  buildDirectories: readonly string[],
): string {
  const built = newestBuilt(buildDirectories)
  if (built.at === 0) {
    return (
      'there is no build to test: run `npm run build` first. This asks what the app' +
      ' actually ships and cannot answer it from source.'
    )
  }

  const source = newestSource(sourceRoots)
  if (source.at <= built.at) return ''

  return (
    `the build is older than the source it is meant to be: ${path.basename(source.file)} was` +
    ' edited after the last `npm run build`, so this would be a green run about code nobody' +
    ' is looking at. Run `npm run build`.'
  )
}
