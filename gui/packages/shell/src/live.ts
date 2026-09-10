import path from 'node:path'

import {
  createClient,
  explainUnreadable,
  type Client,
  type Transport,
  type VerbAnswers,
  type VerbInputs,
  type VerbName,
} from '@rk/core'

import { createMcpTransport, type McpTransport } from './mcp-transport'
import { createProcessTransport } from './process-transport'

/**
 * The seam a live test opens on: this repository, the engine that answers for it, and one
 * way to read a verb.
 *
 * Every file in the live suite began the same four lines — resolve the root, join the
 * launcher, redeclare the timeout, build a transport — and then unwrapped each call by
 * hand: `if (!answer.ok) throw`, `if (answer.value.kind === 'refused') throw`, and the
 * payload two properties down. RG66 had already moved the reader into the verb, so what
 * was left at each site was the throwing, and that is the half that had drifted: the
 * sentence a moved key printed was different in every file, some naming the path and the
 * expected type, some saying `list did not read`, one saying nothing at all.
 *
 * **The message is why this is one place and not thirty.** A shape that moved upstream has
 * to name the key and the build that moved it, and a copy that quietly says `undefined` is
 * the one that wastes an afternoon. Since RG99 the client carries the half about the key
 * and `explainUnreadable` adds the half about the build; this is where it is reached for.
 *
 * **The assertions are not here.** What a file asserts is its own; what it opens on is
 * this. A file that needs a transport of its own — one that counts calls, one that caches,
 * one that points at a missing engine — still builds it, and passes the client it made.
 */

/** This repository, which is the governed project most of the live suite reads. */
export const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/**
 * The wired launcher.
 *
 * How a project says which copy of roadkeep answers for it, and the reason the suite does
 * not run `roadkeep` off PATH: a checkout under development is the one under test.
 */
export const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')

/** Per call: an interpreter start plus a read, with room for a cold import. */
export const CEILING = 60000

/**
 * The engine every ordinary live file spawns, built once per worker process.
 *
 * Shared on purpose. A transport holds no state between calls — it spawns per call, which
 * is what RG101 is about — so one per file bought nothing, and the fixture builder wants a
 * transport before a client exists anyway.
 *
 * **Still the one that spawns, and on purpose** (RG130). The fixture builder writes, the
 * tool surface withholds writes, and a file that compares a transport against the process
 * — `mcp-live`, `seam-live`, the ceilings — is asserting something about a spawn. Every
 * one of those reads this, so it did not move.
 */
export const liveEngine: Transport = createProcessTransport({
  command: 'python',
  prefixArgs: [LAUNCHER],
})

/**
 * The same engine held, one `roadkeep mcp` per root, for the suite's reads (RG130).
 *
 * Measured before it existed: of 579 engine calls across the live gate, 376 were reads and
 * took 283 of the run's 433 seconds — at about 770ms each, which is an interpreter start
 * and very little else. The app has read this way since RG122. A read the surface cannot
 * express falls through to `liveEngine`, which is the fallback, so `stats`, `commands` and
 * a claiming `brief` spawn exactly as they did.
 *
 * **What it holds, something has to give back.** A fixture's `dispose` releases its root
 * before removing the directory — Windows will not remove one a server is standing in —
 * and `live-setup.ts` closes whatever is left when a file ends, which is this repository's
 * own root and nothing else.
 */
export const liveHeld: McpTransport = createMcpTransport({
  engine: ['python', LAUNCHER],
  fallback: liveEngine,
  timeoutMs: CEILING,
})

/** The client over it, reading each verb with the shape that verb declares. */
export const liveClient: Client = createClient(liveHeld)

/**
 * The engine, read once and named for the length of the run (RG84).
 *
 * Thirty-one files call this engine and none of them ever asked what it was. Where it is a
 * working checkout somebody is editing — which here it always is — each call is a fresh
 * reading of a moving program, and the suite went red four times in one afternoon with
 * nothing in this repository changed: a package mid-save does not import, the launcher
 * falls back to a cached build, and what comes back is a payload this app cannot read. That
 * failure is indistinguishable from the one the contract test exists to produce, and a
 * reader who learns red can also mean "somebody hit save elsewhere" stops believing it.
 *
 * So the engine is asked what it is **once per run**, and every file spends that one
 * answer. It cannot make the suite immune to an engine being rebuilt underneath it, and
 * should not: what it does is make the breakage arrive once, at the start, saying which
 * revision answered — instead of thirty-one files each reporting a renamed key.
 *
 * **Named and not discovered.** This asks the launcher this repository commits, which is
 * the engine the suite already calls, rather than resolving candidates: `resolveEngine` is
 * how the *app* picks a copy for a project it was handed, and a suite that discovered its
 * own engine could go green against a `roadkeep` on PATH that governs nothing here.
 *
 * The answer travels to the workers as an environment variable because that is what crosses
 * a fork — the same reason `fixture-cache.ts` gives. Absent, a worker asks for itself, which
 * is one interpreter start and the behaviour this replaces.
 */

