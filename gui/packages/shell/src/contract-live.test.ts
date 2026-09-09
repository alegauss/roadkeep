import {
  listedTasks,
  VERBS,
  WRITES,
  applyWrite,
  composeWrite,
  fieldsRefused,
  flagsFor,
  narrowingOfBrief,
  narrowingOfList,
  narrowingOfStats,
  readAddedPayload,
  readAmendPayload,
  readAnswer,
  buildArgv,
  capabilitiesOf,
  readDeferPayload,
  readListPayload,
  readRepairPayload,
  readRenumberPayload,
  readRestatePayload,
  readResumePayload,
  readRetirePayload,
  readSectionWritten,
  readShipPayload,
  readStatusPayload,
  resolveEngine,
  withheld,
  type VerbAnswers,
  type VerbInputs,
  type VerbName,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveClient as client, liveEngine as transport, read, REPO } from './live'
import { engineCandidates, samePathPart } from './engine-candidates'
import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * RG4: where a rename is allowed to go red.
 *
 * roadkeep holds its own editor client under `tests/test_editor.py`, in its tree, so a
 * renamed key fails there before it reaches a reader written in another language. This app
 * is a second client in another language and that test does not cover it — so without this
 * file the same rename reaches somebody's window instead of a build.
 *
 * What is asserted is the *shape* and never the values. The values belong to a fixture
 * this test builds with the real write verbs; the shape belongs to the engine, and it is
 * the shape that can move underneath this app.
 *
 * A green run here is a claim about one build of roadkeep and never about roadkeep in
 * general, which is why the version that answered is asserted to exist and carried into
 * every failure this file prints.
 *
 * **What it does not assert is that two reads agree on it.** The engine here is often a
 * working checkout somebody is editing, so a version read in `beforeAll` and a version
 * read forty calls later are two samples of a moving number — this suite failed twice in
 * one afternoon on `expected '0.2.385' to be '0.2.384'` with nothing changed, while every
 * shape assertion beside them passed. That failure is indistinguishable from the one this
 * file exists to produce, and a reader who learns red can also mean "somebody rebuilt the
 * engine" is a reader who stops believing it. RG75 was the same shape with a task id in
 * place of a version: an assertion that the world has not moved, which is not what either
 * test was written to check.
 */

/**
 * Every call known to make a verb answer in a shape its ordinary call does not.
 *
 * RG66 gave each verb one shape; this is the half that fix does not reach. A single reader
 * still has to handle both answers, and nothing made anybody notice there were two — every
 * entry below was found by hand at the moment it broke something. `ship --part` cost a red
 * live test and a shape rewrite, because a reader taking only `removed` drew a partial ship
 * as a closure.
 *
 * The pattern is exact and it is why a list is worth keeping: **the flag that narrows a
 * read, or changes what a write does, is the flag that changes the answer** — and it is
 * never the call anybody writes the first test for.
 *
 * So they are declared here and `covers` marks each one off as its case runs. A shape
 * somebody names without covering reds the guard at the foot of this file, which turns a
 * reader that works until the day a person clicks the other button into a gap in a list.
 */
const SECOND_SHAPES = {
  'show --no-body': '`section.body`: the prose on the ordinary call, null under the flag',
  'criterion list --task': '`empty` and `doors`, which the block form answers with neither',
  'delivered --near': '`near`: null unranked, and the sentence it ranked against when given',
  'reversals <id>': '`asked`: null over the whole ledger, the id when one was named',
  'ship --part': '`roadmap`: a line removed on a closure, a line still open on a partial',
  'brief on a shipped line': '`budget`: an object while the design is there, null once it is gone',
} as const

type SecondShape = keyof typeof SECOND_SHAPES

const covered = new Set<SecondShape>()

/** Say that a case exercised one of them. */
function covers(shape: SecondShape): void {
  covered.add(shape)
}

let fixture: Fixture
let engineVersion = ''
/**
 * The first open line, listed once (RG68). Two `show` cases want an id and nothing else,
 * and each was fetching the whole listing to find one — a second and a half apiece for an
 * answer that does not change until the write cases further down start moving lines.
 */
