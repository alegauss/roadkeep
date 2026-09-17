import { randomUUID } from 'node:crypto'

import {
  actionableReport,
  claimingBrief,
  doorsIn,
  findingAt,
  handoverOf,
  lineOf,
  mayHandOver,
  openingUnreadable,
  openOver,
  promptFor,
  promptForDoor,
  readLintPayload,
  resumeCall,
  sessionCall,
  MOVES_QUIET_MS,
  sessionMoves,
  type Agent,
  type AgentResolution,
  type BriefAnswer,
  type BriefPayload,
  type Handed,
  type HandedOver,
  type ReadOutcome,
  type Clock,
  type SessionCall,
  type SessionMoves,
  type SessionOutcome,
  type SessionRecord,
  type TopicEvents,
} from '@rk/core'

import type { Carrier } from './carrier'
import { REAL_CLOCK } from './governed-watch'
import { startSession, type RunningSession, type SessionWatcher } from './session-process'
import { watchSessionRoot, type OnMoved, type SessionWatch } from './session-watch'

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
  /** `doors` among them since RG263: a session about a finding reads the batch a door names. */
  readonly carrier: Pick<Carrier, 'open' | 'run' | 'doors'>
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
  /** The time a session is spawned at (RG244). The clock unless a test says otherwise. */
  readonly now?: () => Date
  /**
   * The folder names the walk skips, as the settings spell them (RG247): what moved under one
   * of those is not this session's work. Nothing skipped unless the caller says so.
   */
  readonly skip?: () => readonly string[]
  /** Watch a session's root while it runs (RG247). `watchSessionRoot` unless a test says otherwise. */
  readonly watch?: (root: string, moved: OnMoved) => SessionWatch
  /** How a burst of moves is held before it is published. `REAL_CLOCK` unless a test drives it. */
  readonly clock?: Clock
}

export interface Sessions {
  handOver(root: string, id: string): Promise<HandedOver>
  /** Start one on a gate finding rather than a line (RG263), named by the door that closes it. */
  handOverDoor(root: string, offered: string, which: number): Promise<HandedOver>
  /** Answer one that stopped, by continuing it under the same key (RG269). */
  reply(key: string, text: string): Promise<HandedOver>
  /** Every session started, each with its lines so far. Copies, so nothing outside edits one. */
  list(): SessionRecord[]
  /**
   * The root a session was started in, or null for a key that names none (RG244): what a
   * question about its files is answered under, so the root is never a page's word.
   */
  rootOf(key: string): string | null
  /** Stop one. Nothing happens for a key that names no running session. */
  stop(key: string): void
  /** Stop every session still running, awaited to the last exit. What quitting waits on. */
  close(): Promise<void>
}

interface Held {
  readonly key: string
  readonly root: string
  readonly id: string
  readonly started: string
  readonly handed: Handed
  readonly agent: Agent
  readonly lines: string[]
  /** What has moved on disk under the root since it was spawned (RG247). */
  readonly moves: SessionMoves
  /** The recursive watch behind those moves, given back when the session ends. */
  watching: SessionWatch | null
  /** How to call off a held burst, so a formatter touching two hundred files is told once. */
  holding: (() => void) | null
  outcome: SessionOutcome | null
  running: RunningSession | null
}

/** Why a reply resumes nothing (RG269), each said in the words a person would act on. */
const NO_SESSION = 'this window holds no session by that key'
const NO_REPLY = 'a reply has to say something'
const STILL_RUNNING = 'the session is still running, and a reply waits for it to stop'
const NEVER_NAMED = 'the session never named itself, so there is nothing to resume'

/** Why a door names no session: the batch is gone, or nothing in the report offered it. */
const NO_SUCH_DOOR = 'that door is no longer on offer: the governed files have moved since'
const NO_FINDING = 'that door belongs to no finding this report names'

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
    started: held.started,
    handed: held.handed,
    agent: held.agent,
    lines: [...held.lines],
    moved: held.moves.paths,
    movedBeyond: held.moves.beyond,
    outcome: held.outcome,
  }
}

