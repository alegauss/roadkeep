import path from 'node:path'

import { buildArgv, createClient, explainFailure, type VerbInputs, type VerbName } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { createProcessTransport } from './process-transport'

/**
 * RG1's symptom is that no code here can fetch a payload. These are the tests that make
 * that false, so they run against a real roadkeep rather than a fake transport.
 *
 * The engine is the launcher this repository commits, driven by whatever `python` is on
 * PATH. That is not engine resolution — RG2 owns which roadkeep answers, and this one is
 * named rather than discovered, which is the point. The project is this repository, whose
 * governed files are the fixture: it has a roadkeep.toml and a backlog, and no test here
 * writes to either.
 *
 * If these fail with `unspawnable`, python is missing rather than the transport being
 * broken. That is a real dependency of this suite and it is stated here rather than
 * skipped around: a test that quietly passes when the engine is absent would report a
 * clean run for the same reason a working one does.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')

const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
const client = createClient(engine)

/** Generous: the engine is a Python start, measured around 360ms, and CI is slower. */
const CEILING = 30000

/**
 * The bytes, which is what half of these are about.
 *
 * A client reads its answer with the verb's own shape and hands back a value (RG66), so
 * the stream, the exit code and the prose on stderr are questions for the transport — the
 * one thing that still has them. `buildArgv` is the same command line either way.
 */
function raw<K extends VerbName>(verb: K, input: VerbInputs[K]) {
  return engine.run({ root: REPO, argv: buildArgv(REPO, verb, input), timeoutMs: CEILING })
}

describe('RG1: a payload this app can actually fetch', () => {
  it('reads the backlog and gets JSON back on stdout', async () => {
    const result = await raw('list', { block: 'A' })

    expect(result.code).toBe(0)
    const payload = JSON.parse(result.stdout) as { file: string; tasks: unknown[] }
    expect(payload.file).toContain('ROADMAP.md')
    expect(Array.isArray(payload.tasks)).toBe(true)
  })

  it("accepts the real answer through RG3's shape, so the shape is not fiction", async () => {
    // One shape against one live payload. Holding *every* shape against every verb is
    // RG4's contract test; this is the smaller claim that these were written from real
    // output rather than from memory, which is the way a hand-written shape goes wrong.
    const answer = await client.call(REPO, 'list', { block: 'A' }, { timeoutMs: CEILING })

    expect(
      answer.ok,
      answer.ok ? '' : explainFailure(answer.failure, { verb: 'list', engineVersion: 'live' }),
    ).toBe(true)
    if (!answer.ok || answer.value.kind === 'refused') return
    expect(answer.value.value.tasks.length).toBeGreaterThan(0)
    expect(answer.value.value.standing?.block).toBe('A')
  })

  it('answers about the project it was given, not the directory the test runs in', async () => {
    // The whole reason `-C` is passed as well as the working directory. Vitest runs from
    // the repository root, so a transport ignoring both would still look right here - the
    // package directory is what separates them.
    const result = await raw('stats', {})

    expect(result.code).toBe(0)
    expect((JSON.parse(result.stdout) as { file: string }).file).toContain('ROADMAP.md')
  })

  it('brings a refusal back as a payload rather than as prose', async () => {
    // An id that does not exist. Under `--json` the engine answers a refusal on *stdout*,
    // structured, and repeats it as prose on stderr - so a client has a machine-readable
    // refusal without parsing English. That is what RG5 builds the field-level refusal on,
    // and it is asserted here because it was assumed the other way round first.
    const result = await raw('show', { id: 'RG9999' })

    expect(result.code).not.toBe(0)
    const refusal = JSON.parse(result.stdout) as { refused: unknown[]; said: string }
    expect(Array.isArray(refusal.refused)).toBe(true)
    expect(refusal.said).toContain('RG9999')

    // And the prose is on the other stream, which is the half a merged reader loses.
    expect(result.stderr).not.toBe('')
  })

  it('RG66: hands that refusal up as a refusal and not as an unreadable answer', async () => {
    // The other end of the same call. A client that returned stdout left every caller to
    // notice this for itself; the shape the verb declares does not fit a refusal, so a
    // caller that forgot would have read `show`'s own gate finding as a broken payload.
    const answer = await client.call(REPO, 'show', { id: 'RG9999' }, { timeoutMs: CEILING })

    expect(answer.ok).toBe(true)
    if (!answer.ok) return
    expect(answer.value.kind).toBe('refused')
    if (answer.value.kind !== 'refused') return
    expect(answer.value.refusal.said).toContain('RG9999')
  })

  it('carries a non-zero exit back as an answer, which is how the gate reads', async () => {
    const result = await raw('lint', {})

    // 0 or 1 are both the gate working. Anything else is the call going wrong.
    expect([0, 1]).toContain(result.code)
    expect(JSON.parse(result.stdout)).toHaveProperty('clean')

    // And the payload survives the exit code: an answer is what `said` decides, not `code`.
    const answer = await client.call(REPO, 'lint', {}, { timeoutMs: CEILING })
    expect(answer.ok && answer.value.kind).toBe('payload')
  })
})
