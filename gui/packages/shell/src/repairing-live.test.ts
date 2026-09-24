import {
  actionableReport,
  anyRunnable,
  applyWrite,
  composeDoor,
  composeWrite,
  offerOf,
  passFrom,
  readAddedPayload,
  readRepairPayload,
  readSectionWritten,
  saidOfPass,
  type Actionable,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { CEILING, liveEngine as engine, read } from './live'
import { buildFixture, type Fixture } from './fixture'

/**
 * The gate as a surface, against a real engine. The findings here are made on purpose —
 * a line filed with no section is a `ref.unresolved` the moment it is written — because a
 * clean project cannot show what a report looks like.
 */

let fixture: Fixture

async function report(): Promise<Actionable[]> {
  return actionableReport(await read(fixture.root, 'lint', {}))
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 1, shipped: 0, deferred: 0 })

  // A line with no section: its pointer resolves to nothing, which the gate reports.
  const filed = await applyWrite(
    engine,
    composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom: 'a line goes in pointing at a section nobody wrote',
      why: 'The gate has to have something to find.',
    }),
    readAddedPayload,
    { timeoutMs: CEILING },
  )
  if (filed.kind !== 'applied') throw new Error(`add was ${filed.kind}`)
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG33: a real finding, with the door that closes it', () => {
  it('reports the code, the place and the argv, all as data', async () => {
    const found = await report()
    const unresolved = found.find((one) => one.code === 'ref.unresolved')

    expect(unresolved).toBeDefined()
    expect(unresolved?.where).toMatch(/ROADMAP\.md:\d+$/)
    expect(unresolved?.id).toMatch(/^FX\d+$/)
    expect(unresolved?.offers.length).toBeGreaterThan(0)
  })

  it('sorts this one as a form, because the prose is the person to write', async () => {
    // `No field this app composes` at the far end: the door names the section and leaves
    // the title and the body blank, which is exactly what cannot be filled in here.
    const found = await report()
    const offer = found.find((one) => one.code === 'ref.unresolved')?.offers[0]

    expect(offer?.kind).toBe('fill')
    expect(offer?.door.writes).toBe(true)
    expect(offer?.door.argv.slice(0, 2)).toEqual(['section', 'add'])
  })

  it('says nothing here can be closed without somebody typing first', async () => {
    expect(anyRunnable(await report())).toBe(false)
  })

  it('reads what a code means, and answers with doors of the same shape', async () => {
    const explained = await read(fixture.root, 'explain', { code: 'ref.unresolved' })

    expect(explained.code).toBe('ref.unresolved')
    expect(explained.cause).not.toBe('')
    // One reader for a refusal's doors and a finding's, so they cannot be offered
    // differently in the two places.
    expect(offerOf(explained.doors[0]!).kind).toBe('fill')
  })
})

describe('RG33: the repair pass, dry first', () => {
  it('says what it would do and changes nothing', async () => {
    const before = await report()

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'repair', { dryRun: true }),
      readRepairPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const pass = passFrom(outcome.value)

    expect(pass.dry).toBe(true)
    expect(saidOfPass(pass)).toContain('dry run')
    // It left what it could not close, in a finding's own shape.
    expect(pass.left.map((one) => one.code)).toContain('ref.unresolved')
    // And the report is exactly as it was.
    expect((await report()).map((one) => one.code)).toEqual(before.map((one) => one.code))
  })

  it('leaves a finding no door can close, rather than claiming it fixed it', async () => {
    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'repair', {}),
      readRepairPayload,
      { timeoutMs: CEILING },
    )

    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    const pass = passFrom(outcome.value)

    expect(pass.dry).toBe(false)
    expect(pass.clean).toBe(false)
    expect(pass.left.map((one) => one.code)).toContain('ref.unresolved')
  })
})

describe('RG33: a door run as the engine composed it', () => {
  it('closes the finding when the blanks are filled and the argv is run', async () => {
    // The door named the section and left the prose blank. Filling it is the person's,
    // and what runs afterwards is the engine's own argv with the root added.
    const found = await report()
    const offer = found.find((one) => one.code === 'ref.unresolved')?.offers[0]
    expect(offer?.kind).toBe('fill')
    if (offer === undefined || offer.kind !== 'fill') throw new Error('unreachable')

    const anchor = offer.door.argv[2]!
    expect(anchor).toMatch(/^FX\d+$/)

    // The same move the door describes, composed through the table because this app is
    // choosing the fields now.
    const written = await applyWrite(
      engine,
      composeWrite(fixture.root, 'sectionAdd', {
        anchor,
        title: 'The rationale the gate asked for',
        body: 'Prose long enough to read as a design and well inside the declared budget.',
      }),
      readSectionWritten,
      { timeoutMs: CEILING },
    )

    expect(written.kind).toBe('applied')
    expect((await report()).some((one) => one.code === 'ref.unresolved')).toBe(false)
  })

  it('wraps a door argv with the root and asks for the machine-readable form', () => {
    const composed = composeDoor(fixture.root, {
      argv: ['section', 'add', 'FX1', '--title', 'A heading'],
    })

    expect(composed.argv[0]).toBe('-C')
    expect(composed.argv[1]).toBe(fixture.root)
    expect(composed.argv.at(-1)).toBe('--json')
    // Nothing between them was touched.
    expect(composed.argv.slice(2, -1)).toEqual(['section', 'add', 'FX1', '--title', 'A heading'])
  })
})
