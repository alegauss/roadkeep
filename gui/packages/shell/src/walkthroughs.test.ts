import {
  bridgedRun,
  NOTHING_WALKED,
  openedFrom,
  openProject,
  type AgentResolution,
  type KeptWalkthroughs,
  type OpenedProject,
  type Transport,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import type { Question, Answered, Asking } from './question'
import { createWalkthroughs, type Walkthroughs } from './walkthroughs'

/**
 * RG292: what asking for a walkthrough does, with every process faked.
 *
 * `glosses.test.ts`'s arrangement: the carrier answers by verb the way an engine would and the
 * query is a promise this test settles. What is held is the order — read the entry, resolve the
 * commit, find the agent, ask once — and what a second opening costs, which is the whole of why
 * anything is kept.
 */

const ROOT = '/proj'
const SHA = '216066b89561b6e9c68f9bab67fe9ffe9ae014a9'
const OTHER = '70aed365ee1c79a9cb73923901f5516ad807ecfe'

const ENTRY = {
  id: 'FX1',
  status: '✅',
  block: 'A',
  shipped: true,
  file: 'docs/CHANGELOG.md',
  line: 12,
  rendered: '- ✅ **FX1** **a read nothing answered** — The read answers now.',
  symptom: 'a read nothing answered',
  why: 'The read answers now.',
  deps: [],
  ref: '',
  section: null,
}

const AGENT: AgentResolution = {
  kind: 'resolved',
  agent: { command: ['claude'], version: '2.1.278', said: '2.1.278 (Claude Code)' },
}

/** An engine answering `show` and `origin` for one shipped entry. */
function engine(options: { shipped?: boolean; sha?: string | null } = {}): Transport {
  const commit = options.sha === undefined ? SHA : options.sha
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      const said = (value: unknown) =>
        Promise.resolve({ code: 0, stdout: JSON.stringify(value), stderr: '', durationMs: 1 })
      if (verb === 'engines') {
        return said({
          writing: { version: '0.2.489', home: '/e', revision: 'abc', on_disk: '0.2.489' },
          invoke: 'python launch.py',
          declaration: '',
          verdict: 'agreed',
          agree: true,
          readable: true,
          split: false,
          swapped: false,
        })
      }
      if (verb === 'config') return said({ version: '0.2.489', source: 'roadkeep.toml', keys: [] })
      if (verb === 'commands') return said({ version: '0.2.489', source: null, commands: [] })
      if (verb === 'show') return said({ ...ENTRY, shipped: options.shipped !== false })
      if (verb === 'origin') {
        return said({
          id: 'FX1',
          proposed_in: null,
          shipped_in:
            commit === null
              ? null
              : {
                  sha: commit,
                  short: commit.slice(0, 7),
                  date: '2026-09-21T15:37:08-03:00',
                  author: 'Somebody',
                  subject: 'feat: the read answers now (FX1)',
                  reasoning: 'feat: the read answers now (FX1)\n\nThe whole message.',
                },
        })
      }
      return said({})
    },
  }
}

/** One query, settled by hand: what was asked, and the answer whenever this test gives one. */
function asking() {
  const calls: Question[] = []
  let settle: (read: Answered) => void = () => undefined
  const ask = (call: Question): Asking => {
    calls.push(call)
    return {
      answered: new Promise<Answered>((resolve) => {
        settle = resolve
      }),
      cancel() {
        settle({ kind: 'cancelled' })
      },
    }
  }
  return {
    ask,
    calls,
    say: (read: Answered) => {
      settle(read)
    },
  }
}

const ANSWER = {
  kind: 'said' as const,
  structured: {
    before: ['a build of the app'],
    steps: [{ does: 'open the entry', sees: 'the steps are drawn' }],
    where: [{ path: 'packages/core/src/verbs.ts', said: 'the row lives here' }],
    nothingToSee: '',
  },
  model: 'claude-opus-5',
  version: '2.1.278',
}

/** What one machine has kept, as the file would hold it. */
function keeping() {
  let kept = NOTHING_WALKED
  return {
    kept: () => kept,
    keep: (written: KeptWalkthroughs) => {
      kept = written
    },
    get held() {
      return kept.walkthroughs
    },
  }
}

async function machine(store = keeping(), transport = engine(), tag = 'en') {
  const opened: OpenedProject = openedFrom(
    await openProject(ROOT, [['python', 'launch.py']], () => transport),
  )
  const query = asking()
  const made = createWalkthroughs({
    carrier: {
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
    },
    agent: () => Promise.resolve(AGENT),
    environment: () => Promise.resolve({}),
    tag: () => tag,
    ask: query.ask,
    kept: store.kept,
    keep: store.keep,
    now: () => new Date('2026-09-21T10:00:00.000Z'),
  })
  return { made, query, store }
}

/** Ask, answer, and hand back what the caller got. */
async function asked(made: Walkthroughs, query: ReturnType<typeof asking>, again = false) {
  const answering = made.walkthrough(ROOT, 'FX1', again)
  await new Promise((settle) => setTimeout(settle, 0))
  query.say(ANSWER)
  return answering
}

