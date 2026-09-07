import { realpathSync } from 'node:fs'
import { tmpdir } from 'node:os'

import { EngineCallFailed, type CancelSignal } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { createProcessTransport } from './process-transport'

// `core` declares `CancelSignal` structurally because it may not name `AbortSignal` -
// neither the DOM nor Node is in its scope. This is where that claim is checked: if the
// shapes ever diverge, this line stops compiling here rather than at a call site.
const _realSignalFits: CancelSignal = AbortSignal.abort()
void _realSignalFits

/**
 * The engine under test is Node itself, run with `-e`. That is deliberate: every property
 * this transport promises is about how a process is started and read, so asserting them
 * against a program whose exact behaviour is written into the test is what makes a failure
 * mean the transport rather than the engine. Whether a real roadkeep answers is
 * `roadkeep-engine.test.ts`, which is a different question.
 */
const node = createProcessTransport({ command: process.execPath })

/** Run a script, with everything after `--` landing in the child's own `process.argv`. */
const script = (source: string, ...args: string[]) => ['-e', source, '--', ...args]

/** What the child saw as its arguments, without this test guessing at an index. */
async function argvSeenBy(...args: string[]): Promise<string[]> {
  const result = await node.run({
    root: tmpdir(),
    argv: script('process.stdout.write(JSON.stringify(process.argv))', ...args),
  })
  return JSON.parse(result.stdout) as string[]
}

describe('RG1: the two streams stay apart', () => {
  it('returns stdout and stderr separately, never interleaved', async () => {
    const result = await node.run({
      root: tmpdir(),
      argv: script('process.stdout.write("the answer");process.stderr.write("the warning")'),
    })

    expect(result.stdout).toBe('the answer')
    expect(result.stderr).toBe('the warning')
  })

  it('reports a non-zero exit as an answer rather than throwing', async () => {
    // `lint` exits 1 when it finds something. That is the verb working, not the call
    // failing, so a transport that threw would make the gate unreadable.
    const result = await node.run({
      root: tmpdir(),
      argv: script('process.stdout.write("found");process.exit(1)'),
    })

    expect(result.code).toBe(1)
    expect(result.stdout).toBe('found')
  })

  it('times the call', async () => {
    const result = await node.run({ root: tmpdir(), argv: script('0') })
    expect(result.durationMs).toBeGreaterThanOrEqual(0)
  })
})

describe('RG1: no shell', () => {
  it('hands a metacharacter to the engine as a character, not as syntax', async () => {
    const hostile = 'one && echo pwned || true; $(whoami) `id` "quoted" \'also\''
    const seen = await argvSeenBy(hostile)

    // One element in, one element out. Through a shell this would have become several
    // arguments, and `echo pwned` would have run as a command of its own.
    expect(seen).toContain(hostile)
    expect(seen.filter((argument) => argument.includes('pwned'))).toHaveLength(1)
  })

  it('passes an argument with spaces as one argument', async () => {
    const seen = await argvSeenBy('a b c')

    expect(seen).toContain('a b c')
    expect(seen).not.toContain('a')
  })
})

describe('RG1: the root is the working directory', () => {
  it('runs the engine in the project, not in wherever the app started', async () => {
    const result = await node.run({
      root: tmpdir(),
      argv: script('process.stdout.write(process.cwd())'),
    })

    // Through `realpath` on both sides: macOS reports /var/folders as /private/var/folders.
    expect(realpathSync(result.stdout)).toBe(realpathSync(tmpdir()))
  })
})

describe('RG1: every call is cancellable and bounded', () => {
  it('abandons a call that runs past its ceiling', async () => {
    const call = node.run({
      root: tmpdir(),
      argv: script('setTimeout(() => {}, 30000)'),
      timeoutMs: 250,
    })

    await expect(call).rejects.toBeInstanceOf(EngineCallFailed)
    await expect(call).rejects.toMatchObject({ reason: 'timeout' })
  })

  it('abandons a call the caller cancels', async () => {
    const controller = new AbortController()
    const call = node.run({
      root: tmpdir(),
      argv: script('setTimeout(() => {}, 30000)'),
      signal: controller.signal,
    })
    controller.abort()

    await expect(call).rejects.toMatchObject({ reason: 'aborted' })
  })

  it('answers immediately when the signal was already aborted', async () => {
    // The window between building the request and the spawn starting. A listener added
    // after the fact never fires, and the call would then hang for its whole ceiling.
    const call = node.run({
      root: tmpdir(),
      argv: script('setTimeout(() => {}, 30000)'),
      signal: AbortSignal.abort(),
    })

    await expect(call).rejects.toMatchObject({ reason: 'aborted' })
  })

  it('lets a call under its ceiling finish normally', async () => {
    const result = await node.run({
      root: tmpdir(),
      argv: script('process.stdout.write("in time")'),
      timeoutMs: 30000,
    })

    expect(result.stdout).toBe('in time')
    expect(result.code).toBe(0)
  })
})

describe('RG1: an engine that is not there', () => {
  it('says the call never happened rather than reporting an exit code', async () => {
    const missing = createProcessTransport({ command: 'no-such-engine-anywhere' })
    const call = missing.run({ root: tmpdir(), argv: ['--version'] })

    await expect(call).rejects.toMatchObject({ reason: 'unspawnable' })
  })
})
