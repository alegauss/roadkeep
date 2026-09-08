import path from 'node:path'

import {
  applyWrite,
  commandLine,
  composeWrite,
  createTranscript,
  entryLine,
  readAddedPayload,
  readStatusPayload,
  type Transcript,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { createProcessTransport } from './process-transport'

/**
 * The transcript against real calls. What it has to be true about is what actually ran, so
 * every entry here comes from a write that really went to the engine.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })

let fixture: Fixture

beforeAll(async () => {
  fixture = await buildFixture(engine, { open: 2, shipped: 0, deferred: 0 })
}, 180000)

afterAll(() => {
  fixture.dispose()
})

describe('RG34: a transcript of what actually ran', () => {
  it('records a write that landed, with its exit code and how long it took', async () => {
    const composed = composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom: 'a write the transcript has not seen yet, with an apostrophe in it',
      why: 'The line has to be reproducible from what was recorded.',
    })
    const outcome = await applyWrite(engine, composed, readAddedPayload, { timeoutMs: CEILING })

    expect(outcome.kind).toBe('applied')
    const log: Transcript = createTranscript().remember(composed, outcome)
    const entry = log.entries[0]

    expect(entry?.ran).toBe('applied')
    expect(entry?.code).toBe(0)
    expect(entry?.durationMs).toBeGreaterThan(0)
    expect(entry?.argv).toEqual(composed.argv)
    expect(entry?.root).toBe(fixture.root)
  })

  it('records a refusal with the exit code the engine actually used', async () => {
    // The pair worth seeing: a refusal is settled by what the answer said, and the code is
    // whatever the process happened to return. Asserted against the real one rather than a
    // number written here.
    const composed = composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom:
        'a symptom deliberately far longer than the limit this project declares for it, ' +
        'so the engine has something to refuse and a field to name when it does',
      why: 'This never lands.',
    })
    const outcome = await applyWrite(engine, composed, readAddedPayload, { timeoutMs: CEILING })

    expect(outcome.kind).toBe('refused')
    if (outcome.kind !== 'refused') throw new Error('unreachable')

    const entry = createTranscript().remember(composed, outcome).entries[0]
    expect(entry?.ran).toBe('refused')
    expect(entry?.code).toBe(outcome.code)
  })

  it('keeps every write in the order it ran them', async () => {
    let log = createTranscript()
    for (const marker of ['📋', '🛠', '📋']) {
      const composed = composeWrite(fixture.root, 'status', { id: 'FX1', marker })
      log = log.remember(
        composed,
        await applyWrite(engine, composed, readStatusPayload, { timeoutMs: CEILING }),
      )
    }

    expect(log.entries.map((one) => one.seq)).toEqual([1, 2, 3])
    expect(log.entries.every((one) => one.verb === 'status')).toBe(true)
    expect(entryLine(log.entries[1]!)).toContain('status')
  })
})

describe('RG34: the line a person could paste', () => {
  it('carries the prose through unmangled, whatever is in it', async () => {
    const symptom = `a backtick \`x\`, a $dollar, a "quote" and an apostrophe's worth`
    const composed = composeWrite(fixture.root, 'add', {
      block: 'A',
      symptom,
      why: 'An argv is an array, so a shell metacharacter is just a character.',
    })

    // It landed, so the prose in the line is prose the engine accepted.
    const outcome = await applyWrite(engine, composed, readAddedPayload, { timeoutMs: CEILING })
    expect(outcome.kind).toBe('applied')
    if (outcome.kind !== 'applied') throw new Error('unreachable')
    expect(outcome.value.rendered).toContain(symptom)

    // And the rendered command holds it, escaped for the shell rather than altered.
    const posix = commandLine(composed, 'posix')
    expect(posix).toContain(String.raw`apostrophe'\''s worth`)
    expect(commandLine(composed, 'powershell')).toContain("apostrophe''s worth")
    // Nothing was dropped: every argument is in there somewhere.
    expect(posix.startsWith('roadkeep -C ')).toBe(true)
    expect(posix.endsWith(' --json')).toBe(true)
  })

  it('renders a real fixture root whole, quoted where the path needs it', () => {
    const composed = composeWrite(fixture.root, 'repair', { dryRun: true })

    // A Windows path carries backslashes, and an unquoted backslash is an escape in a
    // POSIX shell — so it is quoted whether or not it has a space in it. Inside single
    // quotes both shells take it literally, which is what makes one rule serve both.
    const quoted = fixture.root.includes('\\') || fixture.root.includes(' ')
    const root = quoted ? `'${fixture.root}'` : fixture.root

    for (const shell of ['posix', 'powershell'] as const) {
      expect(commandLine(composed, shell)).toBe(`roadkeep -C ${root} repair --dry-run --json`)
    }
  })
})