export function createSessions(options: SessionsOptions): Sessions {
  const start = options.start ?? startSession
  const environment = options.environment ?? (() => Promise.resolve(process.env))
  const named = options.key ?? randomUUID
  const now = options.now ?? (() => new Date())
  const skip = options.skip ?? (() => [])
  const watching = options.watch ?? ((root, moved) => watchSessionRoot(root, moved))
  const clock = options.clock ?? REAL_CLOCK
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
    handed: Handed,
    found: Agent,
    inherits: NodeJS.ProcessEnv,
  ): Held => {
    const [command = ''] = found.command
    // Each shape frames its own payload (RG263), and neither is rewritten on the way in.
    const prompt =
      handed.kind === 'line' ? promptFor(handed.brief) : promptForDoor(handed.finding, handed.argv)
    const call = sessionCall(command, root, prompt)
    const session: Held = {
      key: named(),
      root,
      id,
      // Taken as the process is started, so a file the disk changed before it reads as unchanged.
      started: now().toISOString(),
      handed,
      agent: found,
      lines: [],
      moves: sessionMoves(skip()),
      watching: null,
      holding: null,
      outcome: null,
      running: null,
    }
    held.set(session.key, session)
    run(session, call, found, inherits)
    return session
  }

  /**
   * Spawn one turn of a held session, and keep what it says on the record (RG269).
   *
   * The first turn and every reply go through here, so a continued session is the same session:
   * its lines are appended where the last turn left them, its root is watched again, and the
   * outcome it ends with replaces the one it had.
   */
  const run = (session: Held, call: SessionCall, found: Agent, inherits: NodeJS.ProcessEnv) => {
    const [, ...prefix] = found.command
    // What the stream cannot name (RG247): a formatter or a generator run through Bash. Watched
    // from the spawn, given back at the outcome, and told in bursts rather than per event.
    const tell = () => {
      session.holding = null
      options.publish({
        session: session.key,
        moved: session.moves.paths,
        beyond: session.moves.beyond,
      })
    }
    session.watching = watching(session.root, (path, at) => {
      session.moves.moved(path, at)
      session.holding?.()
      session.holding = clock.after(MOVES_QUIET_MS, tell)
    })

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
      // The watch goes with the process, and what it saw is told once more before the ending:
      // a screen that hears the outcome has the whole list beside it.
      session.watching?.stop()
      session.watching = null
      session.holding?.()
      tell()
      options.publish({ session: session.key, outcome })
    })
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
        session: recordOf(
          begin(root, id, { kind: 'line', brief: took.payload }, found.agent, inherits),
        ),
      }
    },

    async reply(key, text) {
      const session = held.get(key)
      if (session === undefined) return { kind: 'withheld', reason: NO_SESSION }
      if (text.trim() === '') return { kind: 'withheld', reason: NO_REPLY }
      if (session.outcome === null) return { kind: 'withheld', reason: STILL_RUNNING }
      const sessionId = session.outcome.sessionId
      if (sessionId === '') return { kind: 'withheld', reason: NEVER_NAMED }

      // The line is read again before anything resumes (RG269): somebody may have taken it while
      // the session sat stopped, and a reply is not the moment to start a second author on it.
      // A session handed a finding has no line, and nothing of the kind to check.
      if (session.handed.kind === 'line') {
        const reached = await openOver(options.carrier, session.root)
        if (reached.kind !== 'open') {
          return { kind: 'withheld', reason: openingUnreadable(reached).message }
        }
        const read = briefed(
          await reached.project.client.call(session.root, 'brief', { id: session.id }),
          session.id,
        )
        if ('said' in read) return { kind: 'refused', said: read.said }
        const standing = handoverOf(read.payload)
        if (standing.held.length > 0) return { kind: 'held', held: standing.held }
      }

      const found = await resolved(session.root)
      if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
      env ??= environment(found.agent, session.root)
      const inherits = await env

      const [command = ''] = found.agent.command
      // The outcome goes before the process starts, and every window watching is told: what it
      // holds is over, and the lines that follow are a turn still going.
      session.outcome = null
      options.publish({ session: session.key, resumed: true })
      run(session, resumeCall(command, session.root, sessionId, text), found.agent, inherits)
      return { kind: 'started', session: recordOf(session) }
    },

    async handOverDoor(root, offered, which) {
      // The door first, because `taken` is what checks the batch against the files: a finding
      // read out of an answer the tree has moved under is one nobody should be started on.
      const door = await options.carrier.doors.taken(root, offered, which)
      if (door === null) return { kind: 'withheld', reason: NO_SUCH_DOOR }

      const answer = options.carrier.doors.answered(root, offered)
      const read = readLintPayload(answer, '')
      // The batch is every door the answer carried; this report covers the findings' own. A
      // door from a note or an `explain` names no finding, and a session started on a command
      // line with nothing to say about it is worse than no session.
      const finding = read.ok
        ? findingAt(actionableReport(read.value), doorsIn(answer), which)
        : null
      if (finding === null) return { kind: 'withheld', reason: NO_FINDING }

      const found = await resolved(root)
      if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
      env ??= environment(found.agent, root)
      const inherits = await env

      return {
        kind: 'started',
        // No id: a finding is not a line, and an empty one is what says so to a screen.
        session: recordOf(
          begin(root, '', { kind: 'finding', finding, argv: door.argv }, found.agent, inherits),
        ),
      }
    },

    list() {
      return [...held.values()].map(recordOf)
    },

    rootOf(key) {
      return held.get(key)?.root ?? null
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
