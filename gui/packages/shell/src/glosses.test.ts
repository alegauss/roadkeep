import {
  bridgedRun,
  openedFrom,
  openProject,
  type AgentResolution,
  type OpenedProject,
  type Transport,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import type { GlossCall, GlossRead, GlossRun } from './gloss-process'
import { createGlosses } from './glosses'

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

function engine(): Transport {
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
        return said({ ...LINE, id })
      }
      return said({})
    },
  }
}

/** One query, settled by hand: what was asked, and the answer whenever this test gives one. */
function asking() {
  const calls: GlossCall[] = []
  let cancels = 0
  let settle: (read: GlossRead) => void = () => undefined
  const ask = (call: GlossCall): GlossRun => {
    calls.push(call)
    return {
      answered: new Promise<GlossRead>((resolve) => {
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
    say: (read: GlossRead) => {
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
