import { readFileSync } from 'node:fs'
import path from 'node:path'

import {
  actsIn,
  actsOf,
  createClient,
  governedFiles,
  readConfigPayload,
  readPayload,
  touched,
  type Act,
  type Marks,
} from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { fakeClaude } from './fake-claude'
import { createProcessTransport } from './process-transport'
import { sessionCall } from '@rk/core'
import { startSession } from './session-process'

/**
 * The acts, read off a stream a real session actually wrote.
 *
 * `captured/session-stream.jsonl` is one headless run, kept verbatim except for a
 * signature and the usage accounting, which are large and not what the fixture is for.
 * It goes stale the way any recorded fixture does — what it proves is that this reader
 * handles the shapes Claude Code emitted on the day it was captured, and nothing more.
 *
 * The marks, though, are read live: which files this project governs is `config`'s answer
 * and never a filename written into a test.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

const CAPTURED = readFileSync(
  path.join(import.meta.dirname, 'captured', 'session-stream.jsonl'),
  'utf8',
)
  .split('\n')
  .filter((line) => line.trim() !== '')

let marks: Marks = { governed: [], engine: [] }

beforeAll(async () => {
  const result = await client.call(REPO, 'config', {}, { timeoutMs: CEILING })
  const parsed = readPayload(readConfigPayload, result.stdout, {
    verb: 'config',
    engineVersion: '',
  })
  if (!parsed.ok) throw new Error('config did not read')

  marks = {
    governed: Object.values(governedFiles(parsed.value)),
    engine: ['roadkeep', 'mcp__roadkeep__'],
  }
}, 180000)

describe('RG40: a stream a real session wrote', () => {
  it('reads every line into acts, losing none of them', () => {
    const acts = actsIn(CAPTURED, marks)

    expect(CAPTURED.length).toBeGreaterThan(5)
    expect(acts.length).toBeGreaterThanOrEqual(CAPTURED.length)
    // Numbered in the order emitted, with no gaps.
    expect(acts.map((act) => act.seq)).toEqual(acts.map((_, index) => index + 1))
  })

  it('finds the tool call and the result that answered it', () => {
    const acts = actsIn(CAPTURED, marks)
    const used = acts.find((act): act is Extract<Act, { kind: 'used' }> => act.kind === 'used')
    expect(used).toBeDefined()
    if (used === undefined) return

    expect(used.tool).toBe('Bash')
    expect(used.on).toBe('echo hello')

    const answered = acts.find(
      (act): act is Extract<Act, { kind: 'returned' }> =>
        act.kind === 'returned' && act.id === used.id,
    )
    expect(answered?.ok).toBe(true)
    expect(answered?.text).toBe('hello')
  })

  it('draws thinking as a note, because its content came back empty', () => {
    const acts = actsIn(CAPTURED, marks)
    const thinking = acts.filter((act) => act.kind === 'note' && act.about === 'thinking')

    expect(thinking.length).toBeGreaterThan(0)
  })

  it('touched nothing governed, because this session touched nothing', () => {
    // The honest answer for a run that only echoed. A reader reporting otherwise would be
    // inventing evidence a screen is about to act on.
    expect(touched(actsIn(CAPTURED, marks))).toEqual([])
  })

  it('reads the governed set off config rather than out of this file', () => {
    expect(marks.governed.length).toBeGreaterThan(3)
    expect(marks.governed.some((file) => file.includes('ROADMAP'))).toBe(true)
  })

  it('marks a roadkeep call, using this project own governed paths', () => {
    // Not from the capture — that session never called roadkeep — so the line is built
    // from the paths `config` just published.
    const governed = marks.governed[0]!
    const line = JSON.stringify({
      type: 'assistant',
      message: {
        content: [
          {
            type: 'tool_use',
            id: 't1',
            name: 'Bash',
            input: { command: `roadkeep ship RG40 --why "it works"` },
          },
          { type: 'tool_use', id: 't2', name: 'Read', input: { file_path: governed } },
        ],
      },
    })

    const acts = actsOf(line, 1, marks)
    expect(acts.filter((act) => act.kind === 'used' && act.roadkeep)).toHaveLength(1)
    expect(touched(acts)).toEqual([governed])
  })
})

describe('RG40: acts off a session as it runs', () => {
  it('arrives turn by turn rather than at the end', async () => {
    // `stream-json` exists so a window can show the turns as they happen; a reader that
    // waited for the exit would have thrown away what it is for.
    const fake = fakeClaude({ chunked: true })
    const call = sessionCall(fake.command, REPO, 'x')
    const seen: Act[] = []

    const session = startSession(
      { ...call, argv: [...fake.prefixArgs, ...call.argv] },
      { onLine: (line) => seen.push(...actsOf(line, seen.length + 1, marks)) },
    )
    const outcome = await session.finished
    fake.dispose()

    expect(outcome.state).toBe('done')
    // Every line reaches a watcher raw, so acts read the same live as after the fact —
    // and the assistant turn is there, not just the exit.
    expect(seen.some((act) => act.kind === 'said')).toBe(true)
    expect(seen.map((act) => act.seq)).toEqual(seen.map((_, index) => index + 1))
  })

  it('reads the same acts live as it does from the whole stream afterwards', async () => {
    const fake = fakeClaude({})
    const call = sessionCall(fake.command, REPO, 'x')
    const lines: string[] = []

    const session = startSession(
      { ...call, argv: [...fake.prefixArgs, ...call.argv] },
      { onLine: (line) => lines.push(line) },
    )
    await session.finished
    fake.dispose()

    // The raw form is the same object either way, which is what makes one reader serve
    // the live view and the diagnosis afterwards.
    const live = lines.flatMap((line, index) => actsOf(line, index + 1, marks))
    expect(actsIn(lines, marks).map((act) => act.kind)).toEqual(live.map((act) => act.kind))
  })
})
