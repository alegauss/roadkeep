import path from 'node:path'

import {
  anyOver,
  counterFor,
  createClient,
  overBy,
  readBudgetPayload,
  readPayload,
  saidOfCounter,
  structureOf,
  type BudgetPayload,
  type VerbInputs,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The budget read against a real engine. The numbers here are the project's own, so
 * nothing is asserted as a literal that `roadkeep.toml` gets to choose — what is asserted
 * is the arithmetic between them.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function priced(input: VerbInputs['budget']): Promise<BudgetPayload> {
  const result = await client.call(fixture.root, 'budget', input, { timeoutMs: CEILING })
  const parsed = readPayload(readBudgetPayload, result.stdout, {
    verb: 'budget',
    engineVersion: '',
  })
  if (!parsed.ok) {
    throw new Error(`budget did not read: expected ${parsed.failure.expected}`)
  }
  return parsed.value
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG36: a line that does not exist yet, priced', () => {
  it('answers with the id an add would mint and what its fields have', async () => {
    const payload = await priced({ block: 'A' })

    expect(payload.id).toMatch(/^FX\d+$/)
    expect(payload.lineMax).toBeGreaterThan(0)
    expect(payload.fields.map((one) => one.field)).toContain('symptom')
    expect(payload.fields.map((one) => one.field)).toContain('why')
  })

  it('names where each number comes from, so it is the project and not this app', async () => {
    const payload = await priced({ block: 'A' })

    // The address in the project's own config. A limit written here would be the literal
    // `No rule compiled into the client` refuses.
    expect(payload.fields.every((one) => one.source.includes('roadkeep.toml'))).toBe(true)
  })

  it('leaves the why less room once the line carries deps', async () => {
    // The arithmetic, not the numbers: adding a dep is structure, and structure comes out
    // of the prose the line has left.
    const bare = await priced({ block: 'A' })
    const withDeps = await priced({ block: 'A', deps: ['FX1', 'FX2'] })

    expect(withDeps.structure).toBeGreaterThan(bare.structure)
    expect(withDeps.prose).toBeLessThan(bare.prose)

    // The allowance can only go down. Whether it moves at all depends on how much prose
    // the line was already leaving, which is the project's business and not this test's.
    const before = counterFor(bare, 'why')!
    const after = counterFor(withDeps, 'why')!
    expect(after.allowed).toBeLessThanOrEqual(before.allowed)
    expect(structureOf(withDeps)).toContain('2 deps')
  })

  it('takes from the why what the symptom spends, because they share the line', async () => {
    // The coupling that makes this a read and not a constant: what the symptom takes is
    // what the why loses, so a long symptom binds the why below its own limit and the
    // counter has to follow.
    // Long enough to matter: the why keeps its own limit until the symptom has eaten
    // enough of the line that what is left falls below it.
    const short = await priced({ block: 'A', symptom: 'a short one' })
    const long = await priced({
      block: 'A',
      symptom:
        'a symptom that runs most of the way to the limit this project declares for it ' +
        'and then some more',
    })

    const before = counterFor(short, 'why')!
    const after = counterFor(long, 'why')!

    expect(after.allowed).toBeLessThan(before.allowed)
    expect(after.allowed).toBeLessThan(long.fields.find((one) => one.field === 'why')!.limit)
    expect(after.boundBy).toBe('the rendered line')
    expect(saidOfCounter(after)).toContain('the rendered line')
  })

  it('names what bound the allowance exactly when something did', async () => {
    // The invariant rather than the number: whichever way this project's limits fall,
    // `allowed` below `limit` is the case a counter must not miss, and it is the case that
    // has to carry a reason.
    for (const deps of [[], ['FX1'], ['FX1', 'FX2']]) {
      const payload = await priced({ block: 'A', deps })
      for (const field of payload.fields) {
        const counter = counterFor(payload, field.field)!

        expect(counter.allowed).toBeLessThanOrEqual(field.limit)
        expect(counter.boundBy === '').toBe(counter.allowed === field.limit)
        if (counter.boundBy !== '') {
          expect(saidOfCounter(counter)).toContain(counter.boundBy)
        }
      }
    }
  })
})

describe('RG36: a draft measured, not refused', () => {
  it('reports a draft that fits, with what is left and what is left to the aim', async () => {
    const payload = await priced({ block: 'A', symptom: 'a short symptom' })
    const symptom = counterFor(payload, 'symptom')!

    expect(symptom.taken).toBe('a short symptom'.length)
    expect(symptom.over).toBe(0)
    expect(anyOver(payload)).toBe(false)
    expect(symptom.left).toBeGreaterThan(0)
  })

  it('reports one that does not, and nothing is written', async () => {
    // Exit 1 here means over, the way it means found for `lint`. The answer is an
    // ordinary payload and the reading comes off `over`.
    const long = 'a symptom deliberately far longer than whatever this project declares, '.repeat(3)
    const payload = await priced({ block: 'A', symptom: long })

    expect(anyOver(payload)).toBe(true)
    expect(overBy(payload).map((one) => one.field)).toEqual(['symptom'])
    expect(saidOfCounter(overBy(payload)[0]!)).toContain('over')
  })

  it('prices a section in words, where a line is priced in characters', async () => {
    const payload = await priced({ block: 'A' })

    expect(payload.section?.unit).toBe('words')
    expect(payload.fields[0]?.unit).not.toBe('words')
    expect(payload.section?.aim).toBeLessThan(payload.section?.limit ?? 0)
  })

  it('prices the sentence a ship writes, which is a different limit from the line', async () => {
    const line = await priced({ id: 'FX1' })
    const ship = await priced({ id: 'FX1', ship: true })

    // A shipped line carries no pointer, so `ref` comes back null here where the open
    // form sends a string. A shape demanding one fails on exactly this call.
    expect(line.ref).not.toBeNull()
    expect(ship.ref).toBeNull()
    // The ledger line has no pointer and no deps, so its structure is the cheaper one and
    // the sentence is measured against a different shape.
    expect(ship.structure).toBeLessThan(line.structure)
    expect(counterFor(ship, 'why')).not.toBeNull()
  })
})
