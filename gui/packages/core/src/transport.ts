/**
 * The one call this whole app rests on, and the seam a web service replaces.
 *
 * Everything roadkeep-gui knows arrives out of one invocation of the roadkeep command, so
 * this file is that invocation's shape and nothing else: a project root, an argv array,
 * and back an exit code, two streams and a duration. There is one interface with one
 * method. Nothing above this layer knows a process was involved, which is what lets the
 * later service swap a spawn for an HTTP handler and change nothing in front of it.
 *
 * `CancelSignal` exists rather than `AbortSignal` because this package has neither the
 * DOM nor Node in scope, on purpose — it is the half a service keeps, and a type that only
 * exists in a browser or only in Node would be a dependency on the thing being swapped
 * out. A real `AbortSignal` satisfies this structurally, from either side.
 */

export interface CancelSignal {
  readonly aborted: boolean
  addEventListener(type: 'abort', listener: () => void): void
  removeEventListener(type: 'abort', listener: () => void): void
}

import type { EngineCall } from './tools'

export interface EngineRequest {
  /** The project the answer is about. The transport makes it the working directory. */
  readonly root: string
  /**
   * The command line after the engine, already split. Never a string: this app puts prose
   * a person typed into these elements, and a string is where a quoting defect lives.
   */
  readonly argv: readonly string[]
  /**
   * The same call as a tool and its arguments, where the caller composed one (RG101).
   *
   * Carried beside the argv rather than instead of it, because the engine has two surfaces
   * and a transport speaks one of them: the process and HTTP transports run the argv and
   * ignore this, and a transport speaking to a long-lived `roadkeep mcp` reads this and
   * ignores the argv. A request with only an argv still works everywhere — that is what a
   * door's own command line is, and nothing composed a tool call for it.
   */
  readonly call?: EngineCall
  /** Milliseconds after which the call is abandoned. Absent means no ceiling. */
  readonly timeoutMs?: number
  /** Cancellation from the caller — a screen redrawing while reads are still in flight. */
  readonly signal?: CancelSignal
}

export interface EngineResult {
  /** The engine's exit code. Non-zero is an answer, not a failure: `lint` exits 1 by design. */
  readonly code: number
  /**
   * The two streams, kept apart. `list` prints a line it could not accept on stderr with
   * the count, so a client that merged them could not tell an answer from a warning about
   * that answer.
   */
  readonly stdout: string
  readonly stderr: string
  readonly durationMs: number
}

/** Why a call produced no exit code at all. Each is the call not happening, not a refusal. */
export type EngineFailure =
  /** The engine could not be started: wrong path, not executable, no interpreter. */
  | 'unspawnable'
  /** It ran past `timeoutMs` and was killed. */
  | 'timeout'
  /** The caller's signal aborted it. */
  | 'aborted'

/**
 * Thrown when there is no exit code to report. A refusal by the engine is not this — that
 * arrives as a result with a non-zero code and something on stderr.
 */
export class EngineCallFailed extends Error {
  readonly reason: EngineFailure
  readonly durationMs: number

  constructor(reason: EngineFailure, message: string, durationMs: number) {
    super(message)
    this.name = 'EngineCallFailed'
    this.reason = reason
    this.durationMs = durationMs
  }
}

export interface Transport {
  run(request: EngineRequest): Promise<EngineResult>
}
