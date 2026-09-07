/**
 * What `engines --json` says, and how a command line becomes argv.
 *
 * `roadkeep` on PATH is the one thing `engines` exists to say a project may not be
 * running: a checkout may be governed by the plugin, a sibling checkout, a pip install or
 * a committed launcher, and those may sit at different versions and disagree. So this app
 * asks each project which copy writes for it, and asks before it reads anything else.
 *
 * Only the keys this app actually uses are named below. The rest of the payload is left
 * alone rather than modelled, because a shape restated here is one that goes stale
 * silently — and because a general answer to reading payloads is RG3's, not this file's.
 */

/** The copy that answered, as `engines --json` describes it. */
export interface EngineProvenance {
  /** The version that is running, which is not always the version on disk. */
  readonly version: string
  /** Where that copy lives. */
  readonly home: string
  /** The revision it was built from, or an empty string where there is none. */
  readonly revision: string
  /** What the directory holds now — different from `version` when a home was swapped. */
  readonly onDisk: string
}

export interface EnginesPayload {
  readonly writing: EngineProvenance
  /** The command line that reaches the copy wired to this project. One line, for a shell. */
  readonly invoke: string
  /** What the project's own configuration declares, which may name a different copy. */
  readonly declaration: string
  /** `engines`' own word for how the copies stand. Carried through, never interpreted. */
  readonly verdict: string
  /** Whether every copy it found agrees. */
  readonly agree: boolean
  /** Whether the governed files could be read at all. */
  readonly readable: boolean
  /** Copies split across homes, and a home replaced under the running process. */
  readonly split: boolean
  readonly swapped: boolean
}

function text(source: Record<string, unknown>, key: string): string {
  const value = source[key]
  return typeof value === 'string' ? value : ''
}

function flag(source: Record<string, unknown>, key: string): boolean {
  return source[key] === true
}

/**
 * Read the payload, or answer `null` for anything that is not one.
 *
 * Defensive rather than trusting: this is the first call made against a candidate that
 * may not be roadkeep at all, so "did not answer with an engines payload" has to be a
 * value and not an exception. `writing.version` is what a real payload always carries and
 * a wrong program never does, which makes it the field worth testing for.
 */
export function readEnginesPayload(stdout: string): EnginesPayload | null {
  let parsed: unknown
  try {
    parsed = JSON.parse(stdout)
  } catch {
    return null
  }
  if (typeof parsed !== 'object' || parsed === null) return null

  const root = parsed as Record<string, unknown>
  const writing = root['writing']
  if (typeof writing !== 'object' || writing === null) return null

  const provenance = writing as Record<string, unknown>
  const version = text(provenance, 'version')
  if (version === '') return null

  return {
    writing: {
      version,
      home: text(provenance, 'home'),
      revision: text(provenance, 'revision'),
      onDisk: text(provenance, 'on_disk'),
    },
    invoke: text(root, 'invoke'),
    declaration: text(root, 'declaration'),
    verdict: text(root, 'verdict'),
    agree: flag(root, 'agree'),
    readable: flag(root, 'readable'),
    split: flag(root, 'split'),
    swapped: flag(root, 'swapped'),
  }
}

/**
 * Turn a one-line command into argv.
 *
 * `invoke` is documented as a shell command, and every call this app makes is argv with
 * no shell, so somewhere the two have to meet. This is that place, and it is deliberately
 * the smallest thing that can be: whitespace separates, single and double quotes group,
 * and **a backslash is never an escape**. That last rule is the one worth stating — on
 * Windows a backslash is a path separator, and a splitter that consumed them would turn
 * `C:\Users\a` into `C:Usersa` and then report an engine that could not be started.
 *
 * An unterminated quote answers `null` rather than a best guess. A caller that cannot
 * split the line has to say so: silently reaching a different copy of roadkeep is the
 * failure this whole file exists to prevent.
 */
export function splitCommandLine(line: string): string[] | null {
  const argv: string[] = []
  let current = ''
  let holding = false
  let quote: '"' | "'" | null = null

  for (const character of line) {
    if (quote !== null) {
      if (character === quote) quote = null
      else current += character
      continue
    }
    if (character === '"' || character === "'") {
      quote = character
      holding = true
      continue
    }
    if (/\s/.test(character)) {
      if (holding) {
        argv.push(current)
        current = ''
        holding = false
      }
      continue
    }
    current += character
    holding = true
  }

  if (quote !== null) return null
  if (holding) argv.push(current)
  return argv
}
