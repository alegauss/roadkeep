import {
  GLOSS_SCHEMA,
  GLOSS_SHAPE,
  glossedLine,
  glossFor,
  glossShapeStands,
  glossStands,
  lineOf,
  NOTHING_GLOSSED,
  withGloss,
  openingUnreadable,
  openOver,
  promptForGloss,
  readGloss,
  type Agent,
  type AgentResolution,
  type BriefAnswer,
  type BriefPayload,
  type GlossAnswer,
  type KeptGlosses,
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
 * rather than starting a second process, and a reader who gives up cancels the one run. What was
 * answered is kept (RG287), and a line kept in this language answers without a process at all.
 *
 * **What it is doing, while it does it** (RG297): each line of the run's stream is passed on as
 * it passes, so a window can draw the run as a session is drawn. Nothing of it is kept.
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
  /** What this machine has kept (RG287). Nothing kept unless a caller holds a file. */
  readonly kept?: () => KeptGlosses
  /** Keep what was just answered. Nothing is kept unless a caller writes it somewhere. */
  readonly keep?: (glosses: KeptGlosses) => void
  /** When a gloss was answered, which is what the bound reads. The clock unless a test drives it. */
  readonly now?: () => Date
  /**
   * Tell whoever is watching that project each line of the run's stream (RG297), with its place.
   *
   * Nothing is kept of it: a line is passed on as it happens and forgotten. A window that opened
   * the dialog after a run started hears the rest of them, which is what progress is.
   */
  readonly line?: (root: string, id: string, index: number, line: string) => void
}

export interface Glosses {
  /**
   * Ask what one line means, or hand back what was kept for it (RG287).
   *
   * @param again ask anew and replace what was kept, whatever is kept for the line
   */
  gloss(root: string, id: string, again?: boolean): Promise<GlossAnswer>
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
  const kept = options.kept ?? (() => NOTHING_GLOSSED)
  const keep = options.keep ?? (() => undefined)
  const now = options.now ?? (() => new Date())
  /** What is running, by the line it is about: the run to cancel and the answer to share. */
  const running = new Map<
    string,
    { readonly run: GlossRun; readonly answer: Promise<GlossAnswer> }
  >()

  const answer = async (root: string, id: string, again: boolean): Promise<GlossAnswer> => {
    const reached = await openOver(options.carrier, root)
    if (reached.kind !== 'open') {
      return { kind: 'withheld', reason: openingUnreadable(reached).message }
    }
    const read = briefed(await reached.project.client.call(root, 'brief', { id }), id)
    if ('said' in read) return { kind: 'withheld', reason: read.said }

    // What was kept for this line in this language answers at once, stale or not: asking again
    // is the reader's own act, and Regenerate is where it lives (RG287).
    const tag = options.tag()
    const already = again ? null : glossFor(kept(), root, id, tag)
    if (already !== null) {
      return {
        kind: 'said',
        gloss: already.gloss,
        model: already.model,
        version: already.version,
        kept: true,
        stale: !glossStands(already, read.payload),
        // The other oldness, asked separately because the reader weighs it separately (RG290):
        // the line has not moved, and a new reading would fill in what this one has no slot for.
        outgrown: !glossShapeStands(already),
      }
    }

    const found = await options.agent(root)
    if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
    const agent = found.agent
    const env = await environment(found.agent, root)
    const [command = '', ...prefix] = agent.command

    // Counted per run, so every asking starts its stream at 0 and a screen can tell them apart.
    let told = 0
    const run = ask(
      {
        command,
        prefix,
        cwd: root,
        prompt: promptForGloss(read.payload, tag),
        schema: GLOSS_SCHEMA,
        line: (line) => {
          options.line?.(root, id, told, line)
          told += 1
        },
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
      const gloss = readGloss(said.structured, read.payload)
      keep(
        withGloss(kept(), {
          root,
          id,
          tag,
          gloss,
          version: said.version,
          model: said.model,
          answered: now().toISOString(),
          shape: GLOSS_SHAPE,
          line: glossedLine(read.payload),
        }),
      )
      return {
        kind: 'said',
        gloss,
        model: said.model,
        version: said.version,
        kept: false,
        stale: false,
        outgrown: false,
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
    gloss(root, id, again = false) {
      // A positional starting with a dash is an option to any parser, as `handOver` says.
      if (id === '' || id.startsWith('-')) {
        return Promise.resolve({ kind: 'withheld', reason: `\`${id}\` is not a line id` })
      }
      // The same question twice is one run: a screen asking again while it waits is waiting.
      const asking = running.get(`${root}\u0000${id}`)
      return asking?.answer ?? answer(root, id, again)
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
