import path from 'node:path'

import { createClient, promptFor, sessionCall, type SessionEvent } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { fakeClaude, type FakeBehaviour } from './fake-claude'
import { createProcessTransport } from './process-transport'
import { startSession, type RunningSession } from './session-process'

/**
 * The process half of a session, against a `claude` that is not Claude.
 *
 * A real headless run costs money and does work, so none is started here. What is started
 * is a script writing the `stream-json` lines a captured run wrote — which proves the part
 * this app owns and makes no claim about the part it does not.
 *
 * The prompt, though, is built from a real `brief` against this repository: it is the one
 * input that has to be right, and a fixture's would not exercise the join.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

let prompt = ''
const disposals: (() => void)[] = []

/** A session run against the fake, with the interpreter in front of the real argv. */
function run(behaviour: FakeBehaviour = {}, watcher = {}): RunningSession {
  const fake = fakeClaude(behaviour)
  disposals.push(fake.dispose)
  const call = sessionCall(fake.command, REPO, prompt)
  return startSession({ ...call, argv: [...fake.prefixArgs, ...call.argv] }, watcher)
}

beforeAll(async () => {
  const answer = await client.call(REPO, 'brief', {}, { timeoutMs: CEILING })
  if (!answer.ok || answer.value.kind === 'refused') throw new Error('brief did not read')
  prompt = promptFor(answer.value.value)
}, 180000)

afterAll(() => {
  for (const dispose of disposals) dispose()
})

describe('RG38: a session started from a real brief', () => {
  it('hands over the payload roadkeep answered, not a sentence about it', () => {
    // Built from this repository's own `brief`, so the join is the real one: the design
    // section, the resolved deps, and the lists that bind the line.
    expect(prompt).toMatch(/Work roadkeep task RG\d+ in this project/)
    expect(prompt).toContain('"depsResolved"')
    expect(prompt).toContain('"doneWhen"')
    expect(prompt).toContain('"nonGoals"')
    expect(prompt).toContain('verbatim')
  })

  it('runs where it was told to, which is what makes the project wiring answer', async () => {
    const session = run()
    await session.finished

    const started = session.events.find((event) => event.kind === 'started')
    expect(started?.kind).toBe('started')
    if (started?.kind !== 'started') throw new Error('unreachable')
    // The fake reports its own cwd, so this is the process's and not the argv's.
    expect(path.resolve(started.cwd)).toBe(path.resolve(REPO))
  })

  it('reads the whole stream in order and ends done', async () => {
    const seen: SessionEvent[] = []
    const session = run({}, { onEvent: (event: SessionEvent) => seen.push(event) })
    const outcome = await session.finished

    expect(seen.map((event) => event.kind)).toEqual(['started', 'other', 'said', 'finished'])
    expect(outcome.state).toBe('done')
    expect(outcome.sessionId).toBe('fake-0001')
    expect(outcome.result).toBe('done')
  })

  it('assembles a line split across two writes', async () => {
    // A chunk boundary can fall anywhere, including inside a prompt echoed back. Nothing
    // may assume one write is one line.
    const session = run({ chunked: true })
    const outcome = await session.finished

    expect(session.events.map((event) => event.kind)).toEqual([
      'started',
      'other',
      'said',
      'finished',
    ])
    expect(outcome.state).toBe('done')
  })

  it('tells a line it could not read from one it read and ignored', async () => {
    const unreadable: string[] = []
    const session = run(
      { garbage: true },
      { onUnreadable: (line: string) => unreadable.push(line) },
    )
    await session.finished

    expect(unreadable).toEqual(['not json at all'])
    // And the rate-limit line, which it read and had no use for, is still an event.
    expect(session.events.some((event) => event.kind === 'other')).toBe(true)
  })
})

describe('RG38: the three ways it does not work', () => {
  it('is unavailable when there is no claude on the machine', async () => {
    // A fact about the machine, not a session that went wrong — which is why it is its
    // own state. Naming which copy would have answered is RG43's.
    const session = startSession({
      command: path.join(REPO, 'no-such-claude-anywhere'),
      cwd: REPO,
      argv: ['-p', 'x'],
    })
    const outcome = await session.finished

    expect(outcome.state).toBe('unavailable')
    expect(outcome.said).not.toBe('')
  })

  it('is failed when the session says the run did not hold', async () => {
    const outcome = await run({ failing: true }).finished

    expect(outcome.state).toBe('failed')
    // The result is carried on a failure too: that sentence is the session saying why,
    // and dropping it would leave a screen with nothing but the word "failed".
    expect(outcome.result).toBe('ran out of turns')
    expect(outcome.sessionId).toBe('fake-0001')
  })

  it('is failed when it exits without ever saying how it went', async () => {
    const outcome = await run({ hanging: false, exitCode: 3 }).finished
    expect(outcome.state).toBe('done')

    // Nothing at all on stdout and a non-zero exit: there is no verdict to believe.
    const empty = startSession({
      command: process.execPath,
      cwd: REPO,
      argv: ['-e', 'process.exit(3)'],
    })
    const outcome2 = await empty.finished
    expect(outcome2.state).toBe('failed')
    expect(outcome2.code).toBe(3)
  })

  it('is cancelled when the window stops it, and the process is gone', async () => {
    const session = run({ hanging: true })
    // It never writes anything, so cancelling is the only way it ends.
    session.cancel()
    const outcome = await session.finished

    expect(outcome.state).toBe('cancelled')
  })

  it('can be cancelled twice, and after it has already finished', async () => {
    const session = run()
    await session.finished

    expect(() => {
      session.cancel()
      session.cancel()
    }).not.toThrow()
  })

  it('keeps what the process wrote on stderr, beside the outcome', async () => {
    const fake = fakeClaude({ exitCode: 0 })
    disposals.push(fake.dispose)
    const call = sessionCall(fake.command, REPO, prompt)
    const session = startSession({
      ...call,
      argv: [...fake.prefixArgs, ...call.argv, '--say-on-stderr'],
    })
    const outcome = await session.finished

    expect(outcome.said).toBe('a warning')
    // Still done: stderr is not a verdict, and the session said it finished.
    expect(outcome.state).toBe('done')
  })
})
