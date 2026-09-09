import path from 'node:path'

import {
  createClient,
  explainFailure,
  type Client,
  type Transport,
  type VerbAnswers,
  type VerbInputs,
  type VerbName,
} from '@rk/core'

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
 * the one that wastes an afternoon. `explainFailure` composes that sentence and this is
 * where it is reached for.
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
 */
export const liveEngine: Transport = createProcessTransport({
  command: 'python',
  prefixArgs: [LAUNCHER],
})

/** The client over it, reading each verb with the shape that verb declares. */
export const liveClient: Client = createClient(liveEngine)

export interface ReadOptions {
  /** A client of this file's own, where the transport under test is not the ordinary one. */
  readonly client?: Client
  readonly timeoutMs?: number
  /**
   * The build that answered, for the sentence a failure prints.
   *
   * Empty says so rather than guessing — `explainFailure` writes "of an unknown version",
   * which is true and still tells a reader that this app is behind something. A file that
   * has resolved the engine passes what it found.
   */
  readonly engineVersion?: string
}

/**
 * Read one verb's payload, or fail with the sentence a person would need.
 *
 * Three outcomes collapse to two here, which is what a test wants: the payload, or a throw.
 * A refusal is named as a refusal and quotes what the engine said, because a test that
 * asked for an answer and got a refusal has learnt something different from one whose shape
 * did not parse. A file asserting the refusal itself calls the client directly — that is an
 * answer it wanted, not a failure.
 */
export async function read<K extends VerbName>(
  root: string,
  verb: K,
  input: VerbInputs[K],
  over: ReadOptions = {},
): Promise<VerbAnswers[K]> {
  const client = over.client ?? liveClient
  const answer = await client.call(root, verb, input, { timeoutMs: over.timeoutMs ?? CEILING })

  if (!answer.ok) {
    throw new Error(
      explainFailure(answer.failure, { verb, engineVersion: over.engineVersion ?? '' }),
    )
  }
  if (answer.value.kind === 'refused') {
    throw new Error(`\`${verb}\` was refused: ${answer.value.refusal.said}`)
  }
  return answer.value.value
}
