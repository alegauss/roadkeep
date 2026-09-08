import path from 'node:path'

import {
  createClient,
  EngineCallFailed,
  VERBS,
  type Transport,
  type VerbInputs,
  type VerbName,
} from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { serveEngine, type Handler } from './engine-handler'
import { buildFixture, type Fixture } from './fixture'
import { createHttpTransport } from './http-transport'
import { createProcessTransport } from './process-transport'

/**
 * The seam, proven rather than described.
 *
 * Every read this client makes goes over two real transports — a process and an HTTP
 * handler — and the two answers are compared. What that catches is a path, a working
 * directory or an exit code leaking upward, which is what a review does not.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const overProcess = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })

let fixture: Fixture
let handler: Handler
let overHttp: Transport

/** Every read verb, with inputs valid for the fixture. The whole surface, not a sample. */
const READS: { [K in VerbName]: VerbInputs[K] } = {
  list: {},
  show: { id: 'FX3' },
  stats: {},
  brief: { id: 'FX3' },
  deps: { id: 'FX3' },
  delivered: { block: 'A' },
  reversals: {},
  budget: { block: 'A', symptom: 'a draft' },
  nonGoalList: {},
  criterionList: {},
  lint: {},
  engines: {},
  explain: { code: 'symptom.too-long' },
  commands: {},
  config: {},
  pick: {},
}

beforeAll(async () => {
  fixture = await buildFixture(overProcess, { open: 3, shipped: 1, deferred: 1 })
  handler = await serveEngine(overProcess)
  overHttp = createHttpTransport({ url: handler.url, timeoutMs: CEILING })
}, 180000)

afterAll(async () => {
  await handler.close()
  fixture.dispose()
})

describe('RG48: the whole read surface, over both transports', () => {
  it('covers every verb the client can build a command line for', () => {
    // The guard: a verb added to the table without a row here would be a verb the seam is
    // never proven for.
    expect(Object.keys(READS).sort()).toEqual(Object.keys(VERBS).sort())
  })

  for (const verb of Object.keys(VERBS) as VerbName[]) {
    it(`answers identically for ${verb}`, async () => {
      const input = READS[verb]
      const [byProcess, byHttp] = await Promise.all([
        createClient(overProcess).call(fixture.root, verb, input, { timeoutMs: CEILING }),
        createClient(overHttp).call(fixture.root, verb, input, { timeoutMs: CEILING }),
      ])

      // The payload, byte for byte. Anything the transport added or lost shows here.
      expect(byHttp.stdout).toBe(byProcess.stdout)
      expect(byHttp.stderr).toBe(byProcess.stderr)
      // And the exit code: `lint` exits 1 with an ordinary payload, so a transport reading
      // the code as a failure would lose an answer the other one keeps.
      expect(byHttp.code).toBe(byProcess.code)
    })
  }
})

describe('RG48: what a leak would look like', () => {
  it("carries the root as data, not as anybody's working directory", async () => {
    // The HTTP transport has no child and no directory of its own. A read that had come to
    // depend on `cwd` would answer about this repository here and about the fixture there.
    const overThere = await createClient(overHttp).call(
      fixture.root,
      'list',
      {},
      {
        timeoutMs: CEILING,
      },
    )
    const overHere = await createClient(overHttp).call(REPO, 'list', {}, { timeoutMs: CEILING })

    expect(overThere.stdout).not.toBe(overHere.stdout)
    expect(overThere.stdout).toContain('FX')
    expect(overHere.stdout).toContain('RG')
  })

  it('keeps a non-zero exit that is an answer', async () => {
    // The fixture's gate finds something, or it does not — either way the two agree, and
    // an exit of 1 arrives as a number rather than as an exception.
    const byProcess = await createClient(overProcess).call(
      fixture.root,
      'lint',
      {},
      {
        timeoutMs: CEILING,
      },
    )
    const byHttp = await createClient(overHttp).call(
      fixture.root,
      'lint',
      {},
      {
        timeoutMs: CEILING,
      },
    )

    expect([0, 1]).toContain(byHttp.code)
    expect(byHttp.code).toBe(byProcess.code)
    expect(JSON.parse(byHttp.stdout)).toEqual(JSON.parse(byProcess.stdout))
  })

  it('fails the way the other one fails, when it cannot answer at all', async () => {
    // Both raise `EngineCallFailed` rather than each inventing its own failure — which is
    // what lets everything above the transport handle one kind of thing.
    const nowhere = createHttpTransport({ url: 'http://127.0.0.1:1', timeoutMs: 2000 })

    await expect(
      nowhere.run({ root: fixture.root, argv: ['-C', fixture.root, 'list', '--json'] }),
    ).rejects.toBeInstanceOf(EngineCallFailed)
  })

  it('abandons a call that runs past its ceiling, as the other one does', async () => {
    const slow = createHttpTransport({ url: handler.url, timeoutMs: 1 })

    await expect(
      slow.run({ root: fixture.root, argv: ['-C', fixture.root, 'list', '--json'], timeoutMs: 1 }),
    ).rejects.toMatchObject({ reason: 'timeout' })
  })

  it("is cancellable from above, which is the caller's act and not the ceiling", async () => {
    const controller = new AbortController()
    const call = overHttp.run({
      root: fixture.root,
      argv: ['-C', fixture.root, 'list', '--json'],
      signal: controller.signal,
      timeoutMs: CEILING,
    })
    controller.abort()

    await expect(call).rejects.toMatchObject({ reason: 'aborted' })
  })
})