describe('RG291: the question a walkthrough asks', () => {
  it('anchors the prompt on the commit the entry shipped from', async () => {
    const first = await machine()
    const said = await asked(first.made, first.query)

    expect(said.kind).toBe('said')
    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.commit).toBe(SHA)
    expect(said.walkthrough.steps).toHaveLength(1)
    // The prompt is composed on this side out of what the two reads answered, and the sha in it
    // is the one `origin` resolved — never a sentence the renderer supplied.
    const prompt = first.query.calls[0]?.prompt ?? ''
    expect(prompt).toContain(`git show ${SHA}`)
    expect(prompt).toContain(ENTRY.rendered)
  })

  it('gives the run the bounded git read and no shell of its own', async () => {
    const first = await machine()
    await asked(first.made, first.query)

    const call = first.query.calls[0]
    expect(call?.tools).toEqual(['Read', 'Grep', 'Glob'])
    expect(call?.permits?.('Bash', { command: `git show ${SHA}` })).toBe('allow')
    expect(call?.permits?.('Bash', { command: 'rm -rf .' })).toBe('deny')
  })

  it('withholds a line that has not shipped, which has nothing to check', async () => {
    const open = await machine(keeping(), engine({ shipped: false }))
    const said = await open.made.walkthrough(ROOT, 'FX1')

    expect(said.kind).toBe('withheld')
    if (said.kind !== 'withheld') throw new Error(said.kind)
    expect(said.reason).toContain('has not shipped')
    // And nothing was asked of Claude Code for it.
    expect(open.query.calls).toEqual([])
  })

  it('withholds a name that is not a line id, before anything is opened', async () => {
    const one = await machine()

    expect((await one.made.walkthrough(ROOT, '')).kind).toBe('withheld')
    expect((await one.made.walkthrough(ROOT, '--help')).kind).toBe('withheld')
    expect(one.query.calls).toEqual([])
  })
})

describe('RG292: a walkthrough kept between openings', () => {
  it('keeps what was answered, and hands it back without asking again', async () => {
    const store = keeping()
    const first = await machine(store)
    expect((await asked(first.made, first.query)).kind).toBe('said')
    expect(store.held).toHaveLength(1)
    expect(store.held[0]?.commit).toBe(SHA)

    // The sheet closed because somebody went off to follow it, and came back.
    const again = await machine(store)
    const said = await again.made.walkthrough(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(true)
    expect(said.stale).toBe(false)
    expect(said.walkthrough.steps).toHaveLength(1)
    // Nothing was asked of Claude Code the second time, which is the whole of RG292.
    expect(again.query.calls).toEqual([])
  })

  it('keeps one language apart from another', async () => {
    const store = keeping()
    const english = await machine(store)
    await asked(english.made, english.query)

    const portuguese = await machine(store, engine(), 'pt-BR')
    const answering = portuguese.made.walkthrough(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))

    expect(portuguese.query.calls[0]?.prompt).toContain('pt-BR')
    portuguese.query.say(ANSWER)
    await answering
    expect(store.held).toHaveLength(2)
  })

  it('reads one as old once the entry ships from another commit, and still draws it', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)

    // The shipping commit was amended, so the same entry now resolves to another hash.
    const moved = await machine(store, engine({ sha: OTHER }))
    const said = await moved.made.walkthrough(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(true)
    expect(said.stale).toBe(true)
    // Still handed back rather than thrown away — it was true of what shipped — and nothing was
    // asked for it. Regenerate is the reader's own act.
    expect(said.walkthrough.steps).toHaveLength(1)
    expect(said.commit).toBe(SHA)
    expect(moved.query.calls).toEqual([])
  })

  it('reads one as old where the history can no longer place the commit', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)

    const unplaced = await machine(store, engine({ sha: null }))
    const said = await unplaced.made.walkthrough(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.stale).toBe(true)
  })

  it('asks anew and replaces what was kept when the reader asks again', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)

    const again = await machine(store)
    const said = await asked(again.made, again.query, true)

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(false)
    expect(again.query.calls).toHaveLength(1)
    expect(store.held).toHaveLength(1)
  })

  it('keeps nothing of a run that was cancelled or failed', async () => {
    const store = keeping()
    const one = await machine(store)
    const answering = one.made.walkthrough(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    one.query.say({ kind: 'failed', said: 'it said nothing usable' })

    expect((await answering).kind).toBe('failed')
    expect(store.held).toEqual([])
  })

  it('joins a run already going rather than starting a second', async () => {
    const one = await machine()
    const first = one.made.walkthrough(ROOT, 'FX1')
    // After the reads, so the run is registered: a screen asking while it waits is waiting, and
    // the two calls before either read has answered are two questions nothing has joined yet.
    await new Promise((settle) => setTimeout(settle, 0))
    const second = one.made.walkthrough(ROOT, 'FX1')
    one.query.say(ANSWER)

    expect((await first).kind).toBe('said')
    expect((await second).kind).toBe('said')
    expect(one.query.calls).toHaveLength(1)
  })
})
