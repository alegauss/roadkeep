import { EngineCallFailed, type EngineResult, type Transport } from './transport'
import { readAnswer, type Refusal } from './refusals'
import type { Reader } from './reading'
import type { Unreadable } from './limits'
import { WRITES, WRITE_WORDS, type WriteInputs, type WriteName } from './writes'
import { spell } from './verbs'

/**
 * A write, composed here and performed by the command.
 *
 * This app composes an argv and runs it. It never opens a governed file, never renders a
 * line, never fills a field — the person's words go into an array and the verb decides
 * what becomes of them. What this adds over a terminal is the schema arriving before the
 * prose; the verb still decides, and its refusal is what the person sees.
 *
 * **Composing and running are two acts.** `composeWrite` returns the whole command line
 * and touches nothing, so a write can be read before it is approved and repeated after it
 * — and so a screen that shows one has something to show. Nothing here decides whether it
 * should run.
 *
 * **Three states and no more.** `readAnswer` already tells a payload from a refusal by
 * `said` rather than by an exit code — the distinction that stops `lint`'s own findings
 * being read as an error — so a write is applied, refused, or unreadable. The third is
 * `attemptRead`'s state and is spelled the same way, because a write that timed out is a
 * read that timed out with more at stake: the caller cannot know whether it landed, and a
 * state that says so is the only honest answer.
 */

/** A command line, built and not yet run. */
export interface Composed {
  readonly verb: WriteName
  /** The whole argv, `-C <root>` and `--json` included. An array, never a shell string. */
  readonly argv: readonly string[]
  readonly root: string
}

/**
 * Build the command line for one write.
 *
 * `-C <root>` leads and `--json` closes, for the reasons `buildArgv` gives for a read, and
 * the verb's words are spread from `WRITE_WORDS` rather than split out of its key — which
 * matters most here, since almost every write to come is `section add`, `criterion add`,
 * `block add`.
 */
export function composeWrite<K extends WriteName>(
  root: string,
  verb: K,
  input: WriteInputs[K],
): Composed {
  const argvFor = WRITES[verb] as (value: WriteInputs[K]) => readonly string[]
  return {
    verb,
    root,
    argv: ['-C', root, ...spell(verb, WRITE_WORDS), ...argvFor(input), '--json'],
  }
}

export type WriteOutcome<T> =
  | { readonly kind: 'applied'; readonly value: T; readonly durationMs: number }
  /** The engine declined, naming the fields. Nothing was written — that is its promise. */
  | { readonly kind: 'refused'; readonly refusal: Refusal; readonly durationMs: number }
  /**
   * Neither. The call did not happen, ran past its deadline, or answered something this
   * app cannot read — and **whether the write landed is unknown**, which is why this is
   * its own state rather than a refusal with a different message.
   */
  | { readonly kind: 'unreadable'; readonly unreadable: Unreadable }

/**
 * Run one composed write and turn every way it can fail into a state.
 *
 * The reader is the verb's own payload shape. It is passed in rather than looked up here
 * so that adding a write verb stays what the table says it is: a row, and a shape beside
 * it, and no branch in this function.
 */
export async function applyWrite<T>(
  transport: Transport,
  composed: Composed,
  reader: Reader<T>,
  options: { readonly timeoutMs?: number } = {},
): Promise<WriteOutcome<T>> {
  let result: EngineResult
  try {
    result = await transport.run({
      root: composed.root,
      argv: composed.argv,
      ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
    })
  } catch (cause) {
    if (cause instanceof EngineCallFailed) {
      return {
        kind: 'unreadable',
        unreadable: {
          reason: cause.reason,
          message: cause.message,
          elapsedMs: cause.durationMs,
          argv: composed.argv,
        },
      }
    }
    throw cause
  }

  const answer = readAnswer(reader, result)
  if (!answer.ok) {
    return {
      kind: 'unreadable',
      unreadable: {
        reason: 'unreadable-payload',
        message:
          `\`${composed.verb}\` answered with ${answer.failure.got} where ` +
          `${answer.failure.path || 'the answer'} should have been ${answer.failure.expected}`,
        elapsedMs: result.durationMs,
        argv: composed.argv,
      },
    }
  }

  return answer.value.kind === 'refused'
    ? { kind: 'refused', refusal: answer.value.refusal, durationMs: result.durationMs }
    : { kind: 'applied', value: answer.value.value, durationMs: result.durationMs }
}

/**
 * Whether the write landed, for a caller that only needs the one bit.
 *
 * Refused and unreadable are both false and they are not the same thing, which is why
 * this returns a boolean and the outcome keeps its three states: a refusal promises
 * nothing was written and an unreadable answer promises nothing at all.
 */
export function applied<T>(outcome: WriteOutcome<T>): boolean {
  return outcome.kind === 'applied'
}
