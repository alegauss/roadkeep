import { EngineCallFailed, type EngineFailure, type EngineRequest, type EngineResult, type Transport } from './transport'
import type { Parsed, Reader } from './reading'

/**
 * How long a read may take and how many may run at once — and what a project looks like
 * when one of them does not come back.
 *
 * A subprocess that never exits holds a slot forever, and a portfolio read fans out far
 * enough that one of them eventually will. So no call is unbounded, and a read that runs
 * out becomes a *state on that project* rather than a spinner that resolves for nobody.
 *
 * Both numbers are settings. A slow disk and a fast one are different machines, and the
 * deadline is the one number a person may genuinely have to raise — so it is clamped to a
 * sane range rather than fixed, and never silently ignored.
 */

export interface ReadLimits {
  /** Milliseconds one call may take before it is abandoned. */
  readonly timeoutMs: number
  /** How many calls may be in flight at once. */
  readonly width: number
}

/**
 * Fifteen seconds is roughly forty times a measured call, which is slow enough that a
 * cold disk or a large repository never trips it and fast enough that a hang is noticed
 * while somebody is still looking at the screen. Four is a floor a machine can raise.
 */
export const DEFAULT_LIMITS: ReadLimits = { timeoutMs: 15000, width: 4 }

const TIMEOUT_FLOOR = 1000
const TIMEOUT_CEILING = 600000
const WIDTH_CEILING = 32

/** Take a person's settings and make them usable, without pretending they were not given. */
export function withLimits(given: Partial<ReadLimits> = {}): ReadLimits {
  const timeoutMs = clamp(given.timeoutMs ?? DEFAULT_LIMITS.timeoutMs, TIMEOUT_FLOOR, TIMEOUT_CEILING)
  const width = clamp(Math.floor(given.width ?? DEFAULT_LIMITS.width), 1, WIDTH_CEILING)
  return { timeoutMs, width }
}

function clamp(value: number, low: number, high: number): number {
  if (!Number.isFinite(value)) return low
  return Math.min(high, Math.max(low, value))
}

/**
 * A project this app could not read, and everything a screen needs to say so.
 *
 * The elapsed time and the argv are both here because "unreadable" on its own is not
 * something anybody can act on: knowing it waited fifteen seconds on a command you can
 * see is the difference between a bug report and a shrug.
 *
 * **`said` is the engine's own prose**, and it is here because the one case where the
 * engine explained itself in full was the one case this app threw the explanation away.
 * Two of them, measured: a cached older build refusing this project's config exits 0 with
 * the unknown key named on stderr and nothing on stdout, and `section amend --replace`
 * with a fragment that does not match does the same, naming the fragment and the verb that
 * prints the prose. Both arrived as `expected JSON, found ""`.
 */
export interface Unreadable {
  readonly reason: EngineFailure | 'unreadable-payload'
  readonly message: string
  readonly elapsedMs: number
  readonly argv: readonly string[]
  /**
   * What the engine wrote on stderr, trimmed and bounded. Empty where there was none —
   * a call that never launched has no output to have written.
   */
  readonly said: string
}

/**
 * How much of stderr to keep.
 *
 * Generous enough for a refusal with its remedy — the longest measured here is under four
 * hundred characters — and bounded because stderr is not a field anybody promised a size
 * for, and a screen is not the place to discover that.
 */
const SAID_CEILING = 2000

/** The engine's prose, ready to put in front of a person. */
export function saidBy(stderr: string): string {
  const said = stderr.trim()
  return said.length <= SAID_CEILING ? said : `${said.slice(0, SAID_CEILING)}…`
}

export type ProjectRead<T> =
  | { readonly ok: true; readonly value: T; readonly durationMs: number }
  | { readonly ok: false; readonly unreadable: Unreadable }

/**
 * Run one read and turn every way it can fail into a state instead of an exception.
 *
 * Three things end here rather than propagating: the call not happening at all, the call
 * running past its deadline, and the answer not being the shape this app reads. A screen
 * drawing twenty projects has to be able to draw nineteen when one of them is broken.
 */
export async function attemptRead<T>(
  transport: Transport,
  request: EngineRequest,
  reader: Reader<T>,
): Promise<ProjectRead<T>> {
  let result: EngineResult
  try {
    result = await transport.run(request)
  } catch (cause) {
    if (cause instanceof EngineCallFailed) {
      return {
        ok: false,
        unreadable: {
          reason: cause.reason,
          message: cause.message,
          elapsedMs: cause.durationMs,
          argv: request.argv,
          // A call that never launched, or was killed, wrote nothing to carry.
          said: '',
        },
      }
    }
    throw cause
  }

  const said = saidBy(result.stderr)

  let source: unknown
  try {
    source = JSON.parse(result.stdout)
  } catch {
    return {
      ok: false,
      unreadable: {
        reason: 'unreadable-payload',
        // The engine's sentence leads where there is one: it names the cause, and the
        // argv only names the symptom.
        message:
          said === ''
            ? `\`${request.argv.join(' ')}\` answered with something that is not JSON`
            : said,
        elapsedMs: result.durationMs,
        argv: request.argv,
        said,
      },
    }
  }

  const parsed: Parsed<T> = reader(source, '')
  if (!parsed.ok) {
    return {
      ok: false,
      unreadable: {
        reason: 'unreadable-payload',
        message: `${parsed.failure.path || 'the answer'}: expected ${parsed.failure.expected}, found ${parsed.failure.got}`,
        elapsedMs: result.durationMs,
        argv: request.argv,
        said,
      },
    }
  }

  return { ok: true, value: parsed.value, durationMs: result.durationMs }
}
