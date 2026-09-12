import {
  BRIDGE_TOPICS,
  EVERY_SOURCE,
  type BridgedRequest,
  type BridgedResult,
  type OpenedProject,
  type RendererBridge,
  type Topic,
  type TopicEvents,
  type Withheld,
  type WithheldCode,
} from './bridge'
import { argumentsOf, CALLED_NAMES, CALLED_WORDS, flagsFor, type CalledName } from './capabilities'
import { createClient } from './client'
import type { SamePart } from './engine-resolution'
import type { Opening } from './opening'
import { aString, anything, asRecord, dictionaryOf, listOf, record } from './reading'
import { toolFor, type EngineCall } from './tools'
import {
  EngineCallFailed,
  type EngineRequest,
  type EngineResult,
  type Transport,
} from './transport'
import { spell } from './verbs'

/**
 * One process running what another composed (RG143), both halves of it.
 *
 * The renderer holds no process, so every read a screen makes crosses to the one that does.
 * Two halves meet at `RendererBridge`, and both are here because neither needs a process to
 * be written: what the carrier refuses, and how the renderer turns the answers back into the
 * transport and the project every reader in this package already takes.
 *
 * **The carrier opens and keeps; the renderer asks.** The alternative was the renderer
 * running `openProject` itself over the bridge, asking main for candidates and stamps. That
 * hands the renderer command lines to choose between and has main spawn what it chose — and
 * the held engines would belong to the one process that never closes anything.
 *
 * **What the carrier refuses is a table question, and never a path question.** §RG85 set it
 * for a service: a root it did not catalogue, and an argv the verb table did not compose. A
 * verb check alone is short of the second, since the engine takes options this app never
 * sends, so every option has to be one the verb's own builder emits and every tool argument
 * one its input has. And one the builder does emit is still refused when it names a file:
 * `section add --body-file` would copy any file on the machine into a governed doc.
 */

/**
 * The verb whose words head this command line, the longest spelling winning, or null.
 *
 * Longest because a family and its member share a first word, and `section add` is not
 * `section`.
 */
function tabledIn(words: readonly string[]): CalledName | null {
  let found: CalledName | null = null
  let length = 0
  for (const verb of CALLED_NAMES) {
    const spelled = spell(verb, CALLED_WORDS)
    if (spelled.length > length && spelled.every((word, index) => words[index] === word)) {
      found = verb
      length = spelled.length
    }
  }
  return found
}

/**
 * The option this part names, where the engine's parser would read it as one, or null.
 *
 * argparse's own order, near enough to be the guard's: a leading dash, an `=` split before
 * anything else, and only then a space ruling it a value — so `--body-file=a b.md` is an
 * option, and a body opening on `- a list item` is prose. A negative number is a value.
 */
function optionNamed(part: string): string | null {
  if (!part.startsWith('-') || part.length < 2 || /^-\d+(\.\d+)?$/.test(part)) return null
  const head = part.split('=', 1)[0] ?? part
  return head.includes(' ') ? null : head
}

/**
 * Whether an option or argument names a file for the engine to open, judged by its spelling.
 *
 * Refused from a renderer whichever table emits it — `section add` does, as `--body-file`.
 * A process with no filesystem has no path it could have chosen, and the one it could name
 * is any file on the machine, copied into a governed doc and read back. A screen holds the
 * prose itself and sends that. By the name rather than a list, because every such option the
 * engine has is spelled this way and a list beside the builders drifts from them.
 */
function opensAFile(name: string): boolean {
  return name.endsWith('-file') || name.endsWith('_file')
}

/**
 * Why a carrier will not run this request for another process, or null where it will.
 *
 * The root is checked by whoever holds the catalogue; this is the rest — the command line is
 * about that root, closes with `--json`, names a verb one of the two tables holds, and every
 * option in it is one that verb's builder emits and none names a file. A tool call beside it
 * names the same verb's tool and only arguments its input has, since a held engine runs the
 * call and not the argv.
 *
 * @param sameRoot how two spellings of one folder are told apart, which needs a filesystem.
 */
export function withheldBecause(request: EngineRequest, sameRoot: SamePart): string | null {
  const { argv, root } = request
  const about = argv[1]
  if (argv[0] !== '-C' || about === undefined || !sameRoot(about, root)) {
    return `the command line is not about ${root}`
  }
  if (argv.at(-1) !== '--json') return 'the command line does not ask for JSON'

  const words = argv.slice(2, -1)
  const verb = tabledIn(words)
  if (verb === null) return `\`${words[0] ?? ''}\` is in neither verb table`

  return (
    strayOption(verb, words) ??
    (request.call === undefined ? null : strayArgument(verb, request.call))
  )
}

