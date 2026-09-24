import {
  bridgedRun,
  openedFrom,
  openProject,
  type AgentResolution,
  GLOSS_SHAPE,
  NOTHING_GLOSSED,
  type KeptGlosses,
  type OpenedProject,
  type Transport,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import type { Question, Answered, Asking } from './question'
import { createGlosses, type Glosses } from './glosses'

/**
 * RG284: what asking for a gloss does, with every process faked.
 *
 * The carrier answers by verb the way an engine would and the query is a promise this test
 * settles. What is held is the order — read the line, find the agent, ask once — and that the
 * renderer's part of it is an id and nothing else: the prompt is composed here, out of the brief
 * this side read.
 */

const ROOT = '/proj'

const LINE = {
  id: 'FX1',
  status: '📋',
  block: 'A',
  rendered: '- 📋 **FX1** **a line ready to start** — It is. → §FX1',
  symptom: 'a line ready to start',
  why: 'It is.',
  deps: ['FX0'],
  readiness: 'ready',
  held: [],
  non_goals: ['No Markdown parsed in this app'],
}

const AGENT: AgentResolution = {
  kind: 'resolved',
  agent: { command: ['claude'], version: '2.1.274', said: '2.1.274 (Claude Code)' },
}

const NO_AGENT: AgentResolution = {
  kind: 'unresolved',
  reason: 'no claude answered',
  tried: [['claude'], ['claude.cmd']],
}

function engine(why = LINE.why): Transport {
  return {
    run(request) {
      const verb = request.argv[2] ?? ''
      const id = request.argv[3] ?? ''
      const said = (value: unknown) =>
        Promise.resolve({ code: 0, stdout: JSON.stringify(value), stderr: '', durationMs: 1 })
      if (verb === 'engines') {
        return said({
          writing: { version: '0.2.400', home: '/e', revision: 'abc', on_disk: '0.2.400' },
          invoke: 'python launch.py',
          declaration: '',
          verdict: 'agreed',
          agree: true,
          readable: true,
          split: false,
          swapped: false,
        })
      }
      if (verb === 'config') {
        return said({ version: '0.2.400', source: 'roadkeep.toml', keys: [] })
      }
      if (verb === 'commands') return said({ version: '0.2.400', source: null, commands: [] })
      if (verb === 'brief') {
        if (id === 'FX9') {
          return Promise.resolve({
            code: 1,
            stdout: JSON.stringify({ refused: [], beside: '', about: '', said: 'no such line' }),
            stderr: '',
            durationMs: 1,
          })
        }
        return said({ ...LINE, id, why })
      }
      return said({})
    },
  }
}

/** One query, settled by hand: what was asked, and the answer whenever this test gives one. */
function asking() {
  const calls: Question[] = []
  let cancels = 0
  let settle: (read: Answered) => void = () => undefined
  const ask = (call: Question): Asking => {
    calls.push(call)
    return {
      answered: new Promise<Answered>((resolve) => {
        settle = resolve
      }),
      cancel() {
        cancels += 1
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
    get cancels() {
      return cancels
    },
  }
}

const ANSWER = {
  kind: 'said' as const,
  structured: {
    headline: 'what the line is',
    today: 'what is true now',
    after: 'what is true after',
    deps: { FX0: 'the one it waits on', FX7: 'a line nobody filed' },
    binds: { 'No Markdown parsed in this app': 'said as it is' },
  },
  model: 'claude-opus-5',
  version: '2.1.274',
}

async function glosses(agent: AgentResolution = AGENT) {
  const transport = engine()
  const opened: OpenedProject = openedFrom(
    await openProject(ROOT, [['python', 'launch.py']], () => transport),
  )
  const query = asking()
  const made = createGlosses({
    carrier: {
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
    },
    agent: () => Promise.resolve(agent),
    environment: () => Promise.resolve({ PATH: '/usr/bin' }),
    tag: () => 'pt-BR',
    ask: query.ask,
  })
  return { made, query }
}

describe('RG284: asking what a line means', () => {
  it('reads the line itself and frames that brief, so a page never sends a prompt', async () => {
    const { made, query } = await glosses()

    const answering = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    query.say(ANSWER)
    const said = await answering

    const [call] = query.calls
    expect(call?.cwd).toBe(ROOT)
    expect(call?.prompt).toContain('roadkeep task FX1')
    // The payload as the engine answered it, and the window's language, which is main's.
    expect(call?.prompt).toContain('a line ready to start')
    expect(call?.prompt).toContain('Write every string in pt-BR.')
    expect(said.kind).toBe('said')
  })

  it('reads the answer against the brief, dropping what the brief does not carry', async () => {
    const { made, query } = await glosses()

    const answering = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    query.say(ANSWER)
    const said = await answering

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.gloss.headline).toBe('what the line is')
    expect(Object.keys(said.gloss.deps)).toEqual(['FX0'])
    expect(said.model).toBe('claude-opus-5')
    expect(said.version).toBe('2.1.274')
  })

  it('asks once for a line already being asked about, rather than starting a second run', async () => {
    const { made, query } = await glosses()

    const first = made.gloss(ROOT, 'FX1')
    // Once the first has reached the query: before that there is nothing yet to join.
    await new Promise((settle) => setTimeout(settle, 0))
    const second = made.gloss(ROOT, 'FX1')
    query.say(ANSWER)

    expect((await first).kind).toBe('said')
    expect((await second).kind).toBe('said')
    expect(query.calls).toHaveLength(1)
  })

  it('cancels the run a reader gave up on, and answers cancelled', async () => {
    const { made, query } = await glosses()

    const answering = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    made.cancel(ROOT, 'FX1')

    expect((await answering).kind).toBe('cancelled')
    expect(query.cancels).toBe(1)
    // And a line nothing is running for is not an error.
    expect(() => {
      made.cancel(ROOT, 'FX8')
    }).not.toThrow()
  })

  it('withholds a line the engine refused, and an id that is not one', async () => {
    const { made, query } = await glosses()

    expect(await made.gloss(ROOT, 'FX9')).toEqual({ kind: 'withheld', reason: 'no such line' })
    expect((await made.gloss(ROOT, '--designed')).kind).toBe('withheld')
    expect(query.calls).toEqual([])
  })

  it('says the machine has no Claude Code, with every command tried', async () => {
    const { made, query } = await glosses(NO_AGENT)

    expect(await made.gloss(ROOT, 'FX1')).toEqual({
      kind: 'unavailable',
      tried: [['claude'], ['claude.cmd']],
    })
    expect(query.calls).toEqual([])
  })

  it('gives up every run still going when the window closes', async () => {
    const { made, query } = await glosses()

    const answering = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    made.close()

    expect((await answering).kind).toBe('cancelled')
    expect(query.cancels).toBe(1)
  })
})

describe('RG287: a gloss kept between openings', () => {
  /** What one machine has kept, as the file would hold it. */
  function keeping() {
    let kept = NOTHING_GLOSSED
    return {
      kept: () => kept,
      keep: (written: KeptGlosses) => {
        kept = written
      },
      get held() {
        return kept.glosses
      },
    }
  }

  async function machine(store = keeping(), tag = 'en', why?: string) {
    const transport = engine(why)
    const opened: OpenedProject = openedFrom(
      await openProject(ROOT, [['python', 'launch.py']], () => transport),
    )
    const query = asking()
    const made = createGlosses({
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
  async function asked(made: Glosses, query: ReturnType<typeof asking>, again = false) {
    const answering = made.gloss(ROOT, 'FX1', again)
    await new Promise((settle) => setTimeout(settle, 0))
    query.say(ANSWER)
    return answering
  }

  it('keeps what was answered, and hands it back without asking again', async () => {
    const store = keeping()
    const first = await machine(store)
    expect((await asked(first.made, first.query)).kind).toBe('said')
    expect(store.held).toHaveLength(1)

    // A second window, a second run of the app: the file is what carries it across.
    const again = await machine(store)
    const said = await again.made.gloss(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(true)
    expect(said.stale).toBe(false)
    expect(said.outgrown).toBe(false)
    expect(said.gloss.headline).toBe('what the line is')
    // Nothing was asked of Claude Code the second time.
    expect(again.query.calls).toEqual([])
  })

  it('keeps one language apart from another', async () => {
    const store = keeping()
    const english = await machine(store, 'en')
    await asked(english.made, english.query)

    const portuguese = await machine(store, 'pt-BR')
    const answering = portuguese.made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))

    // A window in another language has none kept, so it asks — in that language.
    expect(portuguese.query.calls[0]?.prompt).toContain('Write every string in pt-BR.')
    portuguese.query.say(ANSWER)
    await answering
    expect(store.held).toHaveLength(2)
  })

  it('hands back a gloss the line has moved under, saying it is old', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)

    // The same line, restated since: the gloss explained what it used to claim.
    const moved = await machine(store, 'en', 'Somebody rewrote why this matters.')
    const said = await moved.made.gloss(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(true)
    expect(said.stale).toBe(true)
    // The line moved, and the answer's shape did not: one reason, and the reader is told which.
    expect(said.outgrown).toBe(false)
    // Still handed back rather than thrown away, and nothing was asked for it.
    expect(said.gloss.headline).toBe('what the line is')
    expect(moved.query.calls).toEqual([])
  })

  it('RG290: hands back one written before the answer grew, saying that instead', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)
    // What the file holds after a build that had fewer slots than this one. Written over the
    // store rather than mocked, because what a reader gets has to come off the entry itself.
    store.keep({
      ...store.kept(),
      glosses: store.kept().glosses.map((one) => ({ ...one, shape: GLOSS_SHAPE - 1 })),
    })

    const again = await machine(store)
    const said = await again.made.gloss(ROOT, 'FX1')

    if (said.kind !== 'said') throw new Error(said.kind)
    expect(said.kept).toBe(true)
    // The line is exactly as it was, which is the state nothing said anything about before.
    expect(said.stale).toBe(false)
    expect(said.outgrown).toBe(true)
    expect(said.gloss.headline).toBe('what the line is')
    expect(again.query.calls).toEqual([])
  })

  it('RG290: writes this build shape into what it keeps, so the next build can tell', async () => {
    const store = keeping()
    const first = await machine(store)
    await asked(first.made, first.query)

    expect(store.held[0]?.shape).toBe(GLOSS_SHAPE)
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
})

describe('RG297: the run’s stream, while it is asked', () => {
  /** A machine that tells every line it hears, and the query that answers it. */
  async function telling() {
    const transport = engine()
    const opened: OpenedProject = openedFrom(
      await openProject(ROOT, [['python', 'launch.py']], () => transport),
    )
    const query = asking()
    const told: [string, string, number, string][] = []
    const made = createGlosses({
      carrier: {
        open: () => Promise.resolve(opened),
        run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      },
      agent: () => Promise.resolve(AGENT),
      environment: () => Promise.resolve({}),
      tag: () => 'en',
      ask: query.ask,
      line: (root, id, index, line) => {
        told.push([root, id, index, line])
      },
    })
    return { made, query, told }
  }

  it('names the project, the line and its place beside each line, as the run writes it', async () => {
    const { made, query, told } = await telling()

    const answering = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    // What the run passes back as it goes, which the query carries rather than composes.
    query.calls[0]?.line?.('{"type":"system","subtype":"init"}')
    query.calls[0]?.line?.('{"type":"assistant"}')
    query.say(ANSWER)
    await answering

    expect(told).toEqual([
      [ROOT, 'FX1', 0, '{"type":"system","subtype":"init"}'],
      [ROOT, 'FX1', 1, '{"type":"assistant"}'],
    ])
  })

  it('starts every asking at the first line again', async () => {
    const { made, query, told } = await telling()

    const first = made.gloss(ROOT, 'FX1')
    await new Promise((settle) => setTimeout(settle, 0))
    query.calls[0]?.line?.('{"type":"assistant"}')
    query.say(ANSWER)
    await first

    const again = made.gloss(ROOT, 'FX1', true)
    await new Promise((settle) => setTimeout(settle, 0))
    query.calls[1]?.line?.('{"type":"assistant"}')
    query.say(ANSWER)
    await again

    expect(told.map(([, , index]) => index)).toEqual([0, 0])
  })
})