/** Where the run's one reading is published, for the workers it forks. */
export const ENGINE_VAR = 'RK_LIVE_ENGINE'

export interface EngineReading {
  /** `0.2.426 (984c5b9a)`, or the empty string where nothing answered. */
  readonly named: string
  /** Why nothing answered, sentence-shaped, or the empty string where one did. */
  readonly unresolved: string
}

/** Ask the engine what it is. The one call this suite makes that is not about a project. */
async function askTheEngine(): Promise<EngineReading> {
  // No `try`: since RG99 the client answers `unreadable` where the call never happened,
  // which is what no python and a launcher that cannot import both look like.
  //
  // Spawned and not held (RG130). This runs once, in the process that forks the workers,
  // and a server started here would stand in this repository for the length of the run
  // with nothing placed to close it — for a read that is asked exactly once.
  const spawned = createClient(liveEngine)
  const answer = await spawned.call(REPO, 'engines', {}, { timeoutMs: CEILING })
  if (answer.kind === 'unreadable') {
    return { named: '', unresolved: answer.unreadable.message }
  }
  if (answer.kind === 'refused') {
    return { named: '', unresolved: `it refused \`engines\`: ${answer.refusal.said}` }
  }

  const { version, revision } = answer.value.writing
  return { named: revision === '' ? version : `${version} (${revision})`, unresolved: '' }
}

let held: Promise<EngineReading> | undefined

/** What the engine said it was, asked once and remembered for the rest of this process. */
export function engineReading(): Promise<EngineReading> {
  held ??= (async (): Promise<EngineReading> => {
    const published = process.env[ENGINE_VAR]
    return published === undefined ? askTheEngine() : (JSON.parse(published) as EngineReading)
  })()
  return held
}

/** Vitest's `globalSetup` for the live project: ask once, before any worker starts. */
export async function setup(): Promise<void> {
  process.env[ENGINE_VAR] = JSON.stringify(await askTheEngine())
}

export function teardown(): void {
  delete process.env[ENGINE_VAR]
}

export interface ReadOptions {
  /** A client of this file's own, where the transport under test is not the ordinary one. */
  readonly client?: Client
  readonly timeoutMs?: number
}

/**
 * Read one verb's payload, or fail with the sentence a person would need.
 *
 * Three outcomes collapse to two here, which is what a test wants: the payload, or a throw.
 * A refusal is named as a refusal and quotes what the engine said, because a test that
 * asked for an answer and got a refusal has learnt something different from one whose shape
 * did not parse. A file asserting the refusal itself calls the client directly — that is an
 * answer it wanted, not a failure.
 *
 * **Four outcomes, really**, and the fourth is why the reading is consulted before the call
 * rather than only in the message: an engine that answered nothing at the start of the run
 * is going to answer nothing here either, and saying so is worth more than the renamed-key
 * report a read against a fallen-back build produces. There is no way to override the
 * name — one reading is the point, and a second would be the disagreement this removes.
 */
export async function read<K extends VerbName>(
  root: string,
  verb: K,
  input: VerbInputs[K],
  over: ReadOptions = {},
): Promise<VerbAnswers[K]> {
  const client = over.client ?? liveClient
  const reading = await engineReading()
  if (reading.unresolved !== '' && over.client === undefined) {
    // The shared engine only. A file that built a transport of its own is asking about that
    // one, and this repository's launcher has nothing to say about whether it answers.
    throw new Error(
      'The engine this suite runs against did not answer `engines` at the start of the run, ' +
        `so nothing here is a claim about a build anybody can name: ${reading.unresolved}`,
    )
  }

  const answer = await client.call(root, verb, input, { timeoutMs: over.timeoutMs ?? CEILING })

  if (answer.kind === 'unreadable') {
    // One composer for the sentence, in `core` beside the state it explains: the build is
    // named because the usual cause is this app being behind the engine, and saying which
    // one answered is what saves the afternoon.
    throw new Error(explainUnreadable(answer.unreadable, { verb, engineVersion: reading.named }))
  }
  if (answer.kind === 'refused') {
    throw new Error(`\`${verb}\` was refused: ${answer.refusal.said}`)
  }
  return answer.value
}
