import { createLimiter } from './limiting'
import type { KeyOf, ScanRoot } from './roots'

/**
 * Finding governed checkouts without reading the disk.
 *
 * A walk with no depth bound and no ignore list is the difference between a scan measured
 * in milliseconds and one measured in minutes: seventeen projects live under a few hundred
 * folders, and the `node_modules` beside them hold a hundred thousand.
 *
 * Four rules do all the work. It looks for **one filename** and nothing else. It refuses
 * to enter a directory the policy names, and any hidden one. It stops at the depth the
 * root declared. And **a directory holding the marker is a project and is not descended
 * into** — a governed repository does not contain another, so finding one ends that
 * branch rather than starting a search inside it.
 *
 * Those rules are configuration and not constants. A machine laid out differently needs a
 * different list, and the ignore set is the one part of a scan somebody can be wrong about
 * cheaply — a folder wrongly skipped is a project that does not appear, which is visible,
 * where a folder wrongly entered is a minute nobody can account for.
 *
 * How a directory is *looked at* belongs to whoever has a filesystem. This decides whether
 * to enter it and when to stop.
 *
 * **Nothing here waits on a disk.** A `Look` answers a promise, because the machine this
 * runs on is not the one it was written on: a network share, a sleeping external drive or
 * a directory behind a virus scanner turns one read into hundreds of milliseconds, and a
 * synchronous walk spends every one of them holding the process that answers the window.
 * The directories of one level are looked at together and bounded, so a slow root costs
 * the scan its own time and nothing else's.
 */

export interface ScanPolicy {
  /** The file whose presence makes a directory a project. */
  readonly marker: string
  /** Directory names never entered, whatever else is true of them. */
  readonly ignore: readonly string[]
  /** Skip every directory whose name begins with a dot. */
  readonly skipHidden: boolean
}

export const DEFAULT_POLICY: ScanPolicy = {
  marker: 'roadkeep.toml',
  // `.git` and `.venv` are already covered by `skipHidden`, and are named anyway: somebody
  // who turns hidden directories back on still has no business walking either.
  ignore: [
    '.git',
    '.venv',
    'node_modules',
    'dist',
    'build',
    'target',
    'out',
    'coverage',
    'venv',
    '__pycache__',
    'vendor',
  ],
  skipHidden: true,
}

/** What one directory turned out to hold. `null` from a `Look` means it could not be read. */
export interface Listing {
  /** True when the marker file is here, which makes this a project. */
  readonly isProject: boolean
  /** The child directories, named and addressed the way the caller will address them. */
  readonly children: readonly { readonly name: string; readonly path: string }[]
}

export type Look = (path: string) => Promise<Listing | null>

export interface Found {
  readonly path: string
  /** The root it was found under, so a screen can say where it came from. */
  readonly root: string
  /** How far below that root, which is what the depth bound counted. */
  readonly depth: number
}

export interface ScanResult {
  readonly found: readonly Found[]
  /** Directories that could not be read. A permission error is a fact, not a crash. */
  readonly unreadable: readonly string[]
  /** How many directories were looked at. The number the depth bound exists to hold down. */
  readonly looked: number
}

export function mayEnter(name: string, policy: ScanPolicy): boolean {
  if (policy.skipHidden && name.startsWith('.')) return false
  return !policy.ignore.includes(name)
}

/**
 * How many directories may be read at once.
 *
 * Higher than the four a portfolio read allows itself, because these are not the same
 * resource: that number bounds Python interpreters and this one bounds open handles, and a
 * disk that is answering slowly is a disk with idle time to give. Low enough that a share
 * which has gone away is not met with sixty simultaneous requests to prove it.
 */
export const SCAN_WIDTH = 8

export interface ScanOptions {
  readonly policy?: ScanPolicy
  /** Directories read at once. Defaults to `SCAN_WIDTH`. */
  readonly width?: number
}

/**
 * Walk every root, breadth first.
 *
 * Breadth first because the shallow answer is the likely one: a person naming `~/code`
 * with a depth of three mostly means the repositories directly under it, and finding
 * those first is what lets a list start drawing before the walk has finished.
 *
 * **One level at a time and the level together.** The directories of a level are read
 * concurrently under a bound, which is where a slow disk stops being a stall — but the
 * answers are consumed in the order the level lists them, so what is found and the order
 * it is found in do not depend on which read came back first. A scan of the same machine
 * twice is the same list twice.
 */
export async function scan(
  roots: readonly ScanRoot[],
  look: Look,
  keyOf: KeyOf,
  options: ScanOptions = {},
): Promise<ScanResult> {
  const { policy = DEFAULT_POLICY, width = SCAN_WIDTH } = options
  const limiter = createLimiter(width)

  const found: Found[] = []
  const unreadable: string[] = []
  const seen = new Set<string>()
  let looked = 0

  for (const root of roots) {
    let level: string[] = [root.path]

    for (let depth = 0; depth <= root.depth && level.length > 0; depth += 1) {
      // Claimed before any of them is read, and in order: two roots overlapping must not
      // both look at the same directory, and which of them wins cannot be a race.
      const claimed = level.filter((directory) => {
        const key = keyOf(directory)
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })

      looked += claimed.length
      const listings = await Promise.all(
        claimed.map((directory) => limiter.hold(() => look(directory))),
      )

      const next: string[] = []
      for (const [index, listing] of listings.entries()) {
        const directory = claimed[index] ?? ''
        if (listing === null) {
          unreadable.push(directory)
          continue
        }

        if (listing.isProject) {
          // The branch ends here. A governed repository does not contain another, and
          // descending into one is how a monorepo's every package becomes a candidate.
          found.push({ path: directory, root: root.path, depth })
          continue
        }

        if (depth === root.depth) continue
        for (const child of listing.children) {
          if (mayEnter(child.name, policy)) next.push(child.path)
        }
      }

      level = next
    }
  }

  return { found, unreadable, looked }
}
