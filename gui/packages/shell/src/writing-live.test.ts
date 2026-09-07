import { readFileSync } from 'node:fs'
import path from 'node:path'

import {
  applyWrite,
  composeWrite,
  createClient,
  readAddedPayload,
  readListPayload,
  readPayload,
  type WriteOutcome,
  type AddedPayload,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The write path against a real engine, and never against this repository.
 *
 * Every write here goes to a temporary fixture. A live test that filed a line in this
 * project's own roadmap would be a test that governs the file it is testing, and the
 * failure mode is a governed file with test rows in it that somebody has to find.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

function add(
  input: Parameters<typeof composeWrite<'add'>>[2],
): Promise<WriteOutcome<AddedPayload>> {
  return applyWrite(engine, composeWrite(fixture.root, 'add', input), readAddedPayload, {
    timeoutMs: CEILING,
  })
}

async function roadmapIds(): Promise<string[]> {
  const result = await client.call(fixture.root, 'list', {}, { timeoutMs: CEILING })
  const parsed = readPayload(readListPayload, result.stdout, { verb: 'list', engineVersion: '' })
  if (!parsed.ok) throw new Error('list did not read')
  return parsed.value.tasks.map((task) => task.id)
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG29: a line filed by the command this app composed', () => {
  it('lands, and the answer is the line the file now spells', async () => {
    const before = await roadmapIds()
    const outcome = await add({
      block: 'A',
      symptom: 'a write has no door here yet',
      why: 'The app composes an argv and the command writes, and nothing composes one.',
      section: 'Why a write needs a door',
      sectionBody:
        'A rationale long enough to be prose and short enough to stay inside the budget ' +
        'the project declares for a section.',
    })

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.id).toMatch(/^FX\d+$/)
    expect(outcome.value.rendered).toContain('a write has no door here yet')
    expect(outcome.value.line).toBeGreaterThan(0)

    // Present now and absent before. Not appended: a listing is in file order, which is
    // block order, so a new line lands under its own heading and not at the end.
    const after = await roadmapIds()
    expect(before).not.toContain(outcome.value.id)
    expect(after).toContain(outcome.value.id)
    expect(after).toHaveLength(before.length + 1)
  })

  it('writes the section in the same transaction, so the pointer resolves', async () => {
    // A line whose section is missing is a `ref.unresolved` finding the moment it is
    // written, which is why both halves are one call.
    const outcome = await add({
      block: 'A',
      symptom: 'a pointer resolves to nothing until a section exists',
      why: 'The follow-up belongs in the call that creates the need for it.',
      section: 'A section filed with its line',
      sectionBody:
        'Prose long enough to read as a rationale and short enough to sit well inside ' +
        'the word budget this project declares.',
    })

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.section?.anchor).toBe(outcome.value.id)
    expect(outcome.value.section?.file).toContain('IMPROVEMENTS.md')
    expect(outcome.value.ref).toBe(outcome.value.id)
  })

  it('carries the deps and the marker it was told, as the file spells them', async () => {
    const outcome = await add({
      block: 'B',
      symptom: 'a dep and a marker are dropped on the way to the file',
      why: 'The table repeats a flag per value rather than joining them.',
      status: '💭',
      deps: ['FX1'],
      section: 'A line with a dep',
      sectionBody: 'Prose enough to be a rationale and well inside the budget declared.',
    })

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.rendered).toContain('💭')
    expect(outcome.value.rendered).toContain('FX1')
  })

  it('offers the nearest deliveries unasked, as an order and not a verdict', async () => {
    const outcome = await add({
      block: 'A',
      symptom: 'nothing answers question 1 yet, very nearly',
      why: 'The ranking is offered at the moment a duplicate would be made.',
      section: 'A near duplicate',
      sectionBody: 'Prose enough to be a rationale and well inside the budget declared.',
    })

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.near.length).toBeGreaterThan(0)
    expect(outcome.value.near[0]?.rank).toBe(1)
  })
})

describe('RG29: a write the engine refuses', () => {
  it('comes back as the field it is about, and nothing is written', async () => {
    const before = readFileSync(path.join(fixture.root, 'docs', 'ROADMAP.md'), 'utf8')
    const outcome = await add({
      block: 'A',
      symptom:
        'a symptom deliberately far longer than the limit this project declares for it, ' +
        'so that the engine has something to refuse and a field to name when it does',
      why: 'This never lands.',
    })

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.refused[0]?.code).toBe('symptom.too-long')
    expect(outcome.refusal.refused[0]?.field).toBe('symptom')
    // "refused, nothing written" is the engine's promise and this is what checks it.
    expect(readFileSync(path.join(fixture.root, 'docs', 'ROADMAP.md'), 'utf8')).toBe(before)
  })

  it('names the block that does not exist, without inventing one', async () => {
    const outcome = await add({
      block: 'Z',
      symptom: 'a block nothing declares',
      why: 'The engine owns which labels exist and this app never guesses.',
    })

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')
    expect(outcome.refusal.said).not.toBe('')
  })

  it('sends prose through argv unchanged, however it is spelled', async () => {
    // RK1474 recorded bytes arriving as different bytes through a shell. An argv is an
    // array and never a string, so a backtick is a character and not syntax.
    const outcome = await add({
      block: 'A',
      symptom: 'a `backtick`, a $dollar and a "quote" reach the file',
      why: "An argv is an array, so a shell's metacharacters are just characters.",
      section: 'Bytes that survive the call',
      sectionBody: 'Prose enough to be a rationale and well inside the budget declared.',
    })

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.rendered).toContain('a `backtick`, a $dollar and a "quote" reach the file')
  })
})