/** The first option after the verb's words that its builder never emits, or names a file. */
function strayOption(verb: CalledName, words: readonly string[]): string | null {
  const options = new Set(flagsFor(verb))
  for (const part of words.slice(spell(verb, CALLED_WORDS).length)) {
    const option = optionNamed(part)
    if (option === null) continue
    if (opensAFile(option)) return `\`${option}\` names a file, and a screen sends the prose`
    if (!options.has(option)) {
      return `\`${option}\` is not an option this app composes \`${words[0] ?? ''}\` with`
    }
  }
  return null
}

/** Why a tool call is not the one this verb composes: another tool, or an argument it lacks. */
function strayArgument(verb: CalledName, call: EngineCall): string | null {
  const tool = toolFor(verb, CALLED_WORDS)
  if (call.tool !== tool) {
    return `the tool call names \`${call.tool}\` where the command line names \`${tool}\``
  }
  const named = Object.keys(call.arguments)
  const file = named.find(opensAFile)
  if (file !== undefined) return `\`${file}\` names a file, and a screen sends the prose`
  const known = argumentsOf(verb)
  const stray = named.find((name) => !known.has(name))
  return stray === undefined ? null : `\`${stray}\` is not an argument \`${tool}\` is composed with`
}

const readCall = record<EngineCall>({ tool: aString, arguments: dictionaryOf(anything) })

/**
 * A request as the renderer sent it, or null where it is not one.
 *
 * A channel argument is the renderer's word and crosses as whatever it was, so the shape is
 * read before anything is asked of it: an argv that is not strings is a command line the
 * guard below cannot even look at.
 */
export function requestFrom(value: unknown): BridgedRequest | null {
  const fields = asRecord(value)
  if (fields === null) return null
  const argv = listOf(aString)(fields['argv'], 'argv')
  if (!argv.ok) return null
  const call = fields['call'] === undefined ? null : readCall(fields['call'], 'call')
  if (call !== null && !call.ok) return null
  const timeoutMs = fields['timeoutMs']
  if (timeoutMs !== undefined && typeof timeoutMs !== 'number') return null

  return {
    argv: argv.value,
    ...(call === null ? {} : { call: call.value }),
    ...(timeoutMs === undefined ? {} : { timeoutMs }),
  }
}

/**
 * Whether a channel argument names a topic (RG144). A topic crosses as the renderer's word,
 * like a root or a request, and one this table does not hold is a subscription to nothing.
 */
export function isTopic(value: unknown): value is Topic {
  return typeof value === 'string' && Object.hasOwn(BRIDGE_TOPICS, value)
}

const KEYS: { readonly [T in Topic]: (event: TopicEvents[T]) => string } = {
  governed: (event) => event.root,
  session: (event) => event.session,
  gate: (event) => event.root,
  // One catalogue, so one source: the key is the same one a screen subscribes with (RG180).
  catalogue: () => EVERY_SOURCE,
}

/**
 * The key an event belongs to (RG144). One channel carries every source of a topic, so a
 * listener subscribed to one project hears the others' events too and keeps its own by this.
 */
export function keyOfEvent<T extends Topic>(topic: T, event: TopicEvents[T]): string {
  const keyOf: (one: TopicEvents[T]) => string = KEYS[topic]
  return keyOf(event)
}

/**
 * Whether an event is one a listener asked for (RG178).
 *
 * Its own key, or every source of the topic. The second is why this is a function and not a
 * comparison at the listener: an event carries the key of the source it came from and never
 * the key somebody subscribed with, so a listener asking for all of them would compare its
 * own `*` against a session's key and hear nothing.
 */
export function heardBy<T extends Topic>(topic: T, event: TopicEvents[T], asked: string): boolean {
  return asked === EVERY_SOURCE || keyOfEvent(topic, event) === asked
}

/**
 * A request that will not run, as the answer `run` gives. Nothing started, so no time passed.
 *
 * The sentence and the code are both given because they answer different readers: the first
 * is what a log and a defect report keep, and the second is what a screen says in the
 * window's own language (RG192). A caller with no code is one whose prose is its own report
 * of a command line this app composed, which is drawn as it was written.
 */
