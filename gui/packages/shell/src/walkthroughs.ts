import {
  NOTHING_WALKED,
  openingUnreadable,
  openOver,
  promptForWalkthrough,
  readWalkthrough,
  WALKTHROUGH_SCHEMA,
  walkthroughFor,
  walkthroughStands,
  withWalkthrough,
  type Agent,
  type AgentResolution,
  type KeptWalkthroughs,
  type OriginPayload,
  type ReadOutcome,
  type ShowPayload,
  type WalkthroughAnswer,
} from '@rk/core'

import type { Carrier } from './carrier'

import { askGloss, permitsGitRead, WALKTHROUGH_TOOLS, type GlossRun } from './gloss-process'

/**
 * How to check a shipped entry, asked of Claude Code and kept (RG291, RG292).
 *
 * `glosses.ts`'s arrangement, beside it and for its reasons: the renderer names an entry and
 * never a prompt, one run per entry at a time, and every line of the stream passed on as it
 * passes. What differs is what the question is anchored on and what makes an answer old.
 *
 * **Two reads before the question.** `show` gives the ledger's own sentence and says whether the
 * line shipped at all; `origin` resolves the commit that wrote the entry. The first is the
 * subject and the second is the evidence, and neither is composed here.
 *
 * **Kept, because the sheet is closed by the act of following it** (RG292). Somebody leaves the
 * window, opens a terminal, runs the build, comes back — and an answer thrown away at that
 * moment is thrown away every time. What is kept stands while the entry still ships from the
 * same commit, which is one hash and the whole test.
 *
 * **A line that has not shipped is withheld.** There is nothing to check and no commit to read,
 * so the question is not asked rather than answered emptily.
 */

export interface WalkthroughsOptions {
  /** How reads are made: through the carrier, as a window makes them. */
  readonly carrier: Pick<Carrier, 'open' | 'run'>
  /** Which Claude Code answers here, asked from a project's root — the session's resolution. */
  readonly agent: (root: string) => Promise<AgentResolution>
  /** The environment it runs in (RG205). The one this process inherited unless a caller says. */
  readonly environment?: (agent: Agent, root: string) => Promise<NodeJS.ProcessEnv>
  /** The language every string comes back in. Main's, never the renderer's. */
  readonly tag: () => string
  /** Start the query. `askGloss` unless a test says otherwise. */
  readonly ask?: typeof askGloss
  /** What this machine has kept (RG292). Nothing kept unless a caller holds a file. */
  readonly kept?: () => KeptWalkthroughs
  /** Keep what was just answered. Nothing is kept unless a caller writes it somewhere. */
  readonly keep?: (walkthroughs: KeptWalkthroughs) => void
  /** When one was answered, which is what the bound reads. The clock unless a test drives it. */
  readonly now?: () => Date
  /** Tell whoever is watching that project each line of the run's stream, with its place. */
  readonly line?: (root: string, id: string, index: number, line: string) => void
}

export interface Walkthroughs {
  /**
   * Ask how to check one shipped entry, or hand back what was kept for it (RG292).
   *
   * @param again ask anew and replace what was kept, whatever is kept for the entry
   */
  walkthrough(root: string, id: string, again?: boolean): Promise<WalkthroughAnswer>
  /** Give up on one that is running. An entry nothing is running for does nothing. */
  cancel(root: string, id: string): void
  /** Give up on every one still running, which is what quitting does. */
  close(): void
}

/** What the two reads found, or the sentence to withhold with. */
interface Anchored {
  readonly said: string
  readonly origin: OriginPayload
  readonly commit: string
}

export function createWalkthroughs(options: WalkthroughsOptions): Walkthroughs {
  const ask = options.ask ?? askGloss
  const environment = options.environment ?? (() => Promise.resolve(process.env))
  const kept = options.kept ?? (() => NOTHING_WALKED)
  const keep = options.keep ?? (() => undefined)
  const now = options.now ?? (() => new Date())
  const running = new Map<
    string,
    { readonly run: GlossRun; readonly answer: Promise<WalkthroughAnswer> }
  >()

  const answer = async (root: string, id: string, again: boolean): Promise<WalkthroughAnswer> => {
    const reached = await openOver(options.carrier, root)
    if (reached.kind !== 'open') {
      return { kind: 'withheld', reason: openingUnreadable(reached).message }
    }
    const client = reached.project.client

    const shown = await client.call(root, 'show', { id, noBody: true })
    if (shown.kind !== 'read') {
      return { kind: 'withheld', reason: saidOf(shown) }
    }
    const entry: ShowPayload = shown.value
    if (!entry.shipped) {
      // Nothing shipped is nothing to try, and the engine's own word for it is what says so.
      return { kind: 'withheld', reason: `${id} has not shipped, so there is nothing to check` }
    }

    const resolved = await client.call(root, 'origin', { id })
    if (resolved.kind !== 'read') {
      return { kind: 'withheld', reason: saidOf(resolved) }
    }
    const anchored: Anchored = {
      said: entry.rendered === '' ? entry.why : entry.rendered,
      origin: resolved.value,
      commit: resolved.value.shippedIn?.sha ?? '',
    }

    // What was kept for this entry in this language answers at once, stale or not: asking again
    // is the reader's own act, and Regenerate is where it lives (RG292).
    const tag = options.tag()
    const already = again ? null : walkthroughFor(kept(), root, id, tag)
    if (already !== null) {
      return {
        kind: 'said',
        walkthrough: already.walkthrough,
        model: already.model,
        version: already.version,
        kept: true,
        stale: !walkthroughStands(already, anchored.commit),
        commit: already.commit,
      }
    }

    const found = await options.agent(root)
    if (found.kind !== 'resolved') return { kind: 'unavailable', tried: found.tried }
    const agent = found.agent
    const env = await environment(found.agent, root)
    const [command = '', ...prefix] = agent.command

    let told = 0
    const run = ask(
      {
        command,
        prefix,
        cwd: root,
        prompt: promptForWalkthrough(anchored.origin, anchored.said, tag),
        schema: WALKTHROUGH_SCHEMA,
        tools: WALKTHROUGH_TOOLS,
        // The one shell call it may make, bounded on this side (RG291).
        permits: permitsGitRead,
        line: (line) => {
          options.line?.(root, id, told, line)
          told += 1
        },
      },
      env,
    )
    const key = `${root}\u0000${id}`
    const answered = run.answered.then((said): WalkthroughAnswer => {
      if (said.kind === 'cancelled') return { kind: 'cancelled' }
      if (said.kind === 'unavailable') return { kind: 'unavailable', tried: [agent.command] }
      if (said.kind === 'failed') return { kind: 'failed', said: said.said }
      const walkthrough = readWalkthrough(said.structured)
      keep(
        withWalkthrough(kept(), {
          root,
          id,
          tag,
          walkthrough,
          version: said.version,
          model: said.model,
          answered: now().toISOString(),
          commit: anchored.commit,
        }),
      )
      return {
        kind: 'said',
        walkthrough,
        model: said.model,
        version: said.version,
        kept: false,
        stale: false,
        commit: anchored.commit,
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
    walkthrough(root, id, again = false) {
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

/** The engine's own sentence about a read that did not answer, quoted and never composed. */
function saidOf<T>(outcome: ReadOutcome<T>): string {
  if (outcome.kind === 'refused') return outcome.refusal.said
  if (outcome.kind === 'unreadable') return outcome.unreadable.message
  return ''
}
