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

import { createDoorKeep } from './door-keep'
import type { RunningSession, SessionWatcher } from './session-process'
import type { OnMoved, SessionWatch } from './session-watch'
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
  /** The environment each call was started with, in the same order. */
  readonly envs: NodeJS.ProcessEnv[]
  readonly cancelled: number
  write(line: string): void
  end(outcome: SessionOutcome): void
}

function process(): { fake: Fake; start: NonNullable<SessionsOptions['start']> } {
  const calls: SessionCall[] = []
  const envs: NodeJS.ProcessEnv[] = []
  let watcher: SessionWatcher = {}
  let finish: (outcome: SessionOutcome) => void = () => undefined
  let cancelled = 0
  const fake: Fake = {
    calls,
    envs,
    get cancelled() {
      return cancelled
    },
    write: (line) => watcher.onLine?.(line),
    end: (outcome) => {
      finish(outcome)
    },
  }
  const start = (
    call: SessionCall,
    heard: SessionWatcher,
    env: NodeJS.ProcessEnv,
  ): RunningSession => {
    calls.push(call)
    envs.push(env)
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

/** The clock's answer as a session is spawned. */
const SPAWNED = new Date('2026-09-15T10:00:00.000Z')

/** The environment the fake decision hands back, so a test can find it at the process. */
const DECIDED: NodeJS.ProcessEnv = { PATH: '/bin', DECIDED: 'yes' }

/** A recursive watch the test drives, and a clock it ticks: nothing here waits on either. */
function fakeWatch() {
  const roots: string[] = []
  const stopped: string[] = []
  let told: OnMoved | null = null
  let queued: (() => void)[] = []
  return {
    roots,
    stopped,
    watch: (root: string, moved: OnMoved): SessionWatch => {
      roots.push(root)
      told = moved
      return {
        stop() {
          stopped.push(root)
        },
      }
    },
    clock: {
      after(_ms: number, run: () => void) {
        queued.push(run)
        return () => {
          queued = queued.filter((one) => one !== run)
        }
      },
    },
    move(path: string, at: string) {
      told?.(path, at)
    },
    tick() {
      const running = queued
      queued = []
      for (const run of running) run()
    },
    get pending() {
      return queued.length
    },
  }
}

async function sessions(agent: AgentResolution = FOUND) {
  const { transport, asked } = engine()
  const opened: OpenedProject = openedFrom(
    await openProject(ROOT, [['python', 'launch.py']], () => transport),
  )
  const published: TopicEvents['session'][] = []
  const { fake, start } = process()
  let asksForAgent = 0
  const environmentsAsked: { agent: string; root: string; claimsBefore: number }[] = []
  const claims = () => asked.filter((argv) => argv[2] === 'brief' && argv.includes('--claim'))
  const watch = fakeWatch()
  // The batch a gate answer left, which is what a door is named against (RG263). Held by the
  // test so it can keep one and then hand it over, the way a window does.
  const doors = createDoorKeep({ stampOf: () => Promise.resolve('one') })
  const made = createSessions({
    carrier: {
      open: () => Promise.resolve(opened),
      run: (root, request) => bridgedRun(() => transport.run({ ...request, root })),
      doors,
    },
    agent: () => {
      asksForAgent += 1
      return Promise.resolve(agent)
    },
    environment: (found, root) => {
      environmentsAsked.push({
        agent: found.command.join(' '),
        root,
        claimsBefore: claims().length,
      })
      return Promise.resolve(DECIDED)
    },
    publish: (event) => published.push(event),
    start,
    key: () => 'session-1',
    now: () => SPAWNED,
    skip: () => ['node_modules'],
    watch: watch.watch,
    clock: watch.clock,
  })
  return {
    made,
    fake,
    watch,
    doors,
    published,
    claims,
    asksForAgent: () => asksForAgent,
    environmentsAsked,
  }
}

/**
 * A gate answer with one finding that offers a door, and a note that offers another (RG263).
 *
 * The note's door is first in the document, so its place in the batch is 0 and the finding's
 * is 1 — the ordering `doorsIn` flattens and the case a session started on the wrong number
 * would be about something nobody chose.
 */
const GATED = {
  root: ROOT,
  clean: false,
  lines: 4,
  sections: 1,
  problems: 1,
  checked: ['docs/IMPROVEMENTS.md'],
  codes: { 'ref.dangling': 1 },
  notes: [
    {
      code: 'install.stale',
      file: '.claude/hooks/roadkeep-launch.py',
      line: null,
      column: null,
      id: null,
      message: 'this surface is behind the roadkeep answering here',
      remedy: {
        kind: 'run',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [{ argv: ['install'], what: 'rewrites the launcher', complete: true, writes: true }],
      },
    },
  ],
  findings: [
    {
      code: 'ref.dangling',
      file: 'docs/IMPROVEMENTS.md',
      line: 392,
      column: null,
      id: 'T50',
      message: '§T50 cites §T21, which is not in docs/IMPROVEMENTS.md',
      remedy: {
        kind: 'compose',
        decision: '',
        sequence: false,
        awaits: '',
        doors: [
          {
            argv: ['section', 'amend', 'T50', '--body', '-', '--role', 'improvements'],
            what: 'the rewrite arrives on stdin',
            complete: true,
            writes: true,
          },
        ],
      },
    },
  ],
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
    const told = handed.session.handed
    if (told.kind !== 'line') throw new Error('a line was handed over, not a finding')
    expect(told.brief.status).toBe('🛠')
    expect(told.brief.claimed?.taken).toBe(true)
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

  it('starts the session in the environment decided for its agent, asked before the claim', async () => {
    const { made, fake, environmentsAsked } = await sessions()

    await made.handOver(ROOT, 'FX1')

    expect(fake.envs).toEqual([DECIDED])
    // Asked of the agent that resolved, from the project, and with nothing taken yet.
    expect(environmentsAsked).toEqual([{ agent: 'node claude.mjs', root: ROOT, claimsBefore: 0 }])
  })

  it('decides the environment once, and never for a machine with no Claude Code', async () => {
    const found = await sessions()
    await found.made.handOver(ROOT, 'FX1')
    await found.made.handOver(ROOT, 'FX1')
    expect(found.environmentsAsked).toHaveLength(1)

    const missing = await sessions({ kind: 'unresolved', reason: 'none', tried: [] })
    await missing.made.handOver(ROOT, 'FX1')
    expect(missing.environmentsAsked).toEqual([])
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

  it('says when the process was spawned, which an edited file is read against (RG244)', async () => {
    const { made } = await sessions()

    const handed = await made.handOver(ROOT, 'FX1')

    expect(handed.kind === 'started' && handed.session.started).toBe(SPAWNED.toISOString())
    expect(made.list()[0]?.started).toBe(SPAWNED.toISOString())
  })

  it('answers the root a session runs in by its key, and nothing for a key it never issued', async () => {
    // The root a question about its files is asked under is this, never a page's (RG244).
    const { made } = await sessions()
    await made.handOver(ROOT, 'FX1')

    expect(made.rootOf('session-1')).toBe(ROOT)
    expect(made.rootOf('nobody')).toBeNull()
  })

  it('keeps what moved on disk while it ran, folded, and tells it in bursts (RG247)', async () => {
    const { made, watch, published } = await sessions()
    await made.handOver(ROOT, 'FX1')

    // The root is watched from the spawn, and one burst is one event whatever it touched.
    expect(watch.roots).toEqual([ROOT])
    watch.move('src/a.ts', SPAWNED.toISOString())
    watch.move('src/b.ts', SPAWNED.toISOString())
    watch.move('node_modules/pkg/index.js', SPAWNED.toISOString())
    expect(published.filter((one) => 'moved' in one)).toEqual([])

    watch.tick()

    const told = published.find((one) => 'moved' in one)
    expect(told && 'moved' in told ? told.moved.map((one) => one.path) : []).toEqual([
      'src/a.ts',
      'src/b.ts',
    ])
    expect(made.list()[0]?.moved.map((one) => one.path)).toEqual(['src/a.ts', 'src/b.ts'])
    expect(made.list()[0]?.movedBeyond).toBe(0)
  })

  it('gives the watch back when the session ends, and tells what it saw once more', async () => {
    const { made, fake, watch, published } = await sessions()
    await made.handOver(ROOT, 'FX1')
    watch.move('src/a.ts', SPAWNED.toISOString())

    fake.end(DONE)
    await Promise.resolve()

    expect(watch.stopped).toEqual([ROOT])
    // The held burst was not left pending: the list is told before the ending is.
    expect(watch.pending).toBe(0)
    const kinds = published.map((one) =>
      'moved' in one ? 'moved' : 'outcome' in one ? 'end' : 'line',
    )
    expect(kinds).toEqual(['moved', 'end'])
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

describe('RG263: a gate finding handed to a session', () => {
  it('starts one from the finding the door belongs to, and runs no claim', async () => {
    const { made, fake, doors, claims } = await sessions()
    const offered = await doors.keep(ROOT, GATED)
    if (offered === null) throw new Error('the answer carried no doors')

    // Place 1: the note's door is first in the document, the finding's second.
    const handed = await made.handOverDoor(ROOT, offered, 1)

    expect(handed.kind).toBe('started')
    if (handed.kind !== 'started') return
    const told = handed.session.handed
    if (told.kind !== 'finding') throw new Error('a finding was handed over, not a line')
    expect(told.finding.code).toBe('ref.dangling')
    expect(told.finding.where).toBe('docs/IMPROVEMENTS.md:392')
    expect(told.argv).toEqual(['section', 'amend', 'T50', '--body', '-', '--role', 'improvements'])
    // A finding is not a line: nothing was claimed and no id names it.
    expect(claims()).toEqual([])
    expect(handed.session.id).toBe('')

    // The prompt carries the finding and the command, and the agent is told to run that one.
    const prompt = fake.calls[0]?.argv.find((part) => part.includes('ref.dangling'))
    expect(prompt).toBeDefined()
    expect(prompt).toContain('section amend T50 --body - --role improvements')
    expect(prompt).toContain('standard input')
  })

  it('refuses a batch the keep no longer holds, and starts nothing', async () => {
    const { made, fake } = await sessions()

    const handed = await made.handOverDoor(ROOT, 'never-offered', 0)

    expect(handed.kind).toBe('withheld')
    expect(fake.calls).toEqual([])
  })

  it('refuses a door no finding offered, rather than starting on a bare command line', async () => {
    const { made, fake, doors } = await sessions()
    const offered = await doors.keep(ROOT, GATED)
    if (offered === null) throw new Error('the answer carried no doors')

    // Place 0 is the note's. A note is not a finding, and a session handed only `install`
    // would be an agent told to run something with nothing said about why.
    const handed = await made.handOverDoor(ROOT, offered, 0)

    expect(handed.kind).toBe('withheld')
    expect(fake.calls).toEqual([])
  })
})
