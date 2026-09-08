import { capabilitiesOf, type CapabilityReport } from './capabilities'
import { createClient, type Client } from './client'
import { createCachingTransport, type CachingTransport } from './cache'
import {
  resolveEngine,
  type ResolvedEngine,
  type SamePart,
  type TransportFor,
} from './engine-resolution'
import { saidBy, type Unreadable } from './limits'
import { governedFiles } from './payloads'
import { createPooledTransport } from './pool'
import type { CancelSignal } from './transport'
import { spell, VERBS, VERB_WORDS, type VerbName } from './verbs'

/**
 * Opening one project: the six pieces, in the one order that composes them.
 *
 * Every piece this package ships had a test and no caller. Resolving the engine, bounding
 * how many calls run at once, remembering an answer while the files it came off have not
 * moved, reading a payload with the shape its verb declares — each was built alone, and
 * putting them together was left to whoever wanted to read a project. Twenty-five test
 * files wrote a version of it, and no two wrote the same one.
 *
 * **The order is the whole content of this file**, and it is not arbitrary. The engine has
 * to be resolved before anything can be asked, because which copy answers decides what the
 * answers mean. `config` has to be read before the cache exists, because what stamps a
 * project is the governed files that project declares and only it can say what those are.
 * `commands` comes last because it is the read that says which of the others this build
 * would even accept.
 *
 * **An open project holds its stack.** Composing per read was the alternative and it
 * undoes three tasks at once: a cache that is rebuilt has remembered nothing, a pool that
 * is rebuilt bounds one call, and an engine resolved per read pays the interpreter start
 * RG65 spent a task removing. So this returns something a window keeps, and `invalidate`
 * is how a file watcher tells it the disk moved.
 *
 * **Nothing here has a process or a filesystem.** The candidates, the transport and the
 * stamp all arrive as arguments, exactly as `resolveEngine` takes its transport — which is
 * what keeps the composition itself in the half a web service would keep.
 */

export interface OpenProject {
  readonly root: string
  /** Which copy of roadkeep answered, and whether it is the one this project declares. */
  readonly engine: ResolvedEngine
  /** What this build publishes against what this app would send. */
  readonly capabilities: CapabilityReport
  /** The governed files this project declares, by role. What the stamp is taken over. */
  readonly governed: Readonly<Record<string, string>>
  /** Every later read goes through this. Pooled, cached, and reading each verb's shape. */
  readonly client: Client
  /** Forget what was remembered about this project. What a file watcher calls. */
  invalidate(): void
}

export type Opening =
  /** Nothing here answered `engines`, so which roadkeep governs this project is unknown. */
  | {
      readonly kind: 'unresolved'
      readonly root: string
      readonly reason: string
      readonly tried: readonly (readonly string[])[]
    }
  /**
   * An engine answered and then something it said could not be read. The engine is carried
   * because it is the useful half of that sentence: a screen can name the build that is
   * ahead of this app rather than reporting the project as absent.
   */
  | {
      readonly kind: 'unreadable'
      readonly root: string
      readonly engine: ResolvedEngine
      readonly unreadable: Unreadable
    }
  | { readonly kind: 'open'; readonly project: OpenProject }

export interface OpenOptions {
  readonly timeoutMs?: number
  readonly signal?: CancelSignal
  /** Calls in flight for this project at once. */
  readonly width?: number
  /** How two command lines are told apart, for the engine's own verification call. */
  readonly samePart?: SamePart
  /**
   * A short string that changes when these files do.
   *
   * Takes the governed files as well as the root, because the composition learns them from
   * `config` and the caller cannot know them before this call is made.
   */
  stampFor?(root: string, governed: readonly string[]): Promise<string>
  /** Whether an argv's answer may be remembered. Defaults to `readsOnly`. */
  cacheable?(argv: readonly string[]): boolean
}

/** Four is a floor a machine can raise, and it is what a portfolio read already allows. */
const DEFAULT_WIDTH = 4

/**
 * Whether this argv is one of the reads, and not the one read that writes.
 *
 * A rule about **this app's own verb table** and never about the engine's: it decides
 * whether an argv this app composed may be remembered, so a verb absent from the table is
 * not cacheable rather than assumed safe. `brief --claim` is the exception the table
 * already documents — a read that takes the line, which is a write wearing a read's shape,
 * and remembering it would serve a claim that happened once as though it happened twice.
 */
