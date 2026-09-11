import {
  bridgedRun,
  EngineCallFailed,
  openedFrom,
  openProject,
  type AgentResolution,
  type OpenedProject,
  type SessionCall,
  type SessionOutcome,
  type TopicEvents,
  type Transport,
} from '@rk/core'
import { describe, expect, it } from 'vitest'

import type { RunningSession, SessionWatcher } from './session-process'
import { createSessions, type SessionsOptions } from './sessions'

/**
 * RG153: handing a line to a session, with every process faked.
 *
 * The carrier answers by verb the way an engine would, the agent is a resolution this test
 * chose, and the session is a process that writes the lines the test hands it. What is held
 * is the order of the handover — read, name a holder, find the agent, take the line, start —
 * and that nothing is taken on any path that does not start.
 */

const ROOT = '/proj'

const LINE = {
  id: 'FX1',
  status: '📋',
  block: 'A',
  rendered: '- 📋 **FX1** **a line ready to start** — It is. → §FX1',
  symptom: 'a line ready to start',
  why: 'It is.',
  deps: [],
  readiness: 'ready',
  held: [],
}

const HOLDER = { by: 'another session', since: '2026-09-11T10:00:00Z', state: 'held', paths: [] }

function engine(): { transport: Transport; asked: string[][] } {
  const asked: string[][] = []
  const transport: Transport = {
    run(request) {
      asked.push([...request.argv])
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
        return said({
          version: '0.2.400',
          source: 'roadkeep.toml',
          keys: [
            {
              table: 'files',
              key: 'roadmap',
              address: 'files.roadmap',
              declared: true,
              set: '"docs/ROADMAP.md"',
              default: null,
            },
          ],
        })
      }
      if (verb === 'commands') return said({ version: '0.2.400', source: null, commands: [] })
      if (verb === 'brief') {
        const claiming = request.argv.includes('--claim')
        if (id === 'FX2') return said({ ...LINE, id, held: [HOLDER] })
        if (id === 'FX3') return said({ ...LINE, id, readiness: 'blocked' })
        if (id === 'FX9') {
          return Promise.resolve({
            code: 1,
            stdout: JSON.stringify({ refused: [], beside: '', about: '', said: 'no such line' }),
            stderr: '',
            durationMs: 1,
          })
        }
        return said({
          ...LINE,
          id,
          status: claiming ? '🛠' : '📋',
          claimed: claiming ? { taken: true, from: '📋', to: '🛠' } : null,
        })
      }
      return Promise.reject(new EngineCallFailed('unspawnable', 'no', 1))
    },
  }
  return { transport, asked }
}

const FOUND: AgentResolution = {
  kind: 'resolved',
  agent: { command: ['node', 'claude.mjs'], version: '2.1.263', said: '2.1.263 (Claude Code)' },
}

/** A process the test drives: it writes what it is handed and ends when it is told to. */
interface Fake {
  readonly calls: SessionCall[]
  readonly cancelled: number
  write(line: string): void
  end(outcome: SessionOutcome): void
}

function process(): { fake: Fake; start: NonNullable<SessionsOptions['start']> } {
  const calls: SessionCall[] = []
  let watcher: SessionWatcher = {}
  let finish: (outcome: SessionOutcome) => void = () => undefined
  let cancelled = 0
  const fake: Fake = {
    calls,
    get cancelled() {
      return cancelled
    },
    write: (line) => watcher.onLine?.(line),
    end: (outcome) => {
      finish(outcome)
    },
  }
  const start = (call: SessionCall, heard: SessionWatcher): RunningSession => {
    calls.push(call)
    watcher = heard
    const finished = new Promise<SessionOutcome>((resolve) => {
      finish = resolve
    })
    return {
      cancel: () => {
        cancelled += 1
        finish({ state: 'cancelled', sessionId: '', code: null, said: '', result: '' })
      },
      finished,
      events: [],
    }
  }
  return { fake, start }
}

async function sessions(agent: AgentResolution = FOUND) {
  const { transport, asked } = engine()
  const opened: OpenedProject = openedFrom(
    await openProject(ROOT, [['python', 'launch.py']], () => transport),
  )
  const published: TopicEvents['session'][] = []
  const { fake, start } = process()
  let asksForAgent = 0
  const made = createSessions({
    carrier: {
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
    },
    agent: () => {
      asksForAgent += 1
      return Promise.resolve(agent)
    },
    publish: (event) => published.push(event),
    start,
    key: () => 'session-1',
  })
  const claims = () => asked.filter((argv) => argv[2] === 'brief' && argv.includes('--claim'))
  return { made, fake, published, claims, asksForAgent: () => asksForAgent }
}

const DONE: SessionOutcome = { state: 'done', sessionId: 's', code: 0, said: '', result: 'done' }

