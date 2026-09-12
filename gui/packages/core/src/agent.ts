import { asRecord } from './reading'
import type { CancelSignal, Transport } from './transport'

/**
 * The other command this app runs.
 *
 * This app resolves a roadkeep engine per project and says what it found; without this it
 * does none of that for the command that runs a session. So: resolve once, record which
 * binary and which version answered, and show a machine without one as a stated condition
 * rather than a failure at the moment work starts.
 *
 * The shape is `resolveEngine`'s deliberately — candidates in order, each tried, and an
 * unresolved answer carrying the reason and everything looked for. A screen can then say
 * what it looked for and where, which is the difference between *no Claude Code here* and
 * a spawn that failed with a number.
 *
 * **The version is read from prose**, because there is no other form: `claude --version`
 * prints one line and takes no `--json`. So the whole line is kept and a dotted version is
 * lifted out where one is there — a version this app could not parse loses a label and
 * never the binary.
 *
 * **Nothing is bundled and nothing is guessed.** The session runs the person's own
 * installation, with their own authentication and their own settings; an app shipping a
 * `claude` of its own would be signing somebody else's work in with an account they did
 * not choose.
 */

/** Choosing a candidate is choosing a transport, exactly as it is for an engine. */
export type TransportFor = (command: readonly string[]) => Transport

export interface Agent {
  /** The command every session for this machine is started with. */
  readonly command: readonly string[]
  /** The dotted version, or the empty string where the line held none. */
  readonly version: string
  /** What `--version` printed, whole. The fallback when the version could not be lifted. */
  readonly said: string
}

export type AgentResolution =
  | { readonly kind: 'resolved'; readonly agent: Agent }
  | {
      readonly kind: 'unresolved'
      /** Sentence-shaped and meant to be shown: a blank answer is not a condition. */
      readonly reason: string
      /** Every command tried, so the reason names what was looked for. */
      readonly tried: readonly (readonly string[])[]
    }

export interface ResolveAgentOptions {
  readonly timeoutMs?: number
  readonly signal?: CancelSignal
}

/**
 * The version out of the line, or the empty string.
 *
 * A dotted number is what is looked for and nothing else is assumed about the sentence
 * around it — `2.1.263 (Claude Code)` today, and whatever it becomes later still resolves
 * because the whole line is kept beside this.
 */
export function versionIn(said: string): string {
  return /\b\d+\.\d+\.\d+\S*/.exec(said)?.[0] ?? ''
}

/** Ask one candidate. `null` means it is not the agent, which is not an error here. */
async function ask(
  transportFor: TransportFor,
  root: string,
  command: readonly string[],
  options: ResolveAgentOptions,
): Promise<string | null> {
  try {
    const result = await transportFor(command).run({
      root,
      argv: ['--version'],
      ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
      ...(options.signal === undefined ? {} : { signal: options.signal }),
    })
    // Answering at all is what resolves it. A non-zero exit is a command that is not this
    // one, and the next candidate gets its turn.
    return result.code === 0 ? result.stdout.trim() : null
  } catch {
    // Unspawnable, timed out or cancelled — all of them "not the agent" here.
    return null
  }
}

/**
 * Resolve the command that runs a session.
 *
 * @param candidates commands to try, in order, each already argv. Discovering them needs a
 *   filesystem, so it belongs to whoever has one; this only asks.
 */
export async function resolveAgent(
  transportFor: TransportFor,
  root: string,
  candidates: readonly (readonly string[])[],
  options: ResolveAgentOptions = {},
): Promise<AgentResolution> {
  const tried: (readonly string[])[] = []

  for (const candidate of candidates) {
    tried.push(candidate)
    const said = await ask(transportFor, root, candidate, options)
    if (said === null) continue
    return {
      kind: 'resolved',
      agent: { command: candidate, version: versionIn(said), said },
    }
  }

  return {
    kind: 'unresolved',
    reason:
      tried.length === 0
        ? 'nothing was offered to try, so no session can be started here'
        : `no Claude Code answered on this machine: tried ${tried
            .map((command) => command.join(' '))
            .join(', ')}`,
    tried,
  }
}

/**
 * Whether `claude auth status` says a credential answers (RG205).
 *
 * Read off the JSON and not the exit code: `loggedIn` is the field the command states, and
 * anything short of a literal `true` is no login — a build without the subcommand, a line
 * that is not JSON, a `"true"` somebody quoted. Answering no there costs nothing, since the
 * caller keeps the environment it had and the session runs as it always did.
 */
export function loggedIn(said: string): boolean {
  let source: unknown
  try {
    source = JSON.parse(said.trim())
  } catch {
    return false
  }
  return asRecord(source)?.['loggedIn'] === true
}

/**
 * What was found, for a screen to state before anybody asks for a session.
 *
 * A stated condition and not an error: a machine without Claude Code is a machine where
 * this app reads a backlog and does not hand work to an agent, which is a thing somebody
 * should be told once rather than discover at the moment work starts.
 */
export function saidOfAgent(resolution: AgentResolution): string {
  if (resolution.kind === 'unresolved') return resolution.reason
  const { command, version } = resolution.agent
  const named = version === '' ? resolution.agent.said : version
  return `${command.join(' ')} — ${named}`
}
