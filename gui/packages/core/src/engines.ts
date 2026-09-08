import { aBoolean, aString, orMissing, record, type Reader } from './reading'

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
 * silently.
 *
 * The shape is written with RG3's toolkit like every other payload's. It was not, once:
 * this file predates the toolkit and hand-rolled a reader that answered `null` for
 * everything — a wrong program, a renamed key, a version that arrived as a number. The
 * first call every project makes was the one call that threw its diagnosis away.
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

export const readEngineProvenance: Reader<EngineProvenance> = record<EngineProvenance>(
  {
    /**
     * Strict, and the only field here that is. This is the first call made against a
     * candidate that may not be roadkeep at all, and `writing.version` is what a real
     * payload always carries and a wrong program never does — so it is the field that
     * decides whether anything answered, and the rest may go missing on an older build.
     */
    version: aString,
    home: orMissing(aString, ''),
    revision: orMissing(aString, ''),
    onDisk: orMissing(aString, ''),
  },
  { onDisk: 'on_disk' },
)

export const readEnginesPayload: Reader<EnginesPayload> = record<EnginesPayload>({
  writing: readEngineProvenance,
  invoke: orMissing(aString, ''),
  declaration: orMissing(aString, ''),
  verdict: orMissing(aString, ''),
  agree: orMissing(aBoolean, false),
  readable: orMissing(aBoolean, false),
  split: orMissing(aBoolean, false),
  swapped: orMissing(aBoolean, false),
})

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
