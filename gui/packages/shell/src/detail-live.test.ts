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
/**
 * A second fixture, whose one line is taken before anything reads it.
 *
 * Separate from `fixture` on purpose: taking a line is a write, and a claim in the shared
 * project would change what `pick` answers for every test after it — which is an ordering
 * dependence nothing in the file would say out loud.
 */
let taken: Fixture
/**
 * Whatever this repository has open right now, chosen by `pick` rather than written here.
 *
 * An id in an assertion is a marker pinned to the day it was written: the test below that
 * read `RG23` asserted it was in progress, and it was, until the commit that shipped RG23
 * turned that into a failure nothing had changed to cause. `pick` always answers with an
 * open line, and an open line in this backlog always has a design.
 */
let open: TaskDetail

async function detailOf(root: string, id?: string): Promise<TaskDetail> {
  const result = await client.call(root, 'brief', id === undefined ? {} : { id }, {
    timeoutMs: CEILING,
  })
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

/**
 * Move a fixture line to the working marker with the engine's own `--claim`.
 *
 * Straight down the transport rather than through the client: the client publishes the
 * read-only verbs, and a write here belongs to the fixture and not to the app.
 */
async function takeInFixture(root: string, id: string): Promise<void> {
  const result = await engine.run({
    root,
    argv: ['-C', root, 'brief', id, '--claim', '--json'],
    timeoutMs: CEILING,
  })
  if (result.code !== 0) {
    throw new Error(`claiming ${id} failed (exit ${String(result.code)})\n${result.stderr}`)
  }
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 1 })
  taken = await buildFixture(engine, { open: 1, shipped: 0, deferred: 0 })
  open = await detailOf(REPO)
}, 240000)

afterAll(() => {
  fixture.dispose()
  taken.dispose()
})

describe('RG23: a real task, in one read', () => {
  it('opens a line with its design, its deps and what it unblocks', async () => {
    expect(open.payload.id).toMatch(/^RG\d+$/)
    expect(open.payload.symptom).not.toBe('')
    expect(open.hasDesign).toBe(true)
    expect(designOf(open)?.length).toBeGreaterThan(50)
    expect(open.payload.unblocks).not.toBeNull()
  })

  it('carries the non-goals and the criteria that bind it', () => {
    // Ten non-goals and the block's criteria, off one call.
    expect(open.payload.nonGoals.length).toBeGreaterThan(5)
    expect(open.payload.doneWhen.length).toBeGreaterThan(0)
  })

  it('resolves each dep to a state rather than an id to go and look up', async () => {
    // A line with no deps resolves nothing, so this asks for one that has them.
    const detail = await detailOf(REPO, 'RG9')

    expect(detail.payload.depsResolved.length).toBeGreaterThan(0)
    expect(detail.payload.depsResolved.every((dep) => dep.status !== '')).toBe(true)
  })

  it('takes readiness from the engine, and it is a word the engine chose', () => {
    expect(open.payload.readiness).not.toBe('')
    expect(['ready', 'waiting', 'blocked']).toContain(open.payload.readiness)
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
    // A marker is not a claim: `held` is the claim registry and it stays empty, and work
    // already in progress is the tier `pick` reaches for first — so in-progress makes a
    // line more startable, not less.
    //
    // The state is made here rather than found. Reading it off this repository meant
    // naming the id that happened to be in progress, and the commit that shipped that id
    // failed a test nothing had changed to break.
    const before = await detailOf(taken.root, 'FX1')
    await takeInFixture(taken.root, 'FX1')
    const after = await detailOf(taken.root, 'FX1')

    expect(after.payload.status).not.toBe(before.payload.status)
    expect(after.payload.held).toEqual([])
    expect(after.startable).toBe(true)
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
