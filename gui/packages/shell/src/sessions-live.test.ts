import path from 'node:path'

import {
  bridgedRun,
  listedTasks,
  openedFrom,
  openProject,
  type AgentResolution,
  type OpenedProject,
  type TopicEvents,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { fakeClaude, type FakeClaude } from './fake-claude'
import { buildFixture, type Fixture } from './fixture'
import { liveEngine, read, CEILING, LAUNCHER } from './live'
import { createSessions, type Sessions } from './sessions'

/**
 * RG153: a handover against a real backlog, with a `claude` that is not Claude.
 *
 * The line is taken for real — `brief --claim` writes the fixture's roadmap — and the process
 * that starts is the fake script the session suite uses, so nothing costs money and nothing
 * does work. What this holds over the unit test is the wiring: the claim is a write the engine
 * accepted, the payload the session is handed is the one it answered, and the lines the
 * process writes arrive as published events.
 */

let fixture: Fixture
let fake: FakeClaude
let sessions: Sessions
let published: TopicEvents['session'][] = []
let opened: OpenedProject
let first = ''

beforeAll(async () => {
  fixture = await buildFixture(liveEngine, { open: 2, shipped: 0, deferred: 0 })
  fake = fakeClaude()
  opened = openedFrom(
    await openProject(fixture.root, [['python', LAUNCHER]], () => liveEngine, {
      timeoutMs: CEILING,
    }),
  )
  first = listedTasks(await read(fixture.root, 'list', {}))[0]?.id ?? ''

  const agent: AgentResolution = {
    kind: 'resolved',
    agent: {
      command: [fake.command, ...fake.prefixArgs],
      version: '2.1.263',
      said: '2.1.263 (Claude Code)',
    },
  }
  published = []
  sessions = createSessions({
    carrier: {
      open: () => Promise.resolve(opened),
      run: (root, request) =>
        bridgedRun(() => liveEngine.run({ ...request, root, timeoutMs: CEILING })),
    },
    agent: () => Promise.resolve(agent),
    publish: (event) => published.push(event),
  })
}, 180000)

afterAll(async () => {
  await sessions.close()
  fake.dispose()
  fixture.dispose()
})

describe('RG153: a line handed over for real', () => {
  it('takes the line, starts from the payload the engine answered, and streams it', async () => {
    expect(first).not.toBe('')
    const handed = await sessions.handOver(fixture.root, first)

    expect(handed.kind).toBe('started')
    if (handed.kind !== 'started') throw new Error('unreachable')
    // The claim is a write the engine accepted: the marker moved in the same call.
    expect(handed.session.handed.claimed?.taken).toBe(true)
    expect(handed.session.handed.id).toBe(first)

    const outcome = await new Promise<TopicEvents['session']>((resolve) => {
      const wait = setInterval(() => {
        const ending = published.find((event) => 'outcome' in event)
        if (ending !== undefined) {
          clearInterval(wait)
          resolve(ending)
        }
      }, 50)
    })
    if (!('outcome' in outcome)) throw new Error('unreachable')
    expect(outcome.outcome.state).toBe('done')

    // Every line the process wrote, in order, and kept for a screen that opens late.
    const lines = published.filter((event) => 'line' in event)
    expect(lines.length).toBeGreaterThan(0)
    const record = sessions.list().find((one) => one.key === handed.session.key)
    expect(record?.lines).toHaveLength(lines.length)
    expect(record?.lines[0]).toContain('"type":"system"')
    // It ran where it was told to, which is what makes the project's own wiring answer.
    expect(path.resolve(JSON.parse(record?.lines[0] ?? '{}').cwd as string)).toBe(
      path.resolve(fixture.root),
    )
  }, 120000)

  it('starts no second session on a line whose claim is still live', async () => {
    // The two-sessions case, and the engine is what answers it: a claim is an expiry nothing
    // re-dates, so a second `--claim` is refused and its sentence is what the screen shows.
    // `held` names a holder where the registry has one; here the claim names nobody, and the
    // refusal is the whole answer.
    const running = sessions.list().length
    const again = await sessions.handOver(fixture.root, first)

    expect(again.kind).toBe('refused')
    if (again.kind !== 'refused') throw new Error('unreachable')
    expect(again.said).toContain(first)
    expect(sessions.list()).toHaveLength(running)
  }, 120000)
})
