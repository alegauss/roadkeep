import path from 'node:path'

import {
  createClient,
  designOf,
  detailFrom,
  readBriefPayload,
  readPayload,
  whyNotStartable,
  type TaskDetail,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The detail read against real backlogs. This repository is the interesting one: it has
 * shipped deps, blocked lines, deps outside the backlog and a claim held by this very
 * session, which between them cover every state the screen has to draw.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function detailOf(root: string, id?: string): Promise<TaskDetail> {
  const result = await client.call(
    root,
    'brief',
    id === undefined ? {} : { id },
    { timeoutMs: CEILING },
  )
  const parsed = readPayload(readBriefPayload, result.stdout, {
    verb: 'brief',
    engineVersion: '',
  })
  if (!parsed.ok) {
    throw new Error(
      `brief did not read: expected ${parsed.failure.expected} at ` +
        `${parsed.failure.path || '(the answer)'}, found ${parsed.failure.got}`,
    )
  }
  return detailFrom(parsed.value)
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 1 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG23: a real task, in one read', () => {
  it('opens a line with its design, its deps and what it unblocks', async () => {
    const detail = await detailOf(REPO, 'RG24')

    expect(detail.payload.id).toBe('RG24')
    expect(detail.payload.symptom).not.toBe('')
    expect(detail.hasDesign).toBe(true)
    expect(designOf(detail)?.length).toBeGreaterThan(50)
    expect(detail.payload.unblocks).not.toBeNull()
  })

  it('carries the non-goals and the criteria that bind it', async () => {
    const detail = await detailOf(REPO, 'RG24')

    // Ten non-goals and the block's criteria, off one call.
    expect(detail.payload.nonGoals.length).toBeGreaterThan(5)
    expect(detail.payload.doneWhen.length).toBeGreaterThan(0)
  })

  it('resolves each dep to a state rather than an id to go and look up', async () => {
    const detail = await detailOf(REPO, 'RG24')

    expect(detail.payload.depsResolved.length).toBeGreaterThan(0)
    expect(detail.payload.depsResolved.every((dep) => dep.status !== '')).toBe(true)
  })

  it('takes readiness from the engine, and it is a word the engine chose', async () => {
    const detail = await detailOf(REPO, 'RG24')

    expect(detail.payload.readiness).not.toBe('')
    expect(['ready', 'waiting', 'blocked']).toContain(detail.payload.readiness)
  })

  it('reads a line blocked on work outside this backlog', async () => {
    // RG9 waits on `roadkeep RK1632`, which shipping here can never unblock. The engine
    // knows that and this app must not try to work it out.
    const detail = await detailOf(REPO, 'RG9')

    expect(detail.startable).toBe(false)
    expect(detail.blocking.some((dep) => dep.includes('roadkeep'))).toBe(true)
    expect(whyNotStartable(detail)).toContain('waiting on')
  })

  it('reads a line already in progress, which is the first tier and not a blocker', async () => {
    // RG23 is 🛠 while this runs. A marker is not a claim: `held` is the claim registry
    // and it is empty, and work already in progress is the tier `pick` reaches for first
    // — so in-progress makes a line more startable, not less.
    const detail = await detailOf(REPO, 'RG23')

    expect(detail.payload.status).toBe('🛠')
    expect(detail.payload.held).toEqual([])
    expect(detail.startable).toBe(true)
  })

  it('reads a shipped line, whose design was deleted with it', async () => {
    const detail = await detailOf(REPO, 'RG21')

    expect(detail.hasDesign).toBe(false)
    expect(designOf(detail)).toBeNull()
  })
})

describe('RG23: briefing whatever pick would choose', () => {
  it('answers without being told an id, and says why that line', async () => {
    const detail = await detailOf(fixture.root)

    expect(detail.payload.id).toMatch(/^FX\d+$/)
    // There was a choice here, so there is a reason for it.
    expect(detail.payload.picked).not.toBeNull()
    expect(detail.payload.picked).not.toBe('')
  })

  it('explains nothing when the caller named the id, because nothing was chosen', async () => {
    expect((await detailOf(fixture.root, 'FX1')).payload.picked).toBeNull()
  })

  it('is startable on a fixture with nothing blocking it', async () => {
    const detail = await detailOf(fixture.root)

    expect(detail.payload.readiness).toBe('ready')
    expect(detail.startable).toBe(true)
    expect(whyNotStartable(detail)).toBe('')
  })
})