let firstOpen = ''

beforeAll(async () => {
  fixture = await buildFixture(transport)

  const resolution = await resolveEngine(
    (engine) => createProcessTransport({ command: engine[0] ?? '', prefixArgs: engine.slice(1) }),
    REPO,
    engineCandidates(REPO),
    { timeoutMs: CEILING, samePart: samePathPart },
  )
  if (resolution.kind === 'resolved') {
    engineVersion = resolution.engine.payload.writing.version
  }

  firstOpen = listedTasks(await readVerb('list', {}))[0]?.id ?? ''
}, 180000)

afterAll(() => {
  fixture.dispose()
})

/**
 * Read one verb's answer off the fixture, failing with the sentence a user would see.
 *
 * The shape is no longer passed in: the verb carries its own (RG66), so a case here that
 * asked for `pick` and held it against `list`'s shape is a case that cannot be written.
 */
async function readVerb<K extends VerbName>(
  verb: K,
  input: VerbInputs[K],
): Promise<VerbAnswers[K]> {
  // The seam is `live.ts`, and the version is what this file adds to it: the message a
  // moved key prints names the build that moved it, and this is the one file that has
  // resolved which build answered.
  return read(fixture.root, verb, input, { engineVersion })
}

describe('RG4: the build this contract was proven against', () => {
  it('names a version, so a green suite is a claim about one engine', () => {
    // Named once and never compared again. It reaches a reader through `explainFailure`,
    // which puts it in the sentence every failed read in this file prints — which is what
    // "a claim about one build" needs, and equality between two samples never was.
    expect(engineVersion).toMatch(/^\d+\.\d+\.\d+/)
  })
})