describe('RG153: a line handed to a session', () => {
  it('takes the line with a claiming brief and starts the session from that payload', async () => {
    const { made, fake, claims } = await sessions()

    const handed = await made.handOver(ROOT, 'FX1')

    expect(handed.kind).toBe('started')
    if (handed.kind !== 'started') return
    expect(claims()).toHaveLength(1)
    // What it was told is the claiming read's answer, marker moved and all.
    expect(handed.session.handed.status).toBe('🛠')
    expect(handed.session.handed.claimed?.taken).toBe(true)
    // The agent's own command first, then the call: the prompt is the brief, never a page's.
    const [call] = fake.calls
    expect(call?.command).toBe('node')
    expect(call?.argv[0]).toBe('claude.mjs')
    expect(call?.argv).toContain('-p')
    expect(call?.argv.find((part) => part.includes('"id": "FX1"'))).toBeDefined()
    expect(call?.cwd).toBe(ROOT)
  })

  it('names the holder of a held line and takes nothing', async () => {
    const { made, fake, claims } = await sessions()

    const handed = await made.handOver(ROOT, 'FX2')

    expect(handed).toEqual({ kind: 'held', held: [HOLDER] })
    expect(claims()).toEqual([])
    expect(fake.calls).toEqual([])
  })

  it('takes nothing where the engine does not call the line ready, and says its word', async () => {
    const { made, claims } = await sessions()

    expect(await made.handOver(ROOT, 'FX3')).toEqual({ kind: 'unready', readiness: 'blocked' })
    expect(claims()).toEqual([])
  })

  it('takes nothing on a machine with no Claude Code, and names what it tried', async () => {
    const tried = [['claude']]
    const { made, claims } = await sessions({ kind: 'unresolved', reason: 'none', tried })

    expect(await made.handOver(ROOT, 'FX1')).toEqual({ kind: 'unavailable', tried })
    expect(claims()).toEqual([])
  })

  it('asks again for Claude Code after a machine had none, and keeps one it found', async () => {
    const missing = await sessions({ kind: 'unresolved', reason: 'none', tried: [] })
    await missing.made.handOver(ROOT, 'FX1')
    await missing.made.handOver(ROOT, 'FX1')
    expect(missing.asksForAgent()).toBe(2)

    const found = await sessions()
    await found.made.handOver(ROOT, 'FX1')
    await found.made.handOver(ROOT, 'FX1')
    expect(found.asksForAgent()).toBe(1)
  })

  it('quotes the engine where it refused to brief the line', async () => {
    const { made } = await sessions()

    expect(await made.handOver(ROOT, 'FX9')).toEqual({ kind: 'refused', said: 'no such line' })
  })

  it('refuses an id that is an option, which brief would take as one', async () => {
    // `--designed` is a flag `brief` accepts: sent as an id, the claim lands on the pick.
    const { made, claims } = await sessions()

    const handed = await made.handOver(ROOT, '--designed')

    expect(handed.kind).toBe('withheld')
    expect(claims()).toEqual([])
  })
})

describe('RG153: what a running session says', () => {
  it('publishes every line with its place in the stream, and keeps them for a late screen', async () => {
    const { made, fake, published } = await sessions()
    await made.handOver(ROOT, 'FX1')

    fake.write('{"type":"system"}')
    fake.write('{"type":"assistant"}')

    expect(published).toEqual([
      { session: 'session-1', index: 0, line: '{"type":"system"}' },
      { session: 'session-1', index: 1, line: '{"type":"assistant"}' },
    ])
    expect(made.list()[0]?.lines).toEqual(['{"type":"system"}', '{"type":"assistant"}'])
    expect(made.list()[0]?.outcome).toBeNull()
  })

  it('publishes how it ended, and keeps that too', async () => {
    const { made, fake, published } = await sessions()
    await made.handOver(ROOT, 'FX1')

    fake.end(DONE)
    await Promise.resolve()

    expect(published.at(-1)).toEqual({ session: 'session-1', outcome: DONE })
    expect(made.list()[0]?.outcome).toEqual(DONE)
  })

  it('stops a running session, and nothing for one that ended or was never started', async () => {
    const { made, fake } = await sessions()
    await made.handOver(ROOT, 'FX1')

    made.stop('nobody')
    expect(fake.cancelled).toBe(0)
    made.stop('session-1')
    expect(fake.cancelled).toBe(1)
    await Promise.resolve()
    made.stop('session-1')
    expect(fake.cancelled).toBe(1)
  })

  it('stops what is still running when it closes, and waits for it', async () => {
    const { made, fake } = await sessions()
    await made.handOver(ROOT, 'FX1')

    await made.close()

    expect(fake.cancelled).toBe(1)
    expect(made.list()[0]?.outcome?.state).toBe('cancelled')
  })

  it('hands back copies, so nothing outside can edit what it holds', async () => {
    const { made, fake } = await sessions()
    await made.handOver(ROOT, 'FX1')
    fake.write('{"type":"system"}')

    const first = made.list()[0]
    fake.write('{"type":"assistant"}')

    expect(first?.lines).toHaveLength(1)
  })
})
