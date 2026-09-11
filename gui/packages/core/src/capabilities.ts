import {
  aBoolean,
  aString,
  anything,
  keysOf,
  listOf,
  orMissing,
  record,
  tableOf,
  type Parsed,
  type Reader,
} from './reading'
import { argumentsFor } from './tools'
import {
  EVERY_INPUT,
  publishedAs,
  VERBS,
  VERB_WORDS,
  type Spelling,
  type VerbInputs,
  type VerbName,
} from './verbs'
import { EVERY_WRITE_INPUT, WRITES, WRITE_WORDS, type WriteInputs, type WriteName } from './writes'

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
  /**
   * The verb explained at length, in the engine's own words.
   *
   * Read rather than written, because a screen offering `amend` beside `restate` has to
   * say which is which, and the difference between them is the expensive thing to get
   * wrong. A sentence composed here would be this app's account of another tool's verb.
   */
  readonly description: string
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
  description: orMissing(aString, ''),
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

/**
 * Every verb this app can call, read or write.
 *
 * The two tables are separate because a read is offered freely and a write is not, and
 * this is the one place that wants both: a build too old to `add` has to say so before
 * somebody types a symptom, which means the write verbs are checked exactly as the reads
 * are.
 */
export type CalledName = VerbName | WriteName

/**
 * What each of those takes. The two sets of names are disjoint, so this is each verb's own
 * input and never a blend of a read's and a write's.
 */
type CalledInputs = VerbInputs & WriteInputs

/**
 * The two builder tables as one, declared by the type it is (RG129).
 *
 * It was `Record<string, (input: never) => …>`, which made the key type a claim this file
 * asserted rather than one the declaration carried — `CalledName` written beside the table
 * and agreeing with it because somebody kept them agreeing. Mapped over `CalledName` the way
 * `VERBS` and `WRITES` are each mapped over their own names, a verb added to either without
 * a name here fails to compile, `keysOf` answers the names, and indexing with a generic verb
 * pairs a builder with its own input — which is what lets `flagsFor` call one unasserted.
 */
type Builders = { [K in CalledName]: (input: CalledInputs[K]) => readonly string[] }

const CALLED: Builders = { ...VERBS, ...WRITES }
const CALLED_INPUT: { [K in CalledName]: CalledInputs[K] } = {
  ...EVERY_INPUT,
  ...EVERY_WRITE_INPUT,
}
/**
 * Both spelling tables as one. Exported for the carrier's guard (RG143), which has to know a
 * verb by its words whichever table holds it.
 */
export const CALLED_WORDS: Spelling = { ...VERB_WORDS, ...WRITE_WORDS }

/**
 * The name this build publishes for a verb this app calls.
 *
 * The lookup RG69 is about. A two-word verb whose key was used as its published name is
 * looked up under a name `commands` never printed, reported as one this build cannot run,
 * and its door withheld — the exact failure this read exists to prevent, arriving through
 * the read itself.
 */
export function publishedName(verb: CalledName): string {
  return publishedAs(verb, CALLED_WORDS)
}

/**
 * Every verb name this app can put on a command line, reads and writes together.
 *
 * Published because the check and the things checked have to come from one list. A test
 * or a screen enumerating the reads alone would go on reporting a build complete while
 * the write it is about to offer is one this engine has never heard of.
 */
export const CALLED_NAMES: readonly CalledName[] = keysOf(CALLED)

/** What this build offers for one verb this app calls. */
export interface Capability {
  readonly verb: CalledName
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
      readonly byVerb: Readonly<Record<CalledName, Capability>>
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
export function flagsFor(verb: CalledName): string[] {
  const sent = emitted(CALLED[verb], CALLED_INPUT[verb]).filter((part) => part.startsWith('--'))
  return [...new Set([...sent, '--json'])]
}

/**
 * Every argument name a verb's tool call can carry, derived the way `flagsFor` is (RG143).
 *
 * The same input with every field set, through the same `argumentsFor` the client calls, so a
 * field added to an input is an argument here the moment it is one on the wire.
 */
export function argumentsOf(verb: CalledName): ReadonlySet<string> {
  return new Set(Object.keys(argumentsFor(CALLED_INPUT[verb])))
}

/**
 * One builder over one input, named by the same verb.
 *
 * Generic so the two are read as one verb's pair: inside, `Builders[K]` is a builder taking
 * exactly `CalledInputs[K]`, and the call needs no assertion. Written in the verb's own
 * lookup it would not be — each index answers the whole union on its own, and a builder
 * from that union takes an input fitting every verb at once, which is `never`.
 */
function emitted<K extends CalledName>(
  build: Builders[K],
  input: CalledInputs[K],
): readonly string[] {
  return build(input)
}

/**
 * Build the capability record from a payload already read.
 *
 * The client reads `commands` with the shape the verb declares (RG66), so what is left
 * here is the comparison this file is actually about — what this build publishes against
 * what this app would send. The version comes off the payload: a build that answered this
 * read named itself in it, and `engines`' version is only needed where it did not.
 */
export function capabilitiesOf(payload: CommandsPayload): CapabilityReport {
  const published = new Map(payload.commands.map((command) => [command.command, command]))
  const byVerb = tableOf(CALLED_NAMES, (verb) =>
    capabilityOf(verb, published.get(publishedName(verb))),
  )
  // Complete is every verb runnable with every flag it would send, which is a question about
  // the table once it is built rather than a flag somebody has to remember to lower in a loop.
  const complete = CALLED_NAMES.every(
    (verb) => byVerb[verb].callable && byVerb[verb].missingFlags.length === 0,
  )

  return { kind: 'known', version: payload.version, byVerb, complete }
}

/** One verb against the command this build published for it, or against its absence. */
function capabilityOf(verb: CalledName, command: PublishedCommand | undefined): Capability {
  if (command === undefined || !command.runs) {
    return {
      verb,
      callable: false,
      onToolSurface: command?.published ?? false,
      writes: false,
      missingFlags: [],
    }
  }

  const accepted = new Set(command.arguments.flatMap((argument) => argument.spelling))
  return {
    verb,
    callable: true,
    onToolSurface: command.published,
    writes: command.writes,
    missingFlags: flagsFor(verb).filter((flag) => !accepted.has(flag)),
  }
}

/**
 * The same record, from stdout that has not been read yet.
 *
 * The one caller that still needs this is the one asking whether this build can be talked
 * to at all: a roadkeep too old to publish `commands` answers with prose or with a shape
 * this app does not know, and *that* is the report — `unsupported`, with the reason. A
 * client would have raised it as a failure, which is right for a read and wrong for the
 * question "is there anything here to read".
 */
export function readCapabilities(stdout: string, engineVersion: string): CapabilityReport {
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

  return capabilitiesOf(parsed.value)
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