describe('RG4: every read this client makes, against a live engine', () => {
  it('covers every verb the client can build a command line for', () => {
    // The guard that keeps this file honest. A verb with no shape is now a compile error
    // (RG66); what this still catches is a verb added to both tables and never called
    // against a live engine, which is a shape nothing has held against a real payload.
    expect(Object.keys(VERBS).sort()).toEqual(
      [
        'brief',
        'budget',
        'commands',
        'config',
        'criterionList',
        'delivered',
        'deps',
        'engines',
        'explain',
        'lint',
        'list',
        'nonGoalList',
        'pick',
        'reversals',
        'show',
        'stats',
      ].sort(),
    )
  })

  it('covers every write this client can build a command line for', () => {
    // The same guard as above, for the other table. A write verb added without a shape
    // and without a case here is a door offered against an answer nobody has read.
    expect(Object.keys(WRITES).sort()).toEqual(
      [
        'add',
        'amend',
        'defer',
        'renumber',
        'repair',
        'restate',
        'resume',
        'retire',
        'sectionAdd',
        'sectionAmend',
        'ship',
        'status',
      ].sort(),
    )
  })

  it('reads a listing, with its standing and its lines', async () => {
    const payload = await readVerb('list', {})

    expect(payload.file).toContain('ROADMAP.md')
    expect(listedTasks(payload).length).toBeGreaterThan(0)
    // Shape, not values: what matters is that every declared key was there and typed.
    expect(typeof listedTasks(payload)[0]?.symptom).toBe('string')
    expect(Array.isArray(listedTasks(payload)[0]?.deps)).toBe(true)
    expect(narrowingOfList(payload).complete).toBe(true)
  })

  it('reads a listing narrowed to one block', async () => {
    const payload = await readVerb('list', { block: 'A' })

    expect(payload.standing?.block).toBe('A')
  })

  it('reads a listing of another governed role', async () => {
    // `--role changelog` is a different file with the same shape, and the fixture has a
    // shipped line so it is not empty.
    const payload = await readVerb('list', { role: 'changelog' })

    expect(payload.file).toContain('CHANGELOG.md')
    expect(listedTasks(payload).length).toBeGreaterThan(0)
  })

  it('reads the counts, keyed by the marker set the fixture declared', async () => {
    const payload = await readVerb('stats', {})

    expect(payload.total).toBeGreaterThan(0)
    expect(Object.keys(payload.markers).length).toBeGreaterThan(0)
    expect(payload.blocks.length).toBeGreaterThan(0)
    expect(narrowingOfStats(payload).complete).toBe(true)
  })

  it('reads one task with the rationale its pointer resolves to', async () => {
    expect(firstOpen).not.toBe('')

    const payload = await readVerb('show', { id: firstOpen })

    expect(payload.id).toBe(firstOpen)
    expect(payload.section?.body).not.toBe('')
    expect(payload.section?.words).toBeGreaterThan(0)
  })

  it('reads a task with its prose left out, which is a different answer', async () => {
    const payload = await readVerb('show', { id: firstOpen, noBody: true })

    // The section is still there and still located; only the prose is gone, and it comes
    // back null rather than empty. A shape demanding a string failed on exactly this flag,
    // which is the finding this file was written to produce.
    expect(payload.section?.file).toContain('IMPROVEMENTS.md')
    expect(payload.section?.body).toBeNull()
    covers('show --no-body')
  })

  it('reads a brief, including what it left out', async () => {
    const payload = await readVerb('brief', {})

    expect(payload.id).not.toBe('')
    expect(payload.readiness).not.toBe('')
    expect(payload.nonGoals.length).toBeGreaterThan(0)
    expect(payload.doneWhen.length).toBeGreaterThan(0)
    // Shape over values, as with `deps` below: this fixture's line has no chain, and a key
    // that only exists on blocked lines is the one a shape stops declaring.
    expect(Array.isArray(payload.chains)).toBe(true)
    // The elision counts are read whether or not this fixture elides anything: a client
    // that never looked would draw a sample as though it were the set.
    expect(narrowingOfBrief(payload)).toHaveProperty('complete')
  })

  it('reads one line edges, resolved', async () => {
    const payload = await readVerb('deps', { id: 'FX3' })

    expect(payload.id).toBe('FX3')
    expect(payload.readiness).not.toBe('')
    // Shape over values. The fixture has no chain and no cycle, and a reader that only
    // worked on the populated case is the one that breaks on an ordinary line.
    expect(Array.isArray(payload.deps)).toBe(true)
    expect(Array.isArray(payload.blockers)).toBe(true)
    expect(Array.isArray(payload.chains)).toBe(true)
    expect(Array.isArray(payload.cycle)).toBe(true)
    expect(typeof payload.unblocks?.of).toBe('number')
    expect(Array.isArray(payload.unblocks?.direct)).toBe(true)
  })

  it('reads the two lists that bind a proposal, both two-word verbs', async () => {
    // The only verbs whose name is two words. The name is kept whole because that is the
    // string `commands` publishes, and `buildArgv` is what splits it.
    const bounds = await readVerb('nonGoalList', {})
    const finishing = await readVerb('criterionList', {})

    expect(bounds.governed).toBe(true)
    expect(bounds.nonGoals.length).toBeGreaterThan(0)
    expect(typeof bounds.nonGoalsQuoted).toBe('object')

    expect(finishing.governed).toBe(true)
    expect(finishing.blocks.length).toBeGreaterThan(0)
    expect(finishing.criteria[0]?.lead).not.toBe('')
    expect(typeof finishing.criteria[0]?.shaped).toBe('boolean')
  })

  it('reads an address with no list, and the door that opens one', async () => {
    // `empty` is the engine's word for which nothing this is, and it is null on an answer
    // that is not empty — a shape demanding a string fails on every ordinary read.
    const finishing = await readVerb('criterionList', { task: 'FX1' })

    expect(finishing.criteria).toEqual([])
    expect(finishing.empty).not.toBeNull()
    expect(finishing.doors.length).toBeGreaterThan(0)
    expect(finishing.doors[0]?.argv.length).toBeGreaterThan(0)
    covers('criterion list --task')
  })

  it('reads what a block already delivered, ranked and unranked', async () => {
    const whole = await readVerb('delivered', { block: 'A' })
    const near = await readVerb('delivered', { block: 'A', near: 'nothing answers a question yet' })

    expect(whole.block).toBe('A')
    expect(whole.file).toContain('CHANGELOG.md')
    // `near` is null on the unranked read and the sentence on the ranked one — a shape
    // demanding a string fails on the ordinary call.
    expect(whole.near).toBeNull()
    expect(near.near).not.toBeNull()
    expect(whole.delivered[0]?.symptom).not.toBe('')
    expect(whole.delivered[0]?.undoneBy).toBeNull()
    covers('delivered --near')
  })

  it('reads what the ledger undid, and the id a caller asked about', async () => {
    const all = await readVerb('reversals', {})
    const one = await readVerb('reversals', { id: 'FX1' })

    expect(all.root).not.toBe('')
    expect(all.asked).toBeNull()
    expect(one.asked).toBe('FX1')
    expect(Array.isArray(one.reversed)).toBe(true)
    covers('reversals <id>')
  })

  it('writes a line, and reads back the shape the write answered with', async () => {
    // The one case in this file that changes a file, and it changes the fixture's.
    const outcome = await applyWrite(
      transport,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'the contract has not written anything yet',
        why: 'A write answers with a shape too, and nothing here has read it.',
        section: 'What a write answers with',
        sectionBody: 'Prose enough to be a rationale and well inside the declared budget.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.id).not.toBe('')
    expect(outcome.value.file).toContain('ROADMAP.md')
    expect(typeof outcome.value.length).toBe('number')
    expect(outcome.value.section?.anchor).toBe(outcome.value.id)
    expect(Array.isArray(outcome.value.near)).toBe(true)
  })

  it('moves a marker, and says what the claim did', async () => {
    const listed = await readVerb('list', {})
    const first = listedTasks(listed)[0]
    if (!first) return

    const outcome = await applyWrite(
      transport,
      composeWrite(fixture.root, 'status', { id: first.id, marker: first.status }),
      readStatusPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    // Its own marker, so `changed` is false — the shape of a no-op, which is the answer a
    // shape demanding `changed` true would never see.
    expect(outcome.value.id).toBe(first.id)
    expect(outcome.value.changed).toBe(false)
    expect(outcome.value.to).toBe(first.status)
    expect(Array.isArray(outcome.value.refreshed)).toBe(true)
    expect(Array.isArray(outcome.value.wrote)).toBe(true)
  })

  it('closes a line four ways, and reads the shape each answers with', async () => {
    // One fixture line per departure. Every one is irreversible in the direction that
    // matters, which is why this runs nowhere but here.
    const open = listedTasks(await readVerb('list', {})).map((task) => task.id)
    const [first, second, third] = open.slice(-3)
    if (first === undefined || second === undefined || third === undefined) return

    const ship = await applyWrite(
      transport,
      composeWrite(fixture.root, 'ship', { id: first, why: 'It answers now.' }),
      readShipPayload,
      { timeoutMs: CEILING },
    )
    expect(ship.kind).toBe('applied')
    if (ship.kind !== 'applied') throw new Error('unreachable')
    expect(ship.value.roadmap?.file).toContain('ROADMAP.md')
    expect(typeof ship.value.roadmap?.open).toBe('boolean')
    expect(Array.isArray(ship.value.checked)).toBe(true)
    // The closure half of `ship --part`'s pair: the line left the roadmap, so `removed`
    // names where it was and `open` is false.
    expect(ship.value.roadmap?.removed).toBeGreaterThan(0)
    expect(ship.value.roadmap?.open).toBe(false)
    expect(ship.value.part).toBe('')

    const retire = await applyWrite(
      transport,
      composeWrite(fixture.root, 'retire', { id: second, reason: 'The premise went.' }),
      readRetirePayload,
      { timeoutMs: CEILING },
    )
    expect(retire.kind).toBe('applied')
    if (retire.kind !== 'applied') throw new Error('unreachable')
    expect(retire.value.marker).not.toBe('')
    expect(retire.value.supersededBy).toBeNull()

    const defer = await applyWrite(
      transport,
      composeWrite(fixture.root, 'defer', { id: third, reason: 'Waiting on a decision.' }),
      readDeferPayload,
      { timeoutMs: CEILING },
    )
    expect(defer.kind).toBe('applied')
    if (defer.kind !== 'applied') throw new Error('unreachable')
    expect(defer.value.deferred?.file).toContain('DEFERRED.md')

    const resume = await applyWrite(
      transport,
      composeWrite(fixture.root, 'resume', { id: third }),
      readResumePayload,
      { timeoutMs: CEILING },
    )
    expect(resume.kind).toBe('applied')
    if (resume.kind !== 'applied') throw new Error('unreachable')
    expect(resume.value.was).toBe('Waiting on a decision.')
    expect(resume.value.marker).not.toBe('')
  })

  it('records half a line, which answers about a line that is still there', async () => {
    // The second shape `ship` has, and the one that cost a shape rewrite: a partial writes
    // a ledger entry and leaves the task open, so `roadmap` is about where the line still
    // is rather than about a line that has gone.
    const filed = await applyWrite(
      transport,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'half of something lands before the rest of it does',
        why: 'A partial ship answers in a shape the ordinary one does not.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(filed.kind).toBe('applied')
    if (filed.kind !== 'applied') throw new Error('unreachable')

    const partial = await applyWrite(
      transport,
      composeWrite(fixture.root, 'ship', {
        id: filed.value.id,
        why: 'The local half answers now.',
        part: 'local half',
        remainder: 'The half that crosses a process is still to come.',
      }),
      readShipPayload,
      { timeoutMs: CEILING },
    )
    expect(partial.kind).toBe('applied')
    if (partial.kind !== 'applied') throw new Error('unreachable')

    // Nothing was taken out, and the three keys the closure form leaves at their defaults
    // are the ones a reader has to have looked for.
    expect(partial.value.part).not.toBe('')
    expect(partial.value.roadmap?.removed).toBe(0)
    expect(partial.value.roadmap?.line).toBeGreaterThan(0)
    expect(partial.value.roadmap?.status).not.toBe('')
    expect(partial.value.roadmap?.open).toBe(true)
    // And the line really is still a task, which is the claim `open` is making.
    expect(listedTasks(await readVerb('list', {})).map((task) => task.id)).toContain(filed.value.id)
    covers('ship --part')
  })

  it('briefs a shipped line, whose budget went with its design', async () => {
    // `budget` is an object while there is a design to price and null once shipping has
    // deleted it. A shape demanding the object reads every closed line as unreadable.
    const shipped = listedTasks(await readVerb('list', { role: 'changelog' }))[0]?.id ?? ''
    expect(shipped).not.toBe('')

    const closed = await readVerb('brief', { id: shipped })
    const open = await readVerb('brief', {})

    expect(closed.shipped).toBe(true)
    expect(closed.budget).toBeNull()
    expect(closed.section).toBeNull()
    expect(open.budget).not.toBeNull()
    covers('brief on a shipped line')
  })

  it('writes a rationale under an anchor, and corrects it as a fragment', async () => {
    const filed = await applyWrite(
      transport,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'the contract has written no rationale yet',
        why: 'A section write answers with a shape too, and nothing here has read it.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(filed.kind).toBe('applied')
    if (filed.kind !== 'applied') throw new Error('unreachable')

    const added = await applyWrite(
      transport,
      composeWrite(fixture.root, 'sectionAdd', {
        anchor: filed.value.id,
        title: 'What a section write answers with',
        body: 'A rationale long enough to be prose and well inside the declared budget.',
      }),
      readSectionWritten,
      { timeoutMs: CEILING },
    )
    expect(added.kind).toBe('applied')
    if (added.kind !== 'applied') throw new Error('unreachable')
    expect(added.value.anchor).toBe(filed.value.id)
    expect(added.value.file).toContain('IMPROVEMENTS.md')
    expect(added.value.words).toBeGreaterThan(0)
    // An add reports nothing changed; the key exists all the same.
    expect(added.value.changed).toEqual([])

    const amended = await applyWrite(
      transport,
      composeWrite(fixture.root, 'sectionAmend', {
        anchor: filed.value.id,
        fragment: { replace: 'long enough to be prose', replacement: 'written to be read' },
      }),
      readSectionWritten,
      { timeoutMs: CEILING },
    )
    expect(amended.kind).toBe('applied')
    if (amended.kind !== 'applied') throw new Error('unreachable')
    // The key that tells an amend from an add, and the one a shape without it would miss.
    expect(amended.value.changed).toContain('body')
    expect(typeof amended.value.readBody).toBe('boolean')
  })

  it('corrects a line three ways, and reads what each answers with', async () => {
    const open = listedTasks(await readVerb('list', {})).map((task) => task.id)
    const id = open.at(-1)
    if (id === undefined) return

    const amend = await applyWrite(
      transport,
      composeWrite(fixture.root, 'amend', { id, why: 'A corrected sentence, ending in a stop.' }),
      readAmendPayload,
      { timeoutMs: CEILING },
    )
    expect(amend.kind).toBe('applied')
    if (amend.kind !== 'applied') throw new Error('unreachable')
    // `was` is a map here. The same key is a string on `restate` below.
    expect(typeof amend.value.was).toBe('object')
    expect(amend.value.changed).toContain('why')

    const restate = await applyWrite(
      transport,
      composeWrite(fixture.root, 'restate', { id, symptom: 'the claim turned out to be false' }),
      readRestatePayload,
      { timeoutMs: CEILING },
    )
    expect(restate.kind).toBe('applied')
    if (restate.kind !== 'applied') throw new Error('unreachable')
    expect(typeof restate.value.was).toBe('string')
    expect(typeof restate.value.typo).toBe('boolean')
    expect(Array.isArray(restate.value.premise?.next ?? [])).toBe(true)

    const renumber = await applyWrite(
      transport,
      composeWrite(fixture.root, 'renumber', { id, to: 'FX95' }),
      readRenumberPayload,
      { timeoutMs: CEILING },
    )
    expect(renumber.kind).toBe('applied')
    if (renumber.kind !== 'applied') throw new Error('unreachable')
    expect(renumber.value.to).toBe('FX95')
    expect(Array.isArray(renumber.value.moved)).toBe(true)
    expect(typeof renumber.value.criteria).toBe('boolean')
  })

  it('prices a line that does not exist yet, and one that is about to ship', async () => {
    const line = await readVerb('budget', { block: 'A', symptom: 'a draft' })

    expect(line.id).not.toBe('')
    expect(line.lineMax).toBeGreaterThan(0)
    expect(line.fields.map((one) => one.field)).toContain('why')
    // `allowed` is the key a counter uses and `limit` is the one it must not.
    expect(typeof line.fields[0]?.allowed).toBe('number')
    expect(typeof line.fields[0]?.boundByLine).toBe('boolean')
    expect(line.ref).not.toBeNull()

    const listed = await readVerb('list', { role: 'changelog' })
    const shipped = listedTasks(listed)[0]
    if (shipped === undefined) return

    const ledger = await readVerb('budget', { id: shipped.id, ship: true })
    // A shipped line carries no pointer, so `ref` is null where the open form sends a
    // string — the second shape of this verb, and a reader demanding one fails here.
    expect(ledger.ref).toBeNull()
  })

  it('reads a brief that takes the line, whose claim is a second shape', async () => {
    // Its own line, because a claim is a write and the fixture's other ids are spoken for
    // — one is deferred, which `brief` refuses outright.
    const filed = await applyWrite(
      transport,
      composeWrite(fixture.root, 'add', {
        block: 'A',
        symptom: 'a line nothing has taken yet',
        why: 'A claim is a write, so this one is only for taking.',
      }),
      readAddedPayload,
      { timeoutMs: CEILING },
    )
    expect(filed.kind).toBe('applied')
    if (filed.kind !== 'applied') throw new Error('unreachable')
    const id = filed.value.id

    // `claimed` is null on a brief that only read and an object on one that took, which is
    // the same key answering two ways under a flag.
    const onlyRead = await readVerb('brief', { id })
    expect(onlyRead.claimed).toBeNull()

    const took = await readVerb('brief', { id, claim: true })
    expect(took.claimed).not.toBeNull()
    expect(typeof took.claimed?.taken).toBe('boolean')
    expect(took.claimed?.to).not.toBe('')
  })

  it('reads what to work on next, and which tier answered', async () => {
    const payload = await readVerb('pick', {})

    expect(payload.tier).not.toBe('')
    expect(payload.reason).not.toBe('')
    expect(typeof payload.ready).toBe('number')
    // The fixture has open lines, so there is something to pick.
    expect(payload.pick?.id).toMatch(/^FX\d+$/)
  })

  it('reads a backlog with nothing to pick as a null rather than a refusal', async () => {
    // Scoped to a block the fixture declares and has no open line in. `pick` answering
    // "nothing" is an answer, and a row drawing it as an error would be wrong.
    const payload = await readVerb('pick', { block: 'B', designed: true })

    expect(payload).toHaveProperty('pick')
  })

  it('reads the gate, whose non-zero exit is an answer', async () => {
    // The exit code is the transport's, and the point is that it does not decide: `lint`
    // exits 1 with an ordinary payload, so both have to be read off the same call.
    const raw = await transport.run({
      root: fixture.root,
      argv: buildArgv(fixture.root, 'lint', {}),
      timeoutMs: CEILING,
    })
    expect([0, 1]).toContain(raw.code)

    const payload = await readVerb('lint', {})
    expect(typeof payload.clean).toBe('boolean')
    expect(payload.checked.length).toBeGreaterThan(0)
  })

  it('reads a repair pass, whose dry run is a different answer', async () => {
    const dry = await applyWrite(
      transport,
      composeWrite(fixture.root, 'repair', { dryRun: true }),
      readRepairPayload,
      { timeoutMs: CEILING },
    )

    expect(dry.kind).toBe('applied')
    if (dry.kind !== 'applied') throw new Error('unreachable')
    // `dry_run` is the key that tells the two apart, and a shape without it would read a
    // rehearsal as a pass that ran.
    expect(dry.value.dryRun).toBe(true)
    expect(Array.isArray(dry.value.steps)).toBe(true)
    expect(Array.isArray(dry.value.left)).toBe(true)
    expect(typeof dry.value.exhausted).toBe('boolean')
  })

  it('reads which engine answered for the fixture', async () => {
    const payload = await readVerb('engines', {})

    // Every claim here is about this one call. What the read has to prove is that the
    // payload names a build and the copy it came from — not that the number matches one
    // sampled from another project, minutes earlier, off a tree under edit.
    expect(payload.writing.version).toMatch(/^\d+\.\d+\.\d+/)
    expect(payload.writing.home).not.toBe('')
    expect(payload.invoke).not.toBe('')
    // The verdict over the copies is the engine's own word, and it is carried whether or
    // not they agree: a machine with four copies in play is an ordinary machine.
    expect(payload.verdict).not.toBe('')
    expect(typeof payload.agree).toBe('boolean')
  })
})

describe('RG6: what the live build says it can do', () => {
  it('publishes every verb this app calls, with every flag it would send', async () => {
    const report = capabilitiesOf(await readVerb('commands', {}))

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return

    // The assertion that earns this read: not "commands parsed", but that the flags this
    // app composes are flags this build actually takes. A failure here names them.
    expect(withheld(report), withheld(report).join('\n')).toEqual([])
    expect(report.complete).toBe(true)
    // The build the report is about, named by the report itself. Both halves of that come
    // off this one `commands` call, which is what makes it a claim and not a stopwatch.
    expect(report.version).toMatch(/^\d+\.\d+\.\d+/)
  })

  it('agrees with the flags derived from this project’s own builders', async () => {
    const report = capabilitiesOf(await readVerb('commands', {}))
    if (report.kind !== 'known') return

    expect(report.byVerb.list.callable).toBe(true)
    expect(report.byVerb.list.writes).toBe(false)
    expect(flagsFor('list')).toContain('--marker')

    // The distinction this test exists to pin down: `stats` runs and is not on the MCP
    // tool surface. Reading `published` as "can I call it" withheld it, which is how the
    // live contract caught the wrong field being read.
    expect(report.byVerb.stats.callable).toBe(true)
    expect(report.byVerb.stats.onToolSurface).toBe(false)
  })
})

describe('RG5: a refusal, against a live engine', () => {
  it('names the field a real over-long symptom was refused on', async () => {
    // A write the engine refuses writes nothing, which is what makes this safe to run
    // against the fixture and what makes the refusal worth reading rather than avoiding.
    const result = await transport.run({
      root: fixture.root,
      argv: [
        '-C',
        fixture.root,
        'add',
        '--block',
        'A',
        '--symptom',
        'x'.repeat(200),
        '--why',
        'A reason that is fine.',
        '--json',
      ],
      timeoutMs: CEILING,
    })
    const parsed = readAnswer(readListPayload, result)

    expect(result.code).not.toBe(0)
    expect(parsed.ok).toBe(true)
    if (!parsed.ok || parsed.value.kind !== 'refused') {
      throw new Error(`expected a refusal, got ${result.stdout.slice(0, 120)}`)
    }

    expect(fieldsRefused(parsed.value.refusal)).toEqual(['symptom'])
    expect(parsed.value.refusal.refused[0]?.code).toBe('symptom.too-long')
  })

  it('marks nothing for a refusal the engine did not attach to a field', async () => {
    const parsed = await client.call(fixture.root, 'show', { id: 'FX999' }, { timeoutMs: CEILING })

    expect(parsed.ok).toBe(true)
    if (!parsed.ok || parsed.value.kind !== 'refused') {
      throw new Error('expected a refusal, got a payload')
    }
    expect(fieldsRefused(parsed.value.refusal)).toEqual([])
    expect(parsed.value.refusal.said).not.toBe('')
  })

  it('reads the doors that close the code a refusal named', async () => {
    const payload = await readVerb('explain', { code: 'symptom.too-long' })

    expect(payload.code).toBe('symptom.too-long')
    expect(payload.cause).not.toBe('')
    expect(payload.doors.length).toBeGreaterThan(0)
    expect(payload.doors[0]?.argv.length).toBeGreaterThan(0)
  })

  it('reads a gate finding through the same door shape', async () => {
    // The claim the design makes: `explain`'s table and a lint finding's `remedy` are one
    // map at two moments, so one reader covers both. This repository's own gate carries
    // notes with remedies, which is where that gets exercised against real output.
    const linted = await read(REPO, 'lint', {}, { engineVersion })

    const withRemedy = [...linted.findings, ...linted.notes].find((entry) => entry.remedy !== null)
    expect(withRemedy?.remedy?.doors.length).toBeGreaterThan(0)
    expect(typeof withRemedy?.remedy?.doors[0]?.what).toBe('string')
  })
})

describe('RG4: the states a fixture is built to contain', () => {
  it('has a ledger, whose lines point at no rationale at all', async () => {
    const payload = await readVerb('list', { role: 'changelog' })

    expect(listedTasks(payload).some((task) => task.status === '✅')).toBe(true)
    // Shipping deletes the design, so the pointer has nothing to resolve to. The roadmap's
    // lines carry one and the ledger's do not, which is a shape difference between two
    // listings of the same verb.
    expect(listedTasks(payload).every((task) => task.ref === null)).toBe(true)
  })

  it('has a deferred store, which `list --role deferred` reads', async () => {
    const payload = await readVerb('list', { role: 'deferred' })
    expect(listedTasks(payload).length).toBeGreaterThan(0)
  })
})

/**
 * Last in the file, and it has to be: it reads what the cases above marked off as they ran.
 */
describe('RG83: every second shape this file names is one it covers', () => {
  it('has a case for each, so naming one without covering it is the failure', () => {
    const named = Object.keys(SECOND_SHAPES) as SecondShape[]
    const missing = named.filter((shape) => !covered.has(shape))

    expect(
      missing.map((shape) => `${shape} — ${SECOND_SHAPES[shape]}`),
      'a second shape is declared above and no case exercises it',
    ).toEqual([])
  })

  it('names no shape a case does not, so the list cannot outlive the call', () => {
    // The other direction. A `covers` left behind after its case went is a list claiming
    // coverage nothing provides, which is the failure this file exists to make impossible.
    expect([...covered].every((shape) => shape in SECOND_SHAPES)).toBe(true)
  })
})
