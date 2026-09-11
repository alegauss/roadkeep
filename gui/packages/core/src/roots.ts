/**
 * Where this app is allowed to look, which is nowhere until somebody says.
 *
 * Which folders hold governed checkouts is a fact about one machine, and no file in any
 * repository could hold it. So a root is a folder a person named, with a depth, and there
 * is no default: an app that scans a drive on first launch is an app that reads somebody's
 * whole disk to draw a list. The first run asks.
 *
 * A root that has stopped existing is **kept and marked**, never dropped. A disconnected
 * drive, an unmounted share and a folder somebody renamed for an afternoon all look the
 * same from here, and forgetting the root means the person has to type it again for a
 * reason that was never theirs.
 *
 * Path comparison needs to know a platform — whether case matters, which separator — and
 * this package has neither a filesystem nor a platform in scope. So the list operations
 * take a `keyOf` and the caller who has one supplies it.
 */

import { asRecord } from './reading'

export interface ScanRoot {
  /** The folder, as the person named it. */
  readonly path: string
  /** How far below it to look. Zero is the folder itself and nothing under it. */
  readonly depth: number
}

/** Whether the folder was there the last time anybody looked. */
export type RootPresence = 'present' | 'missing' | 'unchecked'

export interface KnownRoot extends ScanRoot {
  readonly presence: RootPresence
}

/**
 * Two levels: deep enough for the usual `~/code/<org>/<repo>`, shallow enough that naming
 * a home directory by mistake is a second of wasted work rather than a minute.
 */
export const DEFAULT_DEPTH = 2

/** Six is already a hundred thousand folders under a busy tree. Past that it is a mistake. */
export const DEPTH_CEILING = 6

/**
 * There is no default root, and this constant exists so that reads as a decision rather
 * than as something nobody got round to.
 */
export const NO_DEFAULT_ROOTS: readonly ScanRoot[] = []

export type RootProblem = 'empty' | 'depth-not-whole' | 'depth-out-of-range'

export type RootCheck =
  | { readonly ok: true; readonly value: ScanRoot }
  | { readonly ok: false; readonly problem: RootProblem; readonly message: string }

export function checkRoot(path: string, depth: number = DEFAULT_DEPTH): RootCheck {
  const trimmed = path.trim()
  if (trimmed === '') {
    return { ok: false, problem: 'empty', message: 'a root has to be a folder, and this is blank' }
  }
  if (!Number.isInteger(depth)) {
    return {
      ok: false,
      problem: 'depth-not-whole',
      message: 'a depth counts folders, so it is a whole number',
    }
  }
  if (depth < 0 || depth > DEPTH_CEILING) {
    return {
      ok: false,
      problem: 'depth-out-of-range',
      message: `a depth is between 0 and ${String(DEPTH_CEILING)}; past that a scan reads more of the disk than it reports on`,
    }
  }
  return { ok: true, value: { path: trimmed, depth } }
}

/** How two roots are told apart. Supplied by whoever knows the platform's path rules. */
export type KeyOf = (path: string) => string

/**
 * Add a root, or change the depth of one already named.
 *
 * Naming the same folder twice is somebody adjusting its depth, not asking for it to be
 * walked twice — so it replaces in place and keeps its position in the list, which is the
 * order the person put them in.
 */
export function addRoot(roots: readonly ScanRoot[], candidate: ScanRoot, keyOf: KeyOf): ScanRoot[] {
  const key = keyOf(candidate.path)
  const at = roots.findIndex((root) => keyOf(root.path) === key)
  if (at === -1) return [...roots, candidate]

  const next = [...roots]
  next[at] = candidate
  return next
}

export function removeRoot(roots: readonly ScanRoot[], path: string, keyOf: KeyOf): ScanRoot[] {
  const key = keyOf(path)
  return roots.filter((root) => keyOf(root.path) !== key)
}

/**
 * The roots a window asked to keep, narrowed to the ones it could have named (RG146).
 *
 * A window names a root by picking it in the shell's dialog, and keeps or drops the roots the
 * settings already hold. Anything else in the list is a path the renderer typed, and it is
 * dropped here rather than written, because the folder is chosen by the shell. Each survivor
 * goes through `checkRoot` and `addRoot`, so a blank path or a depth out of range is dropped,
 * and two spellings of one folder become one, in the order the window sent them.
 *
 * @param chosen the keys of the folders the dialog answered with, in this process's life.
 */
export function acceptRoots(
  asked: unknown,
  held: readonly ScanRoot[],
  chosen: ReadonlySet<string>,
  keyOf: KeyOf,
): ScanRoot[] {
  if (!Array.isArray(asked)) return [...held]
  const known = new Set(held.map((root) => keyOf(root.path)))

  let kept: ScanRoot[] = []
  for (const entry of asked as unknown[]) {
    const fields = asRecord(entry) ?? {}
    const path = fields['path']
    const depth = fields['depth']
    if (typeof path !== 'string' || typeof depth !== 'number') continue
    const key = keyOf(path)
    if (!known.has(key) && !chosen.has(key)) continue
    const check = checkRoot(path, depth)
    if (check.ok) kept = addRoot(kept, check.value, keyOf)
  }
  return kept
}

/**
 * Mark each root with whether it is there, keeping every one of them.
 *
 * The keeping is the point. Dropping a root that is missing turns a disconnected drive
 * into a setting the person has to re-enter, and it does it silently.
 */
export async function withPresence(
  roots: readonly ScanRoot[],
  present: (path: string) => Promise<boolean>,
): Promise<KnownRoot[]> {
  // In parallel and not in turn: the caller bounds how many reach the disk at once (RG102),
  // and asking one root at a time would make a list of ten as slow as its slowest ten.
  const there = await Promise.all(roots.map(async (root) => present(root.path)))
  return roots.map((root, at) => ({
    ...root,
    presence: there[at] === true ? 'present' : 'missing',
  }))
}

/** The roots worth walking right now. The missing ones are still roots; they are just not here. */
export function walkable(roots: readonly KnownRoot[]): KnownRoot[] {
  return roots.filter((root) => root.presence === 'present')
}

/**
 * Whether a root is already covered by one earlier in the list.
 *
 * Reported, never refused: nesting a root inside another is sometimes exactly what
 * somebody means — a shallow sweep of `~/code` and a deeper one of the monorepo inside it
 * — and this app is not in a position to know which. What it can do is say so.
 */
export function coveredBy(
  roots: readonly ScanRoot[],
  candidate: ScanRoot,
  contains: (outer: ScanRoot, inner: string) => boolean,
): ScanRoot | null {
  return (
    roots.find((root) => root.path !== candidate.path && contains(root, candidate.path)) ?? null
  )
}
