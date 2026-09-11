import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG184: the byte no other gate looks for.
 *
 * Five NUL bytes sat inside a template literal in `packages/ui/src/useFiling.ts` — the
 * separators of a key built from a draft's fields — and every gate passed: `tsc -b` compiled
 * it, `oxlint` read it, `prettier --check` called it formatted, and the suite went green. It
 * was found by `file` calling the source `data` instead of JavaScript, which is not a gate
 * and nobody runs.
 *
 * **What the byte does is worse than being invisible.** It was a separator that worked, so
 * nothing misbehaved — but the file cannot be grepped for the line it is in, an edit against
 * that text does not match, and a diff shows the change as a rewrite of a line that looks
 * identical. A tool writing a file through a shell heredoc is how it arrived, and that is a
 * path this project uses often.
 *
 * **Prose is bound by the same rule.** The governed files are prose a person reads, and an
 * invisible byte in one of them survives every roadkeep read too, since none of them is
 * looking for a character that is not there.
 *
 * It reads bytes and parses nothing, which is why it is a fast test: it starts no process and
 * depends on no build.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** Everything this repository owns and a person reads or edits. */
const OWNED = ['packages/core/src', 'packages/shell/src', 'packages/ui/src', 'docs', '.github']

/**
 * And the files at the root that are text this project wrote.
 *
 * Named rather than walked, because the root also holds what npm and the editors put there
 * — a lock file nobody wrote by hand, a node_modules tree — and a walk would have to spell
 * what to skip instead of what to read.
 */
const AT_ROOT = [
  'CLAUDE.md',
  'LICENSE',
  'package.json',
  'roadkeep.toml',
  'electron-builder.yml',
  'tsconfig.json',
  'tsconfig.base.json',
]

/**
 * What a text file may carry besides printable characters.
 *
 * Tab, carriage return and newline, and nothing else. Carriage return is here because this
 * repository checks out CRLF on Windows (RG112) and a rule that refused it would report every
 * file on the machine this is written on.
 */
const ALLOWED = new Set([0x09, 0x0a, 0x0d])

const TEXT = /[.](ts|tsx|md|json|toml|yml|yaml|css|html)$/

function everyFile(at: string): string[] {
  return readdirSync(path.join(REPO, at), { withFileTypes: true }).flatMap((entry) => {
    // Spelled with forward slashes whatever the platform, so a path in this file reads the
    // same as it does in a commit.
    const here = `${at}/${entry.name}`
    if (entry.isDirectory()) return everyFile(here)
    return TEXT.test(entry.name) ? [here] : []
  })
}

/** Where a file carries a byte it may not, named by path and offset so it can be found. */
function carries(file: string): string[] {
  const bytes = readFileSync(path.join(REPO, file))
  const found: string[] = []
  for (const [at, byte] of bytes.entries()) {
    // Below space, or DEL: the range that is invisible in every editor and every diff.
    if ((byte < 0x20 && !ALLOWED.has(byte)) || byte === 0x7f) {
      found.push(`${file}: byte 0x${byte.toString(16).padStart(2, '0')} at ${String(at)}`)
    }
  }
  return found
}

describe('RG184: no source or prose file carries an invisible byte', () => {
  const owned = [...OWNED.flatMap(everyFile), ...AT_ROOT]

  it('reads the files it claims to, which is what a clean answer rests on', () => {
    // The guard on the guard: a walk pointed at nothing reports a clean tree in the same
    // words as a clean tree, which is the failure RG62 taught this repository.
    expect(owned.length).toBeGreaterThan(100)
    expect(owned).toContain('packages/ui/src/useFiling.ts')
    expect(owned).toContain('docs/ROADMAP.md')
  })

  it('finds none, and names the path and the offset of any it does', () => {
    expect(owned.flatMap(carries)).toEqual([])
  })

  it('finds one that is there, since a gate nobody has seen fail is a gate nobody trusts', () => {
    // The byte is written as an escape, which is six printable characters in this file: a
    // test that put a real NUL in the tree would be a test this very gate reports. And it is
    // read from a buffer rather than a planted file, so nothing can be left behind.
    const bytes = Buffer.from(
      `const key = \`a${String.fromCharCode(0)}b\`
`,
      'utf8',
    )
    const found: number[] = []
    for (const [at, byte] of bytes.entries()) {
      if ((byte < 0x20 && !ALLOWED.has(byte)) || byte === 0x7f) found.push(at)
    }

    expect(found).toEqual([14])
  })
})
