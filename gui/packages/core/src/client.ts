import type { CancelSignal, EngineResult, Transport } from './transport'
import { VERBS, type VerbInputs, type VerbName } from './verbs'

/**
 * The client: a verb, a project, and the transport it goes out over.
 *
 * It composes one argv and hands it to the transport. It parses nothing — a payload's
 * shape is its own task — and it decides nothing about which engine answers, which is
 * the transport's to be told.
 */

export interface CallOptions {
  readonly timeoutMs?: number
  readonly signal?: CancelSignal
}

export interface Client {
  call<K extends VerbName>(
    root: string,
    verb: K,
    input: VerbInputs[K],
    options?: CallOptions,
  ): Promise<EngineResult>
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
 * A verb name is split on spaces because some of the engine's verbs are two words —
 * `non-goal list`, `criterion list` — and the name is kept whole in the table because
 * that is the string `commands` publishes, which is what the capability check matches on.
 */
export function buildArgv<K extends VerbName>(
  root: string,
  verb: K,
  input: VerbInputs[K],
): string[] {
  const argvFor = VERBS[verb] as (value: VerbInputs[K]) => readonly string[]
  return ['-C', root, ...verb.split(' '), ...argvFor(input), '--json']
}

export function createClient(transport: Transport): Client {
  return {
    call(root, verb, input, options = {}) {
      return transport.run({
        root,
        argv: buildArgv(root, verb, input),
        ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
        ...(options.signal === undefined ? {} : { signal: options.signal }),
      })
    },
  }
}
