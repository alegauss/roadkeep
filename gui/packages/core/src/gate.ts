import type { LintPayload } from './payloads'
import type { KeyOf } from './roots'

/**
 * Whether a project's governed files drifted, and what it costs to know.
 *
 * `lint` is the most expensive read there is and the only one that answers the question,
 * so running it across seventeen projects on every draw is not affordable. It runs once
 * per project per change — driven by the files moving, not by a screen redrawing — and the
 * row shows the last verdict with when it was taken.
 *
 * **Unknown is a third state and it is the honest one on first launch.** A row that showed
 * clean because nothing had run yet would be saying the opposite of what it knows, and
 * "this project is fine" is exactly the claim somebody would act on. Clean has to be
 * earned by a run.
 *
 * **A stale verdict says it is stale.** The stamp the verdict was taken against is kept
 * beside it, so a file written by this app, by a terminal or by an agent all make the same
 * verdict old in the same way — the answer is not thrown away, it is dated.
 */

export type GateVerdict =
  /** Nothing has been run. Not clean, and not drifted. */
  | 'unknown'
  /** The gate ran and found nothing. */
  | 'clean'
  /** The gate ran and found something. */
  | 'drifted'

export interface GateRecord {
  readonly verdict: Exclude<GateVerdict, 'unknown'>
  readonly problems: number
  /** When the gate was run, as an ISO string. */
  readonly taken: string
  /** The governed-file stamp it was run against. */
  readonly stamp: string
}

export interface GateHealth {
  readonly verdict: GateVerdict
  readonly problems: number
  /** Null while unknown: there is no moment to report. */
  readonly taken: string | null
  /** The files have moved since. The verdict is kept and dated rather than discarded. */
  readonly stale: boolean
}

export const UNKNOWN_GATE: GateHealth = {
  verdict: 'unknown',
  problems: 0,
  taken: null,
  stale: false,
}

/** Turn one `lint` answer into the record kept for a project. */
export function recordGate(lint: LintPayload, stamp: string, now: string): GateRecord {
  return {
    verdict: lint.clean ? 'clean' : 'drifted',
    problems: lint.problems,
    taken: now,
    stamp,
  }
}

/**
 * What a row should show, given what is on record and what the files look like now.
 *
 * `problems` is carried through even when stale, because a project that had three findings
 * an hour ago is more interesting than one that had none, and pretending not to know is a
 * different lie from the one `unknown` avoids.
 */
export function gateHealth(held: GateRecord | undefined, stamp: string): GateHealth {
  if (held === undefined) return UNKNOWN_GATE
  return {
    verdict: held.verdict,
    problems: held.problems,
    taken: held.taken,
    stale: held.stamp !== stamp,
  }
}

/** Whether this project's gate is worth running now. */
export function needsGate(held: GateRecord | undefined, stamp: string): boolean {
  return held === undefined || held.stamp !== stamp
}

/**
 * The verdicts held for every project, in memory only.
 *
 * Nothing here persists. A verdict is about a moment in a working tree and the files can
 * change while the app is closed, so a saved one would be stale in the one way this design
 * cannot detect — the stamp it was taken against would still match nothing it could check.
 */
export interface GateLedger {
  note(project: string, record: GateRecord): void
  healthOf(project: string, stamp: string): GateHealth
  /** Whether running the gate for this project would tell anybody anything new. */
  stale(project: string, stamp: string): boolean
  forget(project: string): void
  readonly size: number
}

export function createGateLedger(keyOf: KeyOf): GateLedger {
  const held = new Map<string, GateRecord>()

  return {
    note(project, record_) {
      held.set(keyOf(project), record_)
    },
    healthOf(project, stamp) {
      return gateHealth(held.get(keyOf(project)), stamp)
    },
    stale(project, stamp) {
      return needsGate(held.get(keyOf(project)), stamp)
    },
    forget(project) {
      held.delete(keyOf(project))
    },
    get size() {
      return held.size
    },
  }
}
