import { buildArgv } from './client'
import { type EnginesPayload, readEnginesPayload, splitCommandLine } from './engines'
import type { CancelSignal, Transport } from './transport'

/**
 * Which roadkeep writes for this project, asked of the project rather than of the machine.
 *
 * Three states have to be told apart and none of them is a crash. A project whose engine
 * is a modified working tree gets an answer that is that tree's, and this repeats it
 * rather than hiding it. A project whose copies disagree is described as disagreeing, not
 * as whichever answered first. A machine that can start nothing resolves nothing, and that
 * project is unreadable *with the reason* — the alternative being an app that quietly
 * substitutes a build of its own for the one the project chose.
 *
 * Nothing is bundled and nothing is guessed. An engine this app could not name is one it
 * does not use.
 */

/**
 * A candidate engine is a command line, and choosing one is choosing a transport: which
 * copy answers is exactly what a transport is built around. Supplying this is the caller's
 * job because making one needs a process, and this package may not have one.
 */
export type TransportFor = (engine: readonly string[]) => Transport

export interface ResolvedEngine {
  /** The engine every later call for this project goes through. */
  readonly engine: readonly string[]
  readonly payload: EnginesPayload
  /**
   * False when the copy that answered is not the one this project's `invoke` names and the
   * named one could not be reached. The answers are still real, but they are that copy's,
   * and a screen showing them without saying so is showing another project's rules.
   */
  readonly reachedDeclared: boolean
}

export type EngineResolution =
  | { readonly kind: 'resolved'; readonly engine: ResolvedEngine }
  | {
      readonly kind: 'unresolved'
      /** Sentence-shaped and meant to be shown: a blank project is not an answer. */
      readonly reason: string
      /** Every command line tried, so the reason names what was looked for. */
      readonly tried: readonly (readonly string[])[]
    }

export interface ResolveOptions {
  readonly timeoutMs?: number
  readonly signal?: CancelSignal
}

/** Ask one candidate. `null` means it is not an engine, which is not an error here. */
async function ask(
  transportFor: TransportFor,
  root: string,
  engine: readonly string[],
  options: ResolveOptions,
): Promise<EnginesPayload | null> {
  try {
    const result = await transportFor(engine).run({
      root,
      argv: buildArgv(root, 'engines', {}),
      ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
      ...(options.signal === undefined ? {} : { signal: options.signal }),
    })
    return readEnginesPayload(result.stdout)
  } catch {
    // Unspawnable, timed out or cancelled. A candidate that cannot run is a candidate that
    // is not the engine: the next one gets its turn, and running out of them is the answer.
    return null
  }
}

/**
 * Resolve the engine for one project.
 *
 * @param candidates command lines to try, in order, each already argv. Discovering them
 *   needs a filesystem, so it belongs to whoever has one; this only asks.
 */
export async function resolveEngine(
  transportFor: TransportFor,
  root: string,
  candidates: readonly (readonly string[])[],
  options: ResolveOptions = {},
): Promise<EngineResolution> {
  const tried: (readonly string[])[] = []

  for (const candidate of candidates) {
    tried.push(candidate)
    const payload = await ask(transportFor, root, candidate, options)
    if (payload === null) continue

    // The payload names the copy wired to this project, which need not be the one that
    // just answered: a launcher resolves an install of its own, and a `roadkeep` on PATH
    // is whatever the machine happens to have.
    const declared = splitCommandLine(payload.invoke)
    if (declared === null || declared.length === 0 || sameArgv(declared, candidate)) {
      return {
        kind: 'resolved',
        engine: { engine: candidate, payload, reachedDeclared: declared !== null },
      }
    }

    // It names something else. Reaching it costs a second call, and it is worth paying
    // once per project: adopting a command line without checking it runs is how an app
    // ends up answering from a copy nobody chose. RG7's cache stops it repeating.
    const viaDeclared = await ask(transportFor, root, declared, options)
    if (viaDeclared !== null && viaDeclared.writing.home === payload.writing.home) {
      return {
        kind: 'resolved',
        engine: { engine: declared, payload: viaDeclared, reachedDeclared: true },
      }
    }

    return { kind: 'resolved', engine: { engine: candidate, payload, reachedDeclared: false } }
  }

  return {
    kind: 'unresolved',
    reason:
      tried.length === 0
        ? 'nothing was offered as an engine for this project, so nothing was asked'
        : 'no candidate answered `engines --json`, so which roadkeep governs this project is unknown',
    tried,
  }
}

function sameArgv(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((part, index) => part === right[index])
}

/**
 * Whether the copy that answered is a working tree with uncommitted changes.
 *
 * Worth surfacing rather than smoothing over: the answers are that tree's, `lint` says so
 * out loud, and a screen repeating them as though they came from a release would quietly
 * attribute one person's edits to every project it reads.
 */
export function isModified(payload: EnginesPayload): boolean {
  return payload.writing.revision.includes('modified')
}

/** Whether the copies this project can reach disagree with each other. */
export function disagrees(payload: EnginesPayload): boolean {
  return !payload.agree || payload.split || payload.swapped
}
