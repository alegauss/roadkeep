import {
  aBoolean,
  anything,
  aString,
  listOf,
  orMissing,
  record,
  type Parsed,
  type Reader,
} from './reading'
import { EVERY_INPUT, VERBS, type VerbName } from './verbs'

/**
 * What this build of roadkeep can actually do, asked once when a project is opened.
 *
 * `commands --json` is the only read that names the version *and* every argument each verb
 * takes on this project, which makes it the only one that can tell an old build from a
 * broken one. Without it the first sign that a project is behind is a refusal on a flag,
 * arriving after somebody filled in a form.
 *
 * What it produces is a capability record kept beside the engine record, so a screen can
 * withhold a door rather than offer one that will be refused. A project too old to answer
 * at all is drawn as unsupported *with its version* — a state, and not a failure.
 */

export interface CommandArgument {
  /** Every way this flag can be written; `--marker` and `--status` are one argument. */
  readonly spelling: readonly string[]
  readonly primary: string
  readonly positional: boolean
  /** The metavariable, or empty for a flag that takes no value. */
  readonly takes: string
  readonly repeatable: boolean
  readonly required: boolean
  readonly help: string
}

export const readCommandArgument: Reader<CommandArgument> = record<CommandArgument>({
  spelling: orMissing(listOf(aString), []),
  primary: orMissing(aString, ''),
  positional: orMissing(aBoolean, false),
  takes: orMissing(aString, ''),
  repeatable: orMissing(aBoolean, false),
  required: orMissing(aBoolean, false),
  help: orMissing(aString, ''),
})

export interface PublishedCommand {
  readonly command: string
  readonly family: string
  readonly help: string
  readonly writes: boolean
  /** Whether the verb can be run at all. This is the field that matters to this app. */
  readonly runs: boolean
  /**
   * Whether the verb is exposed as an MCP tool, which is a **different question** and one
   * this app does not ask. Twenty-three verbs run and are not published — `init`, `block`,
   * `section`, `criterion`, `stats` and `commands` among them — so a client that read this
   * as "can I call it" would withhold a third of the doors it has. Found by RG4's contract
   * test, which failed on `stats` the first time this file read the wrong field.
   */
  readonly published: boolean
  /** What has to be present for it to work, in the engine's words. Empty for most. */
  readonly needs: string
  readonly arguments: readonly CommandArgument[]
}

export const readPublishedCommand: Reader<PublishedCommand> = record<PublishedCommand>({
  command: aString,
  family: orMissing(aString, ''),
  help: orMissing(aString, ''),
  writes: orMissing(aBoolean, false),
  runs: orMissing(aBoolean, true),
  published: orMissing(aBoolean, true),
  needs: orMissing(aString, ''),
  arguments: orMissing(listOf(readCommandArgument), []),
})

export interface CommandsPayload {
  readonly version: string
  /** Where the answer came from, which is the engine describing itself. */
  readonly source: unknown
  readonly commands: readonly PublishedCommand[]
}

export const readCommandsPayload: Reader<CommandsPayload> = record<CommandsPayload>({
  version: aString,
  source: orMissing(anything, null),
  commands: listOf(readPublishedCommand),
})

/** What this build offers for one verb this app calls. */
export interface Capability {
  readonly verb: VerbName
  /** This build can run it. What a screen needs before offering a door. */
  readonly callable: boolean
  /** It is also on the MCP tool surface — recorded, and not what gates a door here. */
  readonly onToolSurface: boolean
  readonly writes: boolean
  /** Flags this app would send that this build does not accept. Empty is the good case. */
  readonly missingFlags: readonly string[]
}

export type CapabilityReport =
  | {
      readonly kind: 'known'
      readonly version: string
      readonly byVerb: Readonly<Record<VerbName, Capability>>
      /** Every verb this app calls is published and takes every flag it would send. */
      readonly complete: boolean
    }
  | {
      readonly kind: 'unsupported'
      /** From `engines`, since the build could not name itself here. */
      readonly version: string
      readonly reason: string
    }

/**
 * Every flag this app can actually emit for a verb, taken from the builder rather than
 * from a list beside it.
 *
 * A second list would drift: somebody adds a flag to a builder, the list stays as it was,
 * and the capability check goes on approving a flag nobody checks. Running the real
 * builder over an input with every field filled in cannot drift, because it *is* the
 * builder. `--json` is added because the client appends it to every call.
 */
export function flagsFor(verb: VerbName): string[] {
  const build = VERBS[verb] as (input: unknown) => readonly string[]
  const emitted = build(EVERY_INPUT[verb]).filter((part) => part.startsWith('--'))
  return [...new Set([...emitted, '--json'])]
}

/**
 * Build the capability record.
 *
 * @param engineVersion what `engines` reported, used when `commands` itself cannot be
 *   read — a build too old to publish this read still has a version worth showing.
 */
export function readCapabilities(
  stdout: string,
  engineVersion: string,
): CapabilityReport {
  let source: unknown
  try {
    source = JSON.parse(stdout)
  } catch {
    return {
      kind: 'unsupported',
      version: engineVersion,
      reason: '`commands --json` answered with something that is not a payload',
    }
  }

  const parsed: Parsed<CommandsPayload> = readCommandsPayload(source, '')
  if (!parsed.ok) {
    return {
      kind: 'unsupported',
      version: engineVersion,
      reason: `\`commands --json\` is missing ${parsed.failure.path || 'the shape this app reads'}`,
    }
  }

  const published = new Map(parsed.value.commands.map((command) => [command.command, command]))
  const byVerb = {} as Record<VerbName, Capability>
  let complete = true

  for (const verb of Object.keys(VERBS) as VerbName[]) {
    const command = published.get(verb)
    if (command === undefined || !command.runs) {
      byVerb[verb] = {
        verb,
        callable: false,
        onToolSurface: command?.published ?? false,
        writes: false,
        missingFlags: [],
      }
      complete = false
      continue
    }

    const accepted = new Set(command.arguments.flatMap((argument) => argument.spelling))
    const missingFlags = flagsFor(verb).filter((flag) => !accepted.has(flag))
    if (missingFlags.length > 0) complete = false

    byVerb[verb] = {
      verb,
      callable: true,
      onToolSurface: command.published,
      writes: command.writes,
      missingFlags,
    }
  }

  return { kind: 'known', version: parsed.value.version, byVerb, complete }
}

/** The verbs a screen should withhold, with why. Empty means every door can be offered. */
export function withheld(report: CapabilityReport): string[] {
  if (report.kind === 'unsupported') {
    return [`every verb: ${report.reason} (roadkeep ${report.version || 'of an unknown version'})`]
  }
  return Object.values<Capability>(report.byVerb)
    .filter((capability) => !capability.callable || capability.missingFlags.length > 0)
    .map((capability) =>
      capability.callable
        ? `${capability.verb}: this build does not take ${capability.missingFlags.join(', ')}`
        : `${capability.verb}: this build cannot run it`,
    )
}