export function readsOnly(argv: readonly string[]): boolean {
  if (argv.includes('--claim')) return false
  const words = argv.slice(argv[0] === '-C' ? 2 : 0)
  return (Object.keys(VERBS) as VerbName[]).some((verb) => {
    const spelled = spell(verb, VERB_WORDS)
    return spelled.every((word, index) => words[index] === word)
  })
}

/**
 * Resolve, compose, and ask the two questions every later read depends on.
 *
 * @param candidates command lines to try for this project, in order. Discovering them
 *   needs a filesystem, so it belongs to whoever has one.
 * @param transportFor a transport for one command line. Making one needs a process.
 */
export async function openProject(
  root: string,
  candidates: readonly (readonly string[])[],
  transportFor: TransportFor,
  options: OpenOptions = {},
): Promise<Opening> {
  const call = {
    ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
    ...(options.signal === undefined ? {} : { signal: options.signal }),
  }

  const resolution = await resolveEngine(transportFor, root, candidates, {
    ...call,
    ...(options.samePart === undefined ? {} : { samePart: options.samePart }),
  })
  if (resolution.kind === 'unresolved') {
    return { kind: 'unresolved', root, reason: resolution.reason, tried: resolution.tried }
  }

  const engine = resolution.engine
  const pooled = createPooledTransport(transportFor(engine.engine), {
    width: options.width ?? DEFAULT_WIDTH,
  })

  // Uncached, because what the cache is keyed on is exactly what this read answers.
  const config = await createClient(pooled).call(root, 'config', {}, call)
  if (!config.ok) {
    return { kind: 'unreadable', root, engine, unreadable: couldNotRead('config', config.failure) }
  }
  if (config.value.kind === 'refused') {
    return {
      kind: 'unreadable',
      root,
      engine,
      unreadable: refusedBy('config', config.value.refusal.said),
    }
  }
  const governed = governedFiles(config.value.value)

  const files = Object.values(governed)
  const stampFor = options.stampFor
  // **No stamp is no cache, and it is the absence and not a substitute.** What expires a
  // remembered answer is the governed files moving, and a caller with no filesystem cannot
  // tell anyone when they did. Standing a clock in for that keeps answers against a value
  // nothing checks, which on a screen is worse than having kept none.
  const cached: CachingTransport | null =
    stampFor === undefined
      ? null
      : createCachingTransport(pooled, {
          stampFor: (asked) => stampFor(asked, files),
          cacheable: options.cacheable ?? readsOnly,
        })

  const client = createClient(cached ?? pooled)
  const commands = await client.call(root, 'commands', {}, call)
  if (!commands.ok) {
    return {
      kind: 'unreadable',
      root,
      engine,
      unreadable: couldNotRead('commands', commands.failure),
    }
  }

  return {
    kind: 'open',
    project: {
      root,
      engine,
      // A build too old to publish this read is a state and not a failure, which is what
      // `capabilitiesOf` has no way to say — so a refusal here is `unsupported` with the
      // version `engines` already gave, and the project still opens.
      capabilities:
        commands.value.kind === 'refused'
          ? {
              kind: 'unsupported',
              version: engine.payload.writing.version,
              reason: commands.value.refusal.said,
            }
          : capabilitiesOf(commands.value.value),
      governed,
      client,
      invalidate: () => {
        // Nothing to forget where nothing was kept, which is a no-op and not a failure:
        // a watcher should not have to know whether this project cached anything.
        cached?.invalidate(root)
      },
    },
  }
}

function couldNotRead(
  verb: string,
  failure: { readonly path: string; readonly expected: string; readonly got: string },
): Unreadable {
  return {
    reason: 'unreadable-payload',
    message:
      `\`${verb}\` answered with ${failure.got} where ` +
      `${failure.path || 'the answer'} should have been ${failure.expected}`,
    elapsedMs: 0,
    argv: [verb],
    said: '',
  }
}

function refusedBy(verb: string, said: string): Unreadable {
  return {
    reason: 'unreadable-payload',
    message: `\`${verb}\` was refused, so this project declares nothing this app can read`,
    elapsedMs: 0,
    argv: [verb],
    said: saidBy(said),
  }
}
