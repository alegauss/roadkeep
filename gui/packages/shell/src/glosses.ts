import {
  GLOSS_SCHEMA,
  lineOf,
  openingUnreadable,
  openOver,
  promptForGloss,
  readGloss,
  type Agent,
  type AgentResolution,
  type BriefAnswer,
  type BriefPayload,
  type GlossAnswer,
  type ReadOutcome,
} from '@rk/core'

import type { Carrier } from './carrier'

import { askGloss, type GlossCall, type GlossRun } from './gloss-process'

/**
 * What a task means, asked of Claude Code and answered once (RG284).
 *
 * **The renderer names a line, never a prompt.** The id is briefed here, through the same
 * carrier a window reads with, and `promptForGloss` frames that payload — the hand-over's rule
 * (RG153), for the same reason: a page that could put words to an agent would be a page that
 * could ask it anything.
 *
 * **One at a time per line.** A second ask for a line already being glossed joins the first
 * rather than starting a second process, and a reader who gives up cancels the one run. Nothing
 * is kept once it answers: a gloss is a read, and what a screen does with it is the screen's.
 *
 * The run itself is `gloss-process`, which is where no-tool, no-server, nothing-kept lives.
 */

export interface GlossesOptions {
  /** How lines are read: through the carrier, as a window reads them. */
  readonly carrier: Pick<Carrier, 'open' | 'run'>
  /** Which Claude Code answers here, asked from a project's root — the session's resolution. */
  readonly agent: (root: string) => Promise<AgentResolution>
  /** The environment it runs in (RG205). The one this process inherited unless a caller says. */
  readonly environment?: (agent: Agent, root: string) => Promise<NodeJS.ProcessEnv>
  /**
   * The language every string comes back in.
   *
   * Main's, never the renderer's: the window's language is already resolved on this side
   * (`localeChoice` over the settings and the desktop), so a page does not send one.
   */
  readonly tag: () => string
  /** Start the query. `askGloss` unless a test says otherwise. */
  readonly ask?: (call: GlossCall, env: NodeJS.ProcessEnv) => GlossRun
}

export interface Glosses {
  /** Ask what one line means. The answer is the gloss, or why there is none. */
  gloss(root: string, id: string): Promise<GlossAnswer>
  /** Give up on one that is running. A line nothing is running for does nothing. */
  cancel(root: string, id: string): void
  /** Give up on every one still running, which is what quitting does. */
  close(): void
}

/** One line's brief, or the sentence the engine refused with. */
function briefed(
  outcome: ReadOutcome<BriefAnswer>,
  id: string,
): { readonly payload: BriefPayload } | { readonly said: string } {
  if (outcome.kind === 'refused') return { said: outcome.refusal.said }
  if (outcome.kind === 'unreadable') return { said: outcome.unreadable.message }
  const line = lineOf(outcome.value)
  if (line === null) return { said: 'empty' in outcome.value ? outcome.value.reason : '' }
  if (line.id !== id) return { said: `brief answered ${line.id} when ${id} was asked for` }
  return { payload: line }
}

export function createGlosses(options: GlossesOptions): Glosses {
  const ask = options.ask ?? askGloss
  const environment = options.environment ?? (() => Promise.resolve(process.env))
  /** What is running, by the line it is about: the run to cancel and the answer to share. */
  const running = new Map<
    string,
    { readonly run: GlossRun; readonly answer: Promise<GlossAnswer> }
  >()

  const answer = async (root: string, id: string): Promise<GlossAnswer> => {
    const reached = await openOver(options.carrier, root)
    if (reached.kind !== 'open') {
      return { kind: 'withheld', reason: openingUnreadable(reached).message }
    }
    const read = briefed(await reached.project.client.call(root, 'brief', { id }), id)
    if ('said' in read) return { kind: 'withheld', reason: read.said }

    const found = await options.agent(root)
    if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
    const agent = found.agent
    const env = await environment(found.agent, root)
    const [command = '', ...prefix] = agent.command

    const run = ask(
      {
        command,
        prefix,
        cwd: root,
        prompt: promptForGloss(read.payload, options.tag()),
        schema: GLOSS_SCHEMA,
      },
      env,
    )
    const key = `${root}\u0000${id}`
    const answered = run.answered.then((said): GlossAnswer => {
      if (said.kind === 'cancelled') return { kind: 'cancelled' }
      // The command resolved and then would not start, which is the same answer to a reader:
      // no Claude Code ran. What was tried is the one command that was.
      if (said.kind === 'unavailable') return { kind: 'unavailable', tried: [agent.command] }
      if (said.kind === 'failed') return { kind: 'failed', said: said.said }
      return {
        kind: 'said',
        gloss: readGloss(said.structured, read.payload),
        model: said.model,
        version: said.version,
      }
    })
    running.set(key, { run, answer: answered })
    try {
      return await answered
    } finally {
      running.delete(key)
    }
  }

  return {
    gloss(root, id) {
      // A positional starting with a dash is an option to any parser, as `handOver` says.
      if (id === '' || id.startsWith('-')) {
        return Promise.resolve({ kind: 'withheld', reason: `\`${id}\` is not a line id` })
      }
      // The same question twice is one run: a screen asking again while it waits is waiting.
      const already = running.get(`${root}\u0000${id}`)
      return already?.answer ?? answer(root, id)
    },

    cancel(root, id) {
      running.get(`${root}\u0000${id}`)?.run.cancel()
    },

    close() {
      for (const one of running.values()) one.run.cancel()
      running.clear()
    },
  }
}
