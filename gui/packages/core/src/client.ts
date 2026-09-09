import { ANSWERS, type VerbAnswers } from './answers'
import { attemptRead, type Unreadable } from './limits'
import type { Reader } from './reading'
import { readAnswerFrom, type Refusal } from './refusals'
import { callFor, type EngineCall } from './tools'
import type { CancelSignal, Transport } from './transport'
import { spell, VERBS, VERB_WORDS, type VerbInputs, type VerbName } from './verbs'

/**
 * The client: a verb, a project, and the transport it goes out over.
 *
 * It composes one argv, hands it to the transport, and reads the answer with the shape
 * that verb declares. It decides nothing about which engine answers, which is the
 * transport's to be told, and it decides nothing about the payload's meaning either — the
 * shape says what the fields are and every rule about them is somebody else's.
 *
 * **The reader is not a parameter.** It was, in the sense that there was none and each
 * caller picked one, which is a reader chosen at the call site and therefore a reader that
 * can be the wrong one. `ANSWERS[verb]` is the verb's own, and a caller cannot now read a
 * `pick` with `list`'s shape or forget to read at all.
 *
 * What this does not return is stdout. A caller wanting the bytes wants the transport, not
 * a client — `buildArgv` composes the same command line for it, and `seam` compares two
 * transports that way because that comparison is about them and not about this.
 */

export interface CallOptions {
  readonly timeoutMs?: number
  readonly signal?: CancelSignal
}

/**
 * What one read answered — the same three states `applyWrite` gives a write, spelled the
 * same way, because a screen drawing a read and a screen drawing a write are one screen
 * (RG99).
 */
export type ReadOutcome<T> =
  | { readonly kind: 'read'; readonly value: T; readonly durationMs: number }
  /** The engine declined, naming the fields where it named any. */
  | { readonly kind: 'refused'; readonly refusal: Refusal; readonly durationMs: number }
  /**
   * The call did not happen, ran past its deadline, or answered something this app cannot
   * read. One state for the three because what a row does with them is the same: say so,
   * and say what it was doing — which is what `Unreadable` carries.
   */
  | { readonly kind: 'unreadable'; readonly unreadable: Unreadable }

export interface Client {
  /**
   * Run one verb and read what it answered.
   *
   * **Nothing raises.** A call that never happened, one that ran past its deadline and one
   * whose answer this app could not read are all `unreadable`, because a portfolio drawing
   * twenty projects has to draw nineteen when one of them hangs — and a caller that had to
   * wrap every call in a `try` would be every caller (RG99). The transport still throws
   * `EngineCallFailed`; it stops here.
   */
  call<K extends VerbName>(
    root: string,
    verb: K,
    input: VerbInputs[K],
    options?: CallOptions,
  ): Promise<ReadOutcome<VerbAnswers[K]>>
}

/**
 * The one way this app spells a command line, for a read and for a write alike.
 *
 * Three rules live here and nowhere else, which is the point: they were written twice and
 * had begun to drift.
 *
 * `-C <root>` leads, because the engine takes it before the verb, and it is passed even
 * though the transport also makes `root` the working directory. Both, deliberately: an
 * answer has to be about the project on screen and never about the directory this app
 * happened to start in, and one of the two mechanisms is enough only until something
 * changes the other.
 *
 * `--json` closes every call for the same reason no verb declares it: a client that read
 * human output would be reading a format nobody promised it.
 *
 * The verb arrives already spelled, as words rather than a key: some of the engine's verbs
 * are two — `non-goal list`, `criterion list`, `section add` — and each table carries the
 * spelling as an array. Nothing here ever turns a string into arguments, which is the whole
 * point of an argv being an array in the first place.
 *
 * **What stays separate is the tables.** Which verbs may be read and which may be written
 * is about what this app is allowed to offer, and it has nothing to do with how a command
 * line is spelled — so the two builders keep their own tables and share this.
 */
export function wrapArgv(
  root: string,
  words: readonly string[],
  args: readonly string[] = [],
): string[] {
  return ['-C', root, ...words, ...args, '--json']
}

/** Build the whole command line for one read, off the read table's own spelling. */
export function buildArgv<K extends VerbName>(
  root: string,
  verb: K,
  input: VerbInputs[K],
): string[] {
  const argvFor = VERBS[verb] as (value: VerbInputs[K]) => readonly string[]
  return wrapArgv(root, spell(verb, VERB_WORDS), argvFor(input))
}

/**
 * The same read, spelled for the engine's tool surface (RG101).
 *
 * Composed here and carried on every request, so a transport speaking to a long-lived
 * `roadkeep mcp` has what it needs and one that spawns can ignore it. Off the same
 * spelling table as the argv, which is what keeps the two from naming different verbs.
 */
export function buildCall<K extends VerbName>(verb: K, input: VerbInputs[K]): EngineCall {
  return callFor(verb, input, VERB_WORDS)
}

export function createClient(transport: Transport): Client {
  return {
    async call(root, verb, input, options = {}) {
      const reader = ANSWERS[verb] as Reader<VerbAnswers[typeof verb]>

      // Through `attemptRead` rather than beside it: it already turns a call that did not
      // happen, one that ran out and one whose stdout is not JSON into the same state, with
      // the engine's own stderr carried. What is handed in is the *answer* reader, so the
      // refusal split happens inside that one parse instead of in a second one here.
      const read = await attemptRead(
        transport,
        {
          root,
          argv: buildArgv(root, verb, input),
          call: buildCall(verb, input),
          ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
          ...(options.signal === undefined ? {} : { signal: options.signal }),
        },
        (source, path) => readAnswerFrom(reader, source, path),
      )

      if (!read.ok) return { kind: 'unreadable', unreadable: read.unreadable }
      return read.value.kind === 'refused'
        ? { kind: 'refused', refusal: read.value.refusal, durationMs: read.durationMs }
        : { kind: 'read', value: read.value.value, durationMs: read.durationMs }
    },
  }
}
