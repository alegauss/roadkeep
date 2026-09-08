import { ANSWERS, type VerbAnswers } from './answers'
import type { Parsed, Reader } from './reading'
import { readAnswer, type Answer } from './refusals'
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

export interface Client {
  /**
   * Run one verb and read what it answered.
   *
   * Three outcomes and they are not the same: a payload, a refusal the engine composed,
   * and an answer this app could not read — the last being a failure that names the field,
   * because a client that is behind the engine has to say which key moved. A call that
   * could not happen at all still raises `EngineCallFailed`: it is the transport's failure
   * and it is not an answer.
   */
  call<K extends VerbName>(
    root: string,
    verb: K,
    input: VerbInputs[K],
    options?: CallOptions,
  ): Promise<Parsed<Answer<VerbAnswers[K]>>>
}

/**
 * Build the whole command line for one call.
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
 * A verb's words are spread rather than its key split: some of the engine's verbs are two
 * words — `non-goal list`, `criterion list` — and `VERB_WORDS` carries the spelling as an
 * array. Nothing here ever turns a string into arguments, which is the whole point of an
 * argv being an array in the first place.
 */
export function buildArgv<K extends VerbName>(
  root: string,
  verb: K,
  input: VerbInputs[K],
): string[] {
  const argvFor = VERBS[verb] as (value: VerbInputs[K]) => readonly string[]
  return ['-C', root, ...spell(verb, VERB_WORDS), ...argvFor(input), '--json']
}

export function createClient(transport: Transport): Client {
  return {
    async call(root, verb, input, options = {}) {
      const result = await transport.run({
        root,
        argv: buildArgv(root, verb, input),
        ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
        ...(options.signal === undefined ? {} : { signal: options.signal }),
      })
      const reader = ANSWERS[verb] as Reader<VerbAnswers[typeof verb]>
      return readAnswer(reader, result)
    },
  }
}
