import path from 'node:path'

import {
  applyWrite,
  composeWrite,
  createClient,
  readAddedPayload,
  readSectionWritten,
  saidOfWrite,
  wasCreated,
  whereWritten,
  writtenFrom,
  type Written,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * Writing rationale against a real engine, on a fixture. The prose in this repository's
 * own improvements file is governed, so a live test that wrote there would be editing the
 * thing it is testing.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let fixture: Fixture

async function sectionWrite(
  verb: 'sectionAdd' | 'sectionAmend',
  input: Parameters<typeof composeWrite<'sectionAdd' | 'sectionAmend'>>[2],
): Promise<Written> {
  const outcome = await applyWrite(
    engine,
    composeWrite(fixture.root, verb, input),
    readSectionWritten,
    { timeoutMs: CEILING },
  )
  if (outcome.kind !== 'applied') throw new Error(`${verb} was ${outcome.kind}`)
  return writtenFrom(outcome.value)
}

/** The prose the file now holds, read back through `show`. */
async function proseOf(id: string): Promise<string> {
  const answer = await client.call(fixture.root, 'show', { id }, { timeoutMs: CEILING })
  if (!answer.ok || answer.value.kind === 'refused') throw new Error('show did not read')
  return answer.value.value.section?.body ?? ''
}

/** A line with no section, so its pointer resolves to nothing until one is written. */
async function lineWithoutSection(symptom: string): Promise<string> {
  const outcome = await applyWrite(
    engine,
    composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom,
      why: 'A sentence that ends in a stop.',
    }),
    readAddedPayload,
    { timeoutMs: CEILING },
  )
  if (outcome.kind !== 'applied') throw new Error(`add was ${outcome.kind}`)
  return outcome.value.id
}

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 1, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG32: the follow-up a pointer needs', () => {
  it('writes the section a line was filed without', async () => {
    const id = await lineWithoutSection('a line goes in with no rationale behind it')

    // Filed without one, so the pointer resolves to nothing until this call.
    expect(await proseOf(id)).toBe('')

    const one = await sectionWrite('sectionAdd', {
      anchor: id,
      title: 'Why this line needed a rationale',
      body: 'A rationale long enough to read as prose and well inside the declared budget.',
    })

    expect(one.anchor).toBe(id)
    expect(wasCreated(one)).toBe(true)
    expect(whereWritten(one)).toContain('IMPROVEMENTS.md')
    expect(one.words).toBeGreaterThan(0)
    expect(await proseOf(id)).toContain('long enough to read as prose')
  })

  it('counts the words the file holds, not the string that was sent', async () => {
    const id = await lineWithoutSection('the count comes off the draft rather than the file')
    const body = 'One two three four five six seven eight nine ten.'
    const one = await sectionWrite('sectionAdd', { anchor: id, title: 'A short one', body })

    expect(one.words).toBe(10)
    expect(saidOfWrite(one)).toContain('10 words')
  })
})

describe('RG32: correcting a section as a fragment', () => {
  it('replaces the fragment and leaves the rest of the prose alone', async () => {
    const id = await lineWithoutSection('a correction has to match bytes nobody chose')
    await sectionWrite('sectionAdd', {
      anchor: id,
      title: 'A section to correct',
      body: 'A rationale long enough to be prose and well inside the declared budget.',
    })

    const one = await sectionWrite('sectionAmend', {
      anchor: id,
      fragment: { replace: 'long enough to be prose', replacement: 'written to be read' },
    })

    expect(wasCreated(one)).toBe(false)
    expect(one.changed).toContain('body')

    const prose = await proseOf(id)
    expect(prose).toContain('written to be read')
    expect(prose).not.toContain('long enough to be prose')
    // The rest of the sentence survived, which is the whole point of a fragment edit.
    expect(prose).toContain('well inside the declared budget')
  })

  it('deletes a fragment with an empty replacement', async () => {
    const id = await lineWithoutSection('a clause has to come out without rewriting the paragraph')
    await sectionWrite('sectionAdd', {
      anchor: id,
      title: 'A section with a clause too many',
      body: 'A rationale that is long enough, and a clause nobody needed, to be prose.',
    })

    await sectionWrite('sectionAmend', {
      anchor: id,
      fragment: { replace: ', and a clause nobody needed,', replacement: '' },
    })

    expect(await proseOf(id)).not.toContain('nobody needed')
  })

  it('writes nothing for a fragment that is not there, and says why', async () => {
    const id = await lineWithoutSection('a fragment that matches nothing must not be guessed at')
    await sectionWrite('sectionAdd', {
      anchor: id,
      title: 'A section to miss',
      body: 'A rationale long enough to be prose and well inside the declared budget.',
    })
    const before = await proseOf(id)

    const outcome = await applyWrite(
      engine,
      composeWrite(fixture.root, 'sectionAmend', {
        anchor: id,
        fragment: { replace: 'a phrase this prose never contained', replacement: 'x' },
      }),
      readSectionWritten,
      { timeoutMs: CEILING },
    )

    expect(await proseOf(id)).toBe(before)

    // This refusal goes to stderr with nothing on stdout, so there is no payload and the
    // outcome is `unreadable` rather than `refused`. RG79 is why the engine's own sentence
    // survives that: it names the fragment and points at the verb that prints the prose,
    // which is the whole of what there is to tell somebody who mistyped it.
    expect(outcome.kind).toBe('unreadable')
    if (outcome.kind !== 'unreadable') throw new Error('unreachable')
    expect(outcome.unreadable.reason).toBe('unreadable-payload')
    expect(outcome.unreadable.said).toContain('a phrase this prose never contained')
    expect(outcome.unreadable.said).toContain('section show')
    expect(outcome.unreadable.message).toBe(outcome.unreadable.said)
  })

  it('amends the heading without touching the prose bytes', async () => {
    const id = await lineWithoutSection('a heading is wrong and the prose under it is not')
    await sectionWrite('sectionAdd', {
      anchor: id,
      title: 'A name that turned out wrong',
      body: 'A rationale long enough to be prose and well inside the declared budget.',
    })
    const before = await proseOf(id)

    const one = await sectionWrite('sectionAmend', { anchor: id, title: 'A better name' })

    expect(one.title).toBe('A better name')
    expect(one.changed).toContain('title')
    expect(await proseOf(id)).toBe(before)
  })
})
