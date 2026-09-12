import {
  capabilitiesOf,
  readCapabilities,
  type CalledName,
  type CapabilityReport,
} from './capabilities'
import { buildArgv, createClient, type CallOptions, type Client } from './client'
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
import type { CancelSignal, EngineResult, Transport } from './transport'
import { keysOf } from './reading'
import { spell, VERBS, VERB_WORDS } from './verbs'

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
 * **And since RG122 it holds a process, so it is something to give back.** The transport a
 * screen reads through keeps a `roadkeep mcp` per project — six milliseconds a read against
 * seven hundred and thirty-eight — and a window that opened seventeen projects holds
 * seventeen engines. `close` is that, and the five ways of not opening call it
 * themselves: `config` is read *before* this knows whether the project opens, so a caller
 * holding no project would have nothing to close an engine with.
 *
 * **The pool stays, and what it bounds has changed.** A held engine multiplexes by frame
 * id, so four calls in flight to one process are not four interpreters. What is still
 * bounded is every read that surface does not publish — `stats` and `commands` among them —
 * which falls through to the transport that spawns, underneath the pool, exactly where a
 * portfolio read would otherwise fan a hundred candidates into a hundred processes.
 *
 * **Nothing here has a process or a filesystem.** The candidates, the transport, the stamp
 * and now the closing all arrive as arguments, exactly as `resolveEngine` takes its
 * transport — which is what keeps the composition itself in the half a web service would
 * keep.
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
  /**
   * What `client` reads through — pooled, and cached where a stamp exists — as a transport.
   *
   * Exposed for the two callers a client does not serve (RG143): a write, which `applyWrite`
   * hands a transport, and a process running requests another process composed, which has an
   * argv and not a verb. Both go through the one stack, so neither starts a second engine.
   */
  readonly transport: Transport
  /** Forget what was remembered about this project. What a file watcher calls. */
  invalidate(): void
  /**
   * Why its engine could not be held, in the engine's words — or null while it is, before
   * anything was read, or where nothing holds engines at all (RG137).
   *
   * A project here reads at spawn speed, seven hundred milliseconds where the rest read at
   * six, and this is the sentence its row gives for being the slow one. Asked and not kept:
   * a handshake fails on the first read of a root, which is after the project opened.
   */
  unheld(): string | null
  /**
   * Give back what this project holds — the engine process the transport kept for it.
   *
   * Awaited rather than fired off, because on Windows a killed-but-not-yet-exited server
   * still holds the project as its working directory, and whoever closes a project is often
   * the one about to remove or move it. Safe to call twice: a window closing and a process
   * quitting are two owners of one lifetime.
   */
  close(): Promise<void>
}

export type Opening =
  /** Nothing here answered `engines`, so which roadkeep governs this project is unknown. */
  | {
      readonly kind: 'unresolved'
      readonly root: string
      /**
       * In English, for a log. `code` is what a screen says in the window's language.
       *
       * @notForScreen `code`, looked up in the catalogue with `say`
       */
      readonly reason: string
      readonly code: 'nothing-offered' | 'none-answered'
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
  /**
   * An engine answered, and said no roadkeep project governs this folder (RG13).
   *
   * An answer and not a failure: the engine's own `governed`, read off the one call that
   * says it, before anything that needs a project is asked. Until then it arrived as a
   * `config` this app could not read — a folder rejected by a read failing, and the sentence
   * that came with it said this app was behind the engine.
   */
  | { readonly kind: 'ungoverned'; readonly root: string; readonly engine: ResolvedEngine }
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
  stampFor?: (root: string, governed: readonly string[]) => Promise<string>
  /** Whether an argv's answer may be remembered. Defaults to `readsOnly`. */
  cacheable?: (argv: readonly string[]) => boolean
  /**
   * How to give back everything the transports this open built are holding.
   *
   * Injected for the reason the transport itself is: a held engine is a process, and this
   * package does not have one. Absent, `close` is a no-op — which is the truth for a
   * transport that spawns per call and keeps nothing.
   */
  closing?: () => Promise<void>
  /**
   * Why the transports this open built could not hold its engine, or null (RG137).
   *
   * The fifth thing this composition takes rather than computes, beside the candidates, the
   * transport, the stamp and the closing — and for their reason: holding an engine is a
   * process, which this package does not have. Absent, a project answers null, which is the
   * truth for a transport that spawns per call and holds nothing.
   */
  unheld?: () => string | null
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
  // The one place that reads the wrapper `wrapArgv` writes, rather than writing one: the
  // leading `-C <root>` is skipped so the verb's own words line up at the head.
  const words = argv.slice(argv[0] === '-C' ? 2 : 0)
  return keysOf(VERBS).some((verb) => {
    const spelled = spell(verb, VERB_WORDS)
    return spelled.every((word, index) => words[index] === word)
  })
}

