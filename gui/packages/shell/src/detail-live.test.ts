import {
  designOf,
  detailFrom,
  graphOfBrief,
  listedTasks,
  routeOf,
  whyNotStartable,
  type TaskDetail,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { aLine, CEILING, liveEngine as engine, openWithDesign, read, REPO } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * The detail read against real backlogs. This repository is the interesting one: it has
 * shipped deps, blocked lines, deps outside the backlog and a claim held by this very
 * session, which between them cover every state the screen has to draw.
 */
/** The engine's word for a dep nothing shipped in this backlog will ever satisfy. */
const UNRESOLVABLE = 'unresolvable'

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
 * An open line this repository has designed, found off the listing rather than written here.
 *
 * An id in an assertion is a marker pinned to the day it was written: the test below that
 * read `RG23` asserted it was in progress, and it was, until the commit that shipped RG23
 * turned that into a failure nothing had changed to cause. This was chosen by `pick` after
 * that, until the day nothing here was ready and pick chose nothing (RG141).
 */
let open: TaskDetail
/**
 * A line whose deps the engine resolved, and one waiting on work outside this backlog.
 *
 * Found rather than written down, for the reason above: both of these were read off an id
 * named here, and an id is a claim about today. What each test is about is the state — a
 * dep carrying a status, a dep no ship here can ever clear — so the state is what locates
 * the line, and which id happens to be in it is never asserted.
 */
let withDeps: TaskDetail
let outside: TaskDetail

async function detailOf(root: string, id?: string): Promise<TaskDetail> {
  return detailFrom(aLine(await read(root, 'brief', id === undefined ? {} : { id })))
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

/**
 * Brief the lines that have deps at all, until both states above are in hand.
 *
 * The listing is the cheap half: it says which ids carry a dep without saying anything
 * about what the dep resolves to, and most of this backlog carries none — so the briefs,
 * which each cost an interpreter start, run over a handful of lines rather than over all
 * of them. Only `brief` can answer the second question, since `unresolvable` is the
 * engine's verdict and reading it off the dep's text would be this app resolving deps.
 */
async function findStates(): Promise<void> {
  let resolved: TaskDetail | undefined
  let never: TaskDetail | undefined
  for (const task of listedTasks(await read(REPO, 'list', {}))) {
    if (task.deps.length === 0) continue
    const detail = await detailOf(REPO, task.id)
    if (detail.payload.depsResolved.length === 0) continue
    resolved ??= detail
    if (detail.payload.depsResolved.some((dep) => dep.status === UNRESOLVABLE)) never ??= detail
    if (never !== undefined) break
  }

  // The premise of this file, stated where it fails. A backlog that stopped carrying one
  // of these has not broken the app; it has taken away what these two tests read.
  if (resolved === undefined) throw new Error('no line in this backlog has a dep to resolve')
  if (never === undefined) throw new Error('no line in this backlog waits on work outside it')
  withDeps = resolved
  outside = never
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 3, shipped: 1, deferred: 1 })
  taken = await buildFixture(engine, { open: 1, shipped: 0, deferred: 0 })
  open = await detailOf(REPO, await openWithDesign())
  await findStates()
}, 240000)

afterAll(() => {
  fixture.dispose()
  taken.dispose()
})

describe('RG23: a real task, in one read', () => {
  it('opens a line with its design, its deps and what it unblocks', () => {
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

  it('resolves each dep to a state rather than an id to go and look up', () => {
    // A line with no deps resolves nothing, so the subject is one the listing said has
    // them — which line that is has never been what this asserts.
    expect(withDeps.payload.depsResolved.length).toBeGreaterThan(0)
    expect(withDeps.payload.depsResolved.every((dep) => dep.status !== '')).toBe(true)
  })

  it('takes readiness from the engine, and it is a word the engine chose', () => {
    // A word and not a sentence — and not a word from a list kept here. This held three until
    // RG141 moved the subject off `pick`, which only ever handed it a ready line: the first
    // open line read otherwise said `blocked-outside`, a word this test had never been shown.
    expect(open.payload.readiness).toMatch(/^[a-z]+(-[a-z]+)*$/)
  })

  it('reads a line blocked on work outside this backlog', () => {
    // Some line here waits on a task in another repository, which shipping in this one can
    // never unblock. The engine knows that and this app must not try to work it out — so
    // the dep is named by the verdict it came back with, not by the project it points into.
    const never = outside.payload.depsResolved.find((dep) => dep.status === UNRESOLVABLE)

    expect(outside.startable).toBe(false)
    expect(outside.blocking).toContain(never?.dep)
    expect(whyNotStartable(outside)).toContain('waiting on')
  })

  it('draws that line chain off the brief, with no second call for it', () => {
    // RG76: a real `brief` sends the routes already resolved, so opening a blocked task
    // costs one subprocess and not two. What it does not send is the blockers as a list
    // and the cycle, and the graph says which rather than answering an empty bracket.
    const graph = graphOfBrief(outside.payload)

    expect(graph.chains.length).toBeGreaterThan(0)
    expect(routeOf(graph.chains[0]!)).toContain(outside.payload.id)
    expect(graph.chains.some((chain) => chain.standing === 'never')).toBe(true)
    expect(graph.narrowing.complete).toBe(false)
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
