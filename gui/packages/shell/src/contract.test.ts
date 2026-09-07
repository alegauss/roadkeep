import path from 'node:path'

import {
  VERBS,
  createClient,
  explainFailure,
  fieldsRefused,
  flagsFor,
  narrowingOfBrief,
  narrowingOfList,
  narrowingOfStats,
  readAnswer,
  readBriefPayload,
  readCapabilities,
  readEnginesPayload,
  readExplanation,
  readListPayload,
  readLintPayload,
  readPayload,
  readShowPayload,
  readStatsPayload,
  resolveEngine,
  withheld,
  type Parsed,
  type Reader,
  type VerbName,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { engineCandidates } from './engine-candidates'
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
 * general, which is why the version that answered is asserted to exist and reported.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const transport = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(transport)

let fixture: Fixture
let engineVersion = ''

beforeAll(async () => {
  fixture = await buildFixture(transport)

  const resolution = await resolveEngine(
    (engine) =>
      createProcessTransport({ command: engine[0] ?? '', prefixArgs: engine.slice(1) }),
    REPO,
    engineCandidates(REPO),
    { timeoutMs: CEILING },
  )
  if (resolution.kind === 'resolved') {
    engineVersion = resolution.engine.payload.writing.version
  }
}, 180000)

afterAll(() => {
  fixture.dispose()
})

/** Read one verb's answer off the fixture, failing with the sentence a user would see. */
async function readVerb<T>(
  verb: VerbName,
  input: Parameters<typeof client.call>[2],
  reader: Reader<T>,
): Promise<T> {
  const result = await client.call(fixture.root, verb, input, { timeoutMs: CEILING })
  const where = { verb, engineVersion }
  const parsed: Parsed<T> = readPayload(reader, result.stdout, where)

  // The message is the point of failing: it names the key that moved and the build that
  // moved it, which is what somebody reading a red suite actually needs.
  expect(parsed.ok, parsed.ok ? '' : explainFailure(parsed.failure, where)).toBe(true)
  if (!parsed.ok) throw new Error(explainFailure(parsed.failure, where))
  return parsed.value
}

describe('RG4: the build this contract was proven against', () => {
  it('names a version, so a green suite is a claim about one engine', () => {
    expect(engineVersion).toMatch(/^\d+\.\d+\.\d+/)
  })
})

describe('RG4: every read this client makes, against a live engine', () => {
  it('covers every verb the client can build a command line for', () => {
    // The guard that keeps this file honest. A verb added to the table without a shape and
    // without a case here is the hole RG66 exists to close structurally; until then this
    // is what notices.
    expect(Object.keys(VERBS).sort()).toEqual(
      ['brief', 'commands', 'engines', 'explain', 'lint', 'list', 'show', 'stats'].sort(),
    )
  })

  it('reads a listing, with its standing and its lines', async () => {
    const payload = await readVerb('list', {}, readListPayload)

    expect(payload.file).toContain('ROADMAP.md')
    expect(payload.tasks.length).toBeGreaterThan(0)
    // Shape, not values: what matters is that every declared key was there and typed.
    expect(typeof payload.tasks[0]?.symptom).toBe('string')
    expect(Array.isArray(payload.tasks[0]?.deps)).toBe(true)
    expect(narrowingOfList(payload).complete).toBe(true)
  })

  it('reads a listing narrowed to one block', async () => {
    const payload = await readVerb('list', { block: 'A' }, readListPayload)

    expect(payload.standing?.block).toBe('A')
  })

  it('reads a listing of another governed role', async () => {
    // `--role changelog` is a different file with the same shape, and the fixture has a
    // shipped line so it is not empty.
    const payload = await readVerb('list', { role: 'changelog' }, readListPayload)

    expect(payload.file).toContain('CHANGELOG.md')
    expect(payload.tasks.length).toBeGreaterThan(0)
  })

  it('reads the counts, keyed by the marker set the fixture declared', async () => {
    const payload = await readVerb('stats', {}, readStatsPayload)

    expect(payload.total).toBeGreaterThan(0)
    expect(Object.keys(payload.markers).length).toBeGreaterThan(0)
    expect(payload.blocks.length).toBeGreaterThan(0)
    expect(narrowingOfStats(payload).complete).toBe(true)
  })

  it('reads one task with the rationale its pointer resolves to', async () => {
    const listed = await readVerb('list', {}, readListPayload)
    const first = listed.tasks[0]
    expect(first).toBeDefined()
    if (!first) return

    const payload = await readVerb('show', { id: first.id }, readShowPayload)

    expect(payload.id).toBe(first.id)
    expect(payload.section?.body).not.toBe('')
    expect(payload.section?.words).toBeGreaterThan(0)
  })

  it('reads a task with its prose left out, which is a different answer', async () => {
    const listed = await readVerb('list', {}, readListPayload)
    const first = listed.tasks[0]
    if (!first) return

    const payload = await readVerb('show', { id: first.id, noBody: true }, readShowPayload)

    // The section is still there and still located; only the prose is gone, and it comes
    // back null rather than empty. A shape demanding a string failed on exactly this flag,
    // which is the finding this file was written to produce.
    expect(payload.section?.file).toContain('IMPROVEMENTS.md')
    expect(payload.section?.body).toBeNull()
  })

  it('reads a brief, including what it left out', async () => {
    const payload = await readVerb('brief', {}, readBriefPayload)

    expect(payload.id).not.toBe('')
    expect(payload.readiness).not.toBe('')
    expect(payload.nonGoals.length).toBeGreaterThan(0)
    expect(payload.doneWhen.length).toBeGreaterThan(0)
    // The elision counts are read whether or not this fixture elides anything: a client
    // that never looked would draw a sample as though it were the set.
    expect(narrowingOfBrief(payload)).toHaveProperty('complete')
  })

  it('reads the gate, whose non-zero exit is an answer', async () => {
    const result = await client.call(fixture.root, 'lint', {}, { timeoutMs: CEILING })
    const where = { verb: 'lint', engineVersion }
    const parsed = readPayload(readLintPayload, result.stdout, where)

    expect(parsed.ok, parsed.ok ? '' : explainFailure(parsed.failure, where)).toBe(true)
    if (!parsed.ok) return
    expect([0, 1]).toContain(result.code)
    expect(typeof parsed.value.clean).toBe('boolean')
    expect(parsed.value.checked.length).toBeGreaterThan(0)
  })

  it('reads which engine answered for the fixture', async () => {
    const result = await client.call(fixture.root, 'engines', {}, { timeoutMs: CEILING })
    const payload = readEnginesPayload(result.stdout)

    expect(payload).not.toBeNull()
    expect(payload?.writing.version).toBe(engineVersion)
  })
})

describe('RG6: what the live build says it can do', () => {
  it('publishes every verb this app calls, with every flag it would send', async () => {
    const result = await client.call(fixture.root, 'commands', {}, { timeoutMs: CEILING })
    const report = readCapabilities(result.stdout, engineVersion)

    expect(report.kind).toBe('known')
    if (report.kind !== 'known') return

    // The assertion that earns this read: not "commands parsed", but that the flags this
    // app composes are flags this build actually takes. A failure here names them.
    expect(withheld(report), withheld(report).join('\n')).toEqual([])
    expect(report.complete).toBe(true)
    expect(report.version).toBe(engineVersion)
  })

  it('agrees with the flags derived from this project’s own builders', async () => {
    const result = await client.call(fixture.root, 'commands', {}, { timeoutMs: CEILING })
    const report = readCapabilities(result.stdout, engineVersion)
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
      argv: ['-C', fixture.root, 'add', '--block', 'A', '--symptom', 'x'.repeat(200), '--why', 'A reason that is fine.', '--json'],
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
    const result = await client.call(fixture.root, 'show', { id: 'FX999' }, { timeoutMs: CEILING })
    const parsed = readAnswer(readShowPayload, result)

    expect(parsed.ok).toBe(true)
    if (!parsed.ok || parsed.value.kind !== 'refused') {
      throw new Error(`expected a refusal, got ${result.stdout.slice(0, 120)}`)
    }
    expect(fieldsRefused(parsed.value.refusal)).toEqual([])
    expect(parsed.value.refusal.said).not.toBe('')
  })

  it('reads the doors that close the code a refusal named', async () => {
    const payload = await readVerb('explain', { code: 'symptom.too-long' }, readExplanation)

    expect(payload.code).toBe('symptom.too-long')
    expect(payload.cause).not.toBe('')
    expect(payload.doors.length).toBeGreaterThan(0)
    expect(payload.doors[0]?.argv.length).toBeGreaterThan(0)
  })

  it('reads a gate finding through the same door shape', async () => {
    // The claim the design makes: `explain`'s table and a lint finding's `remedy` are one
    // map at two moments, so one reader covers both. This repository's own gate carries
    // notes with remedies, which is where that gets exercised against real output.
    const result = await client.call(REPO, 'lint', {}, { timeoutMs: CEILING })
    const parsed = readPayload(readLintPayload, result.stdout, { verb: 'lint', engineVersion })

    expect(parsed.ok).toBe(true)
    if (!parsed.ok) return
    const withRemedy = [...parsed.value.findings, ...parsed.value.notes].find(
      (entry) => entry.remedy !== null,
    )
    expect(withRemedy?.remedy?.doors.length).toBeGreaterThan(0)
    expect(typeof withRemedy?.remedy?.doors[0]?.what).toBe('string')
  })
})

describe('RG4: the states a fixture is built to contain', () => {
  it('has a ledger, whose lines point at no rationale at all', async () => {
    const payload = await readVerb('list', { role: 'changelog' }, readListPayload)

    expect(payload.tasks.some((task) => task.status === '✅')).toBe(true)
    // Shipping deletes the design, so the pointer has nothing to resolve to. The roadmap's
    // lines carry one and the ledger's do not, which is a shape difference between two
    // listings of the same verb.
    expect(payload.tasks.every((task) => task.ref === null)).toBe(true)
  })

  it('has a deferred store, which `list --role deferred` reads', async () => {
    const payload = await readVerb('list', { role: 'deferred' }, readListPayload)
    expect(payload.tasks.length).toBeGreaterThan(0)
  })
})