/**
 * Resolve, compose, and ask the two questions every later read depends on.
 *
 * The whole of this function is the lifetime, and `compose` below is the order. They are
 * separate because the order has five ways to end without a project and every one of them
 * can already have started an engine: one `close` on the way out is a promise nothing can
 * forget, and five of them are five places to forget it.
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
  const closing = options.closing
  let closed: Promise<void> | null = null
  // Once, and the promise is the memory: two owners closing at the same moment wait on the
  // same kill rather than racing a second one against a process that is already going.
  const close = (): Promise<void> => (closed ??= closing === undefined ? RESOLVED : closing())

  const opening = await compose(root, candidates, transportFor, options, close)
  if (opening.kind !== 'open') await close()
  return opening
}

const RESOLVED: Promise<void> = Promise.resolve()

/** The order, which is the whole content of the rest of this file. */
async function compose(
  root: string,
  candidates: readonly (readonly string[])[],
  transportFor: TransportFor,
  options: OpenOptions,
  close: () => Promise<void>,
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
    return {
      kind: 'unresolved',
      root,
      reason: resolution.reason,
      code: resolution.code,
      tried: resolution.tried,
    }
  }

  const engine = resolution.engine
  const pooled = createPooledTransport(transportFor(engine.engine), {
    width: options.width ?? DEFAULT_WIDTH,
  })

  // Uncached, because what the cache is keyed on is exactly what this read answers.
  const config = await createClient(pooled).call(root, 'config', {}, call)
  // Since RG99 the client carries the call that never happened as a state too, so this is
  // the whole of what can go wrong here rather than the two thirds a `try` used to leave.
  if (config.kind === 'unreadable') {
    // **Which copy answered is the useful half** (RG193). A build older than the verb answers
    // with its own usage dump — every command it has, and nothing about the one it lacks — so
    // the prose reaches a row as prose and the reader is left to recognise a version that is
    // behind.
    //
    // **Only where the answer was no payload at all.** A build that does not publish a verb
    // cannot produce that verb's payload, and cannot refuse it either: a refusal is this
    // engine's own document about a verb it knows. So a shape this app could not read is a
    // build that *has* `config`, and asking `commands` about it would replace a true sentence
    // with a wrong one. `not-json` and the engine's own prose are the two that can be a usage
    // dump, and they are the two asked about.
    if (config.unreadable.code === '' || config.unreadable.code === 'not-json') {
      // Asked here and only here: on a path that has already failed, and through the pooled
      // transport rather than the cache the failed `config` never built.
      const behind = await notPublished(pooled, root, 'config', engine, call, config.unreadable)
      if (behind !== null) return { kind: 'unreadable', root, engine, unreadable: behind }
    }
    return { kind: 'unreadable', root, engine, unreadable: config.unreadable }
  }
  if (config.kind === 'refused') {
    return {
      kind: 'unreadable',
      root,
      engine,
      unreadable: refusedBy('config', config.refusal.said),
    }
  }
  // The cheap no (RG13). Asked of the engine, which owns the rule for what governs a folder
  // — this never looks for a `roadkeep.toml` above the one it was given.
  if (!config.value.governed) return { kind: 'ungoverned', root, engine }
  const governed = governedFiles(config.value)

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

  const transport = cached ?? pooled
  const client = createClient(transport)
  const commands = await client.call(root, 'commands', {}, call)
  if (commands.kind === 'unreadable') {
    return { kind: 'unreadable', root, engine, unreadable: commands.unreadable }
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
        commands.kind === 'refused'
          ? {
              kind: 'unsupported',
              version: engine.payload.writing.version,
              reason: commands.refusal.said,
            }
          : capabilitiesOf(commands.value),
      governed,
      client,
      transport,
      invalidate: () => {
        // Nothing to forget where nothing was kept, which is a no-op and not a failure:
        // a watcher should not have to know whether this project cached anything.
        cached?.invalidate(root)
      },
      unheld: () => options.unheld?.() ?? null,
      close,
    },
  }
}

/**
 * A refusal, said as the state a project is in.
 *
 * The other two ways a read can fail no longer need a builder here: since RG99 the client
 * hands back an `Unreadable` already carrying the argv, the elapsed time and whatever the
 * engine wrote — all of which this had to leave empty.
 */
/**
 * The unreadable for a build that does not publish the verb a read needed, or null (RG193).
 *
 * Null is every other case and is the important half: this only ever says *behind*, never
 * *broken*. A `commands` that cannot be read at all, a build that publishes the verb after
 * all, a call that never launched — each leaves the original failure to speak for itself,
 * because a wrong diagnosis is worse than the usage dump it replaces.
 *
 * `readCapabilities` already turns prose from a build too old to answer `commands` into
 * `unsupported` with its version, and `capabilitiesOf` already says whether a build
 * publishes a verb. Nothing is decided here that those two do not already answer.
 */
async function notPublished(
  transport: Transport,
  root: string,
  verb: CalledName,
  engine: ResolvedEngine,
  call: CallOptions,
  failed: Unreadable,
): Promise<Unreadable | null> {
  let ran: EngineResult
  try {
    ran = await transport.run({ root, argv: buildArgv(root, 'commands', {}), ...call })
  } catch {
    // The failure being explained is the one that already happened; this read failing adds
    // nothing to it.
    return null
  }
  if (ran.code !== 0) return null

  // The version that is *running*, which is what a reader has to update.
  const running = engine.payload.writing.version
  const report = readCapabilities(ran.stdout, running)
  // A build too old to answer `commands` is one too old to be asked about `config`, and its
  // version is what the reader needs either way.
  const missing = report.kind === 'unsupported' ? true : !report.byVerb[verb].callable
  if (!missing) return null

  const version = running === '' ? 'of an unknown version' : running
  // The diagnosis replaces the sentence and nothing else. What the engine wrote, what was
  // asked and how long it took stay the failed call's: the usage dump is the evidence for
  // this answer, and reporting `commands`' own silence instead would drop it.
  return {
    ...failed,
    message: `the copy answering here is roadkeep ${version}, which has no \`${verb}\``,
    code: 'behind',
    fields: { verb, version },
  }
}

function refusedBy(verb: string, said: string): Unreadable {
  return {
    reason: 'unreadable-payload',
    message: `\`${verb}\` was refused, so this project declares nothing this app can read`,
    code: 'declares',
    fields: { verb },
    elapsedMs: 0,
    argv: [verb],
    said: saidBy(said),
  }
}
