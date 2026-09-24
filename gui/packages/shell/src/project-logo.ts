import { readFile, stat } from 'node:fs/promises'
import path from 'node:path'

import { probing } from './probing'

/**
 * The mark a project declares, read here and handed over as bytes (RG204).
 *
 * **The renderer never gets a path.** A `file://` URL from the portfolio into an Electron
 * renderer widens what the window can read to whatever a path can reach — and the path was
 * written by a repository on this machine rather than by this app. So the resolving, the
 * refusing and the reading all happen on the side that has the disk, and what crosses is a
 * data URL or nothing.
 *
 * **Every failure is the same failure.** Missing, unreadable, the wrong type, too large, or
 * outside the project — each answers empty, and the row falls back to `project.icon` and
 * that to the folder glyph. A broken logo is a cosmetic outcome rather than an empty cell,
 * which is also why the emoji stays worth declaring where a logo exists.
 */

/**
 * What this agrees to draw, and the bytes that prove each one.
 *
 * Sniffed rather than trusted to the extension: the declaration is a repository's word, and
 * a `.png` holding something else is a file this app would otherwise hand to a renderer as
 * an image. SVG is the exception with no magic number — it is text, so it is recognised by
 * its root element, and it is the one type here that can carry script.
 */
const MAGIC: readonly { readonly type: string; readonly bytes: readonly number[] }[] = [
  { type: 'image/png', bytes: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a] },
  { type: 'image/jpeg', bytes: [0xff, 0xd8, 0xff] },
  { type: 'image/gif', bytes: [0x47, 0x49, 0x46, 0x38] },
  { type: 'image/webp', bytes: [0x52, 0x49, 0x46, 0x46] },
]

/**
 * A logo is a list-row icon at thirty-two pixels.
 *
 * Enforced on the bytes and never on a declaration: a repository pointing at a four-megabyte
 * PNG gets the emoji instead of a portfolio that stalls on seventeen reads of it.
 */
export const LOGO_CEILING = 512 * 1024

/**
 * Whether a declared path stays inside the project.
 *
 * Resolved and then compared, because a string test is not a location (block G's criterion):
 * `docs/../../other/mark.svg` starts with nothing suspicious and lands in another repository
 * once the dot segments are resolved. An absolute path is refused for the same reason — it
 * is not a path inside the project at all.
 */
function inside(root: string, declared: string): string {
  if (declared === '' || path.isAbsolute(declared)) return ''
  const resolvedRoot = path.resolve(root)
  const full = path.resolve(resolvedRoot, declared)
  const within = path.relative(resolvedRoot, full)
  if (within === '' || within.startsWith('..') || path.isAbsolute(within)) return ''
  return full
}

/** Which image these bytes actually are, or the empty string. */
function typeOf(bytes: Buffer): string {
  for (const known of MAGIC) {
    if (known.bytes.every((byte, at) => bytes[at] === byte)) return known.type
  }
  // SVG is text and carries no magic number. Read as a string and recognised by its root
  // element, which is what a renderer would have to find to draw it either way.
  const head = bytes.subarray(0, 512).toString('utf8').trimStart()
  return head.startsWith('<svg') || head.startsWith('<?xml') ? 'image/svg+xml' : ''
}

/**
 * The declared logo as a data URL, or the empty string for every way of not having one.
 *
 * @param root the project, already the folder this app was given.
 * @param declared what `project.logo` says, repository-relative.
 */
export async function logoOf(root: string, declared: string): Promise<string> {
  const full = inside(root, declared)
  if (full === '') return ''

  let size: number
  try {
    const entry = await probing(async () => stat(full))
    if (!entry.isFile()) return ''
    size = entry.size
  } catch {
    return ''
  }
  // Asked of the entry before the bytes are read, so an oversized file costs a stat and not
  // a read.
  if (size > LOGO_CEILING || size === 0) return ''

  let bytes: Buffer
  try {
    bytes = await probing(async () => readFile(full))
  } catch {
    return ''
  }

  const type = typeOf(bytes)
  if (type === '') return ''
  return `data:${type};base64,${bytes.toString('base64')}`
}
