import { randomUUID } from 'node:crypto'

import {
  claimingBrief,
  handoverOf,
  lineOf,
  mayHandOver,
  openingUnreadable,
  openOver,
  promptFor,
  sessionCall,
  type Agent,
  type AgentResolution,
  type BriefAnswer,
  type BriefPayload,
  type HandedOver,
  type ReadOutcome,
  type SessionCall,
  type SessionOutcome,
  type SessionRecord,
  type TopicEvents,
} from '@rk/core'

import type { Carrier } from './carrier'
import { startSession, type RunningSession, type SessionWatcher } from './session-process'

/**
 * The sessions a window started, held by the process that can stop them (RG153).
 *
 * **The line is taken here, from a brief read here.** A window names a root and an id and
 * nothing else: this reads the line through the carrier the way the window would, names the
 * holder of a held line and stops, and otherwise takes it with `brief --claim` and starts the
 * session from that payload through `promptFor`. The prompt is never a page's word, which is
 * what keeps a renderer from starting an agent with a prompt of its own.
 *
 * **Nothing is taken that cannot be started.** Which Claude Code this machine has is asked
 * before the claim, so a machine with none answers that and leaves the line as it was. The
 * environment the session runs in is decided there too (RG205), once, beside the agent.
 *
 * Every line the session writes is kept and published with its place in the stream, and its
 * outcome is published when it ends, so a screen that opens late asks for what it missed and
 * hears the rest. Stopping kills the process and leaves the claim to the registry's expiry: the
 * session may have moved the line, and releasing it would undo a state nobody reviewed.
 *
 * Nothing here names Electron, so a test drives it with a fake carrier and a fake process.
 */

export interface SessionsOptions {
  /** How lines are read: through the carrier, as a window reads them. */
  readonly carrier: Pick<Carrier, 'open' | 'run'>
  /** Which Claude Code answers here, asked from a project's root. */
  readonly agent: (root: string) => Promise<AgentResolution>
  /**
   * The environment that agent's sessions run in (RG205), asked once it resolved. The one
   * this process inherited unless the caller says otherwise.
   */
  readonly environment?: (agent: Agent, root: string) => Promise<NodeJS.ProcessEnv>
  /** Where each line and each ending goes: the `session` topic, keyed on the session. */
  readonly publish: (event: TopicEvents['session']) => void
  /** Start the process. `startSession` unless a test says otherwise. */
  readonly start?: (
    call: SessionCall,
    watcher: SessionWatcher,
    env: NodeJS.ProcessEnv,
  ) => RunningSession
  /** Name a new session. A random UUID unless a test says otherwise. */
  readonly key?: () => string
}

export interface Sessions {
  handOver(root: string, id: string): Promise<HandedOver>
  /** Every session started, each with its lines so far. Copies, so nothing outside edits one. */
  list(): SessionRecord[]
  /** Stop one. Nothing happens for a key that names no running session. */
  stop(key: string): void
  /** Stop every session still running, awaited to the last exit. What quitting waits on. */
  close(): Promise<void>
}

interface Held {
  readonly key: string
  readonly root: string
  readonly id: string
  readonly handed: BriefPayload
  readonly agent: Agent
  readonly lines: string[]
  outcome: SessionOutcome | null
  running: RunningSession | null
}

/** The line a brief answered for this id, or the sentence the engine said instead. */
function briefed(
  outcome: ReadOutcome<BriefAnswer>,
  id: string,
): { readonly payload: BriefPayload } | { readonly said: string } {
  if (outcome.kind === 'refused') return { said: outcome.refusal.said }
  if (outcome.kind === 'unreadable') return { said: outcome.unreadable.message }
  const line = lineOf(outcome.value)
  if (line === null) return { said: 'empty' in outcome.value ? outcome.value.reason : '' }
  // A brief naming an id answers that line; one that answered another took the wrong line.
  if (line.id !== id) return { said: `brief answered ${line.id} when ${id} was asked for` }
  return { payload: line }
}

function recordOf(held: Held): SessionRecord {
  return {
    key: held.key,
    root: held.root,
    id: held.id,
    handed: held.handed,
    agent: held.agent,
    lines: [...held.lines],
    outcome: held.outcome,
  }
}

export function createSessions(options: SessionsOptions): Sessions {
  const start = options.start ?? startSession
  const environment = options.environment ?? (() => Promise.resolve(process.env))
  const named = options.key ?? randomUUID
  const held = new Map<string, Held>()
  // Kept once found: which Claude Code a machine has does not change under a running app. A
  // machine that had none is asked again, since installing one is what somebody does next.
  let agent: Promise<AgentResolution> | null = null
  // Kept for the same reason, and asked only of an agent that resolved — which is also kept,
  // so the two never belong to different installations.
  let env: Promise<NodeJS.ProcessEnv> | null = null

  const resolved = async (root: string): Promise<AgentResolution> => {
    agent ??= options.agent(root)
    const answer = await agent
    if (answer.kind !== 'resolved') agent = null
    return answer
  }

  const begin = (
    root: string,
    id: string,
    handed: BriefPayload,
    found: Agent,
    inherits: NodeJS.ProcessEnv,
  ): Held => {
    const [command = '', ...prefix] = found.command
    const call = sessionCall(command, root, promptFor(handed))
    const session: Held = {
      key: named(),
      root,
      id,
      handed,
      agent: found,
      lines: [],
      outcome: null,
      running: null,
    }
    held.set(session.key, session)

    session.running = start(
      { ...call, argv: [...prefix, ...call.argv] },
      {
        onLine: (line) => {
          session.lines.push(line)
          options.publish({ session: session.key, index: session.lines.length - 1, line })
        },
      },
      inherits,
    )
    void session.running.finished.then((outcome) => {
      session.outcome = outcome
      options.publish({ session: session.key, outcome })
    })
    return session
  }

  return {
    async handOver(root, id) {
      // A positional that starts with a dash is an option to any parser, and `brief` takes
      // `--designed` as one: the claim would land on whichever line the pick chose.
      if (id === '' || id.startsWith('-')) {
        return { kind: 'withheld', reason: `\`${id}\` is not a line id` }
      }
      const reached = await openOver(options.carrier, root)
      if (reached.kind !== 'open') {
        return { kind: 'withheld', reason: openingUnreadable(reached).message }
      }
      const { client } = reached.project

      const read = briefed(await client.call(root, 'brief', { id }), id)
      if ('said' in read) return { kind: 'refused', said: read.said }
      const before = handoverOf(read.payload)
      if (before.held.length > 0) return { kind: 'held', held: before.held }
      if (!mayHandOver(before)) return { kind: 'unready', readiness: before.readiness }

      const found = await resolved(root)
      if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
      env ??= environment(found.agent, root)
      const inherits = await env

      const took = briefed(await client.call(root, 'brief', claimingBrief(id)), id)
      if ('said' in took) return { kind: 'refused', said: took.said }
      return {
        kind: 'started',
        session: recordOf(begin(root, id, took.payload, found.agent, inherits)),
      }
    },

    list() {
      return [...held.values()].map(recordOf)
    },

    stop(key) {
      const session = held.get(key)
      if (session?.outcome === null) session.running?.cancel()
    },

    async close() {
      const running = [...held.values()].filter((session) => session.outcome === null)
      for (const session of running) session.running?.cancel()
      await Promise.all(
        running.flatMap((session) => (session.running === null ? [] : [session.running.finished])),
      )
    },
  }
}