export function withheldResult(
  reason: string,
  code: WithheldCode = '',
  fields: Readonly<Record<string, string>> = {},
): BridgedResult {
  return { kind: 'failed', reason: 'withheld', message: reason, code, fields, durationMs: 0 }
}

/**
 * Run one request and answer it as data, for the side of the bridge that has the engine.
 *
 * The failure is taken apart into its fields here and put back together by
 * `bridgedTransport`, which is the round trip a thrown class cannot make over IPC.
 */
export async function bridgedRun(run: () => Promise<EngineResult>): Promise<BridgedResult> {
  try {
    return { kind: 'ran', result: await run() }
  } catch (cause) {
    // No code on either: a spawn that failed, a deadline, a thrown class — the words are the
    // transport's own, quoted rather than translated, which is the reading `attemptRead`
    // already settled for the same prose arriving the other way (RG192).
    if (cause instanceof EngineCallFailed) {
      return {
        kind: 'failed',
        reason: cause.reason,
        message: cause.message,
        code: '',
        fields: {},
        durationMs: cause.durationMs,
      }
    }
    return {
      kind: 'failed',
      reason: 'unspawnable',
      message: cause instanceof Error ? cause.message : String(cause),
      code: '',
      fields: {},
      durationMs: 0,
    }
  }
}

/** An opening with the process taken out of it, for the side of the bridge that keeps it. */
export function openedFrom(opening: Opening): OpenedProject {
  if (opening.kind !== 'open') return opening
  const { project } = opening
  return {
    kind: 'open',
    root: project.root,
    engine: project.engine,
    capabilities: project.capabilities,
    governed: project.governed,
    declares: project.declares,
    mark: project.mark,
    unheld: project.unheld(),
  }
}

/**
 * A transport whose `run` is the bridge's, for the renderer.
 *
 * **Cancellation is honoured here and not across.** A signal cannot be sent, so an aborted
 * call is refused before it is asked and abandoned if it aborts while in flight — the carrier
 * finishes it and nobody reads the answer, which is what a screen that redrew wanted.
 */
export function bridgedTransport(bridge: Pick<RendererBridge, 'run'>): Transport {
  return {
    run(request: EngineRequest): Promise<EngineResult> {
      const { signal } = request
      const aborted = (): EngineCallFailed =>
        new EngineCallFailed('aborted', 'the call was cancelled before it answered', 0)
      if (signal?.aborted === true) return Promise.reject(aborted())

      const crossing: BridgedRequest = {
        argv: request.argv,
        ...(request.call === undefined ? {} : { call: request.call }),
        ...(request.timeoutMs === undefined ? {} : { timeoutMs: request.timeoutMs }),
      }

      return new Promise<EngineResult>((resolve, reject) => {
        const abandon = (): void => {
          reject(aborted())
        }
        signal?.addEventListener('abort', abandon)

        bridge.run(request.root, crossing).then(
          (answer) => {
            signal?.removeEventListener('abort', abandon)
            if (answer.kind === 'ran') resolve(answer.result)
            else reject(new EngineCallFailed(answer.reason, answer.message, answer.durationMs))
          },
          (cause: unknown) => {
            signal?.removeEventListener('abort', abandon)
            reject(
              new EngineCallFailed(
                'unspawnable',
                cause instanceof Error ? cause.message : String(cause),
                0,
              ),
            )
          },
        )
      })
    },
  }
}

/**
 * Open one project from the renderer: the carrier opens it, and this builds the project
 * every reader takes over the carrier's `run`.
 *
 * `invalidate` does nothing here and that is the truth: the cache is the carrier's, keyed on
 * a stamp taken per read, so an answer it holds is never older than the files. `close` does
 * nothing either — the engines are the carrier's, and it closes them when it quits.
 */
export async function openOver(
  bridge: Pick<RendererBridge, 'open' | 'run'>,
  root: string,
): Promise<Opening | Withheld> {
  const opened = await bridge.open(root)
  if (opened.kind !== 'open') return opened

  const transport = bridgedTransport(bridge)
  return {
    kind: 'open',
    project: {
      root: opened.root,
      engine: opened.engine,
      capabilities: opened.capabilities,
      governed: opened.governed,
      declares: opened.declares,
      mark: opened.mark,
      client: createClient(transport),
      transport,
      invalidate: () => undefined,
      unheld: () => opened.unheld,
      close: () => Promise.resolve(),
    },
  }
}
