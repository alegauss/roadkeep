import { buildArgv, buildCall, VERBS, type VerbInputs, type VerbName } from '@rk/core'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { buildFixture, type Fixture } from './fixture'
import { CEILING, LAUNCHER, REPO, liveEngine as overProcess } from './live'
import { createMcpTransport, type McpTransport } from './mcp-transport'

/**
 * RG101: the third transport, against a real engine.
 *
 * A spawned call costs about a second and a half and almost all of it is Python starting.
 * This one starts a `roadkeep mcp` per project and keeps it, so the interpreter is paid for
 * once. What has to be true for that to be a transport swap rather than a second reader is
 * that the bytes are the same — which is what this asks, verb by verb, against the same
 * fixture the process transport reads.
 *
 * The comparison goes through the transport rather than the client for the reason the HTTP
 * seam does: a client reads its answer into a value, and two values comparing equal would
 * not say whether the same bytes arrived.
 */

let fixture: Fixture
let overMcp: McpTransport

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
  blockList: {},
  sectionShow: { anchor: 'FX3' },
}

beforeAll(async () => {
  fixture = await buildFixture(overProcess, { open: 3, shipped: 1, deferred: 1 })
  overMcp = createMcpTransport({
    engine: ['python', LAUNCHER],
    fallback: overProcess,
    timeoutMs: CEILING,
  })
}, 180000)

afterAll(async () => {
  // Awaited before the fixture goes: a server's working directory is the fixture, and on
  // Windows a process that has been killed still holds that directory until it exits.
  await overMcp.close()
  fixture.dispose()
})

/**
 * The payload, with the two differences that belong to the surfaces rather than to the
 * answer. Both were measured here, and neither is one this app can remove honestly.
 *
 * **A line ending.** A spawned Python writes a bare line feed and Windows text-mode stdout
 * turns it into a carriage return and a line feed on the way through the pipe; the MCP
 * surface carries the same string inside a JSON frame, where no console touches it. Making
 * them agree would mean rewriting what one of the two engines actually wrote.
 *
 * **A terminator.** The CLI prints the payload, so it ends in a newline; the tool answers
 * with the string and stops. One character, and it is `print`'s rather than the document's.
 *
 * Nothing above the transport can tell, because every reader parses this as JSON and the
 * two are then the same document. A caller comparing payload *text* could — which is worth
 * knowing rather than hiding, and is why this is a named function with a reason on it
 * instead of a `trim` inside an assertion.
 */
const CRLF = String.fromCharCode(13, 10)
const LF = String.fromCharCode(10)

function payload(stdout: string): string {
  return stdout.replaceAll(CRLF, LF).replace(/\n$/, '')
}

/**
 * Which build wrote a payload, read off the payload itself.
 *
 * Every one of them carries it, which is what makes an engine rebuilt mid-run visible as
 * something other than sixteen unrelated diffs.
 */
function engineVersion(stdout: string): string {
  return /"version":\s*"([^"]*)"/.exec(payload(stdout))?.[1] ?? ''
}

/** The same call, both ways: an argv for one transport and a tool call for the other. */
function asked(verb: VerbName) {
  return {
    root: fixture.root,
    argv: buildArgv(fixture.root, verb, READS[verb]),
    call: buildCall(verb, READS[verb]),
    timeoutMs: CEILING,
  }
}

describe('RG101: the whole read surface, over a held engine', () => {
  it('covers every verb the client can build a command line for', () => {
    expect(Object.keys(READS).sort()).toEqual(Object.keys(VERBS).sort())
  })

  for (const verb of Object.keys(VERBS) as VerbName[]) {
    it(`answers identically for ${verb}`, async () => {
      const [bySpawn, byHeld] = await Promise.all([
        overProcess.run(asked(verb)),
        overMcp.run(asked(verb)),
      ])

      // A held process pins the engine it started with; a spawn loads whatever is on disk
      // now. So a roadkeep rebuilt underneath this run makes every payload differ on its
      // `version`, and reporting that as a transport defect would send a reader looking in
      // the wrong place. Named here for the same reason RG84 names it once per run.
      const moved = engineVersion(byHeld.stdout) !== engineVersion(bySpawn.stdout)
      expect(
        moved,
        `the engine moved under this run — the held process is roadkeep ${engineVersion(byHeld.stdout)}` +
          ` and a spawn now loads ${engineVersion(bySpawn.stdout)}. Nothing here is a claim about` +
          ' either transport until they are one build.',
      ).toBe(false)

      // The payload, byte for byte once the console's newline is out of it. Anything the
      // surface added or lost shows here.
      expect(payload(byHeld.stdout)).toBe(payload(bySpawn.stdout))
      // And the exit code, because `lint` exits 1 with an ordinary payload: a transport
      // that read the code as a failure would lose an answer the other one keeps.
      expect(byHeld.code).toBe(bySpawn.code)
    })
  }
})

describe('RG101: what the process being held changes', () => {
  it('holds one engine per root and not one per call', () => {
    // The whole point. A second process per read would be the spawn cost again with a
    // protocol on top of it.
    expect(overMcp.held).toBe(1)
  })

  it('starts a second engine for a second root, since the surface takes no project', async () => {
    // `roadkeep mcp` answers about the directory it was started in and takes no `-C`, so
    // reading two projects means two servers. Stated because it is the cost of this design.
    await overMcp.run({
      root: REPO,
      argv: buildArgv(REPO, 'config', {}),
      call: buildCall('config', {}),
      timeoutMs: CEILING,
    })

    expect(overMcp.held).toBe(2)
  })

  it('answers about the root it was started in, and never about this repository', async () => {
    // The failure a held process invites: one server answering for the wrong project
    // because somebody reused it. The fixture's roadmap and this one are different files.
    const here = await overMcp.run(asked('config'))

    expect(here.stdout).toContain(fixture.root.replaceAll('\\', '/'))
  })
})

describe('RG131: a read somebody stopped wanting', () => {
  it('lets a call cancelled in flight go at once, and keeps the engine for the next', async () => {
    // `lint` over this repository is the slowest read the surface serves — about 160ms
    // held — which is room to cancel one after its frame has gone out.
    const warm = await overMcp.run({
      root: REPO,
      argv: buildArgv(REPO, 'engines', {}),
      call: buildCall('engines', {}),
      timeoutMs: CEILING,
    })
    expect(warm.code).toBe(0)
    const holding = overMcp.held

    const stopped = new AbortController()
    const cancelled = overMcp.run({
      root: REPO,
      argv: buildArgv(REPO, 'lint', {}),
      call: buildCall('lint', {}),
      timeoutMs: CEILING,
      signal: stopped.signal,
    })
    setTimeout(() => {
      stopped.abort()
    }, 5)

    // Refused as a cancellation, which is what the process transport says for the same
    // thing — and not as an engine that could not start, which is what a caller would then
    // go and debug.
    await expect(cancelled).rejects.toMatchObject({ name: 'EngineCallFailed', reason: 'aborted' })

    // The server was only abandoned, never lost: still held, the same count. And the answer
    // it finishes anyway is dropped, so the call after it gets its own — measured, this build
    // does answer a cancelled call, which is exactly the frame that must not land elsewhere.
    expect(overMcp.held).toBe(holding)
    await new Promise((done) => setTimeout(done, 400))
    const after = await overMcp.run({
      root: REPO,
      argv: buildArgv(REPO, 'config', {}),
      call: buildCall('config', {}),
      timeoutMs: CEILING,
    })
    expect(JSON.parse(payload(after.stdout))).toHaveProperty('keys')
  })

  it('starts nothing for a call cancelled before it began', async () => {
    // The pool's rule, held by the transport too: a call nobody still wants must not become
    // a process — and a first read of a root would start one, handshake and all.
    const fresh = createMcpTransport({
      engine: ['python', LAUNCHER],
      fallback: overProcess,
      timeoutMs: CEILING,
    })

    try {
      await expect(
        fresh.run({ ...asked('list'), signal: AbortSignal.abort() }),
      ).rejects.toMatchObject({ reason: 'aborted' })
      expect(fresh.held).toBe(0)
    } finally {
      await fresh.close()
    }
  })
})

describe('RG135: an engine that cannot hold a session', () => {
  it('reads anyway, and keeps why in the engine`s own words', async () => {
    // What a checkout caught mid-save looks like from here: a process that writes a
    // traceback and exits before the handshake. Spelled as its own Python rather than
    // waited for, and answered by a fallback that says what it is.
    const traceback = 'ModuleNotFoundError: No module named roadkeep.backlog'
    const broken = [
      'python',
      '-c',
      `import sys; sys.stderr.write("Traceback (most recent call last):\\n${traceback}\\n"); sys.exit(3)`,
    ]
    const fellBack = { code: 0, stdout: '{"fell":"back"}', stderr: '', durationMs: 1 }
    const unheldable = createMcpTransport({
      engine: broken,
      fallback: { run: () => Promise.resolve(fellBack) },
      timeoutMs: CEILING,
    })

    try {
      // Slow beats broken, which is RG122's call and stays: the read is answered.
      expect(await unheldable.run(asked('list'))).toEqual(fellBack)
      expect(unheldable.held).toBe(0)

      // And the reason is kept — the exit, then the traceback's own last line, which names
      // the module that would not import and is the whole of the diagnosis.
      const why = unheldable.unheld.get(fixture.root) ?? ''
      expect(why).toContain('exited with 3')
      expect(why).toContain(traceback)
    } finally {
      await unheldable.close()
    }
  })
})

describe('RG101: a call it cannot serve', () => {
  it('sends a request with no tool call to the transport that spawns', async () => {
    // A door's own argv is composed by the engine, and nothing here turned it into a tool.
    // Falling back is what keeps every path working rather than only the ones this knows.
    const byFallback = await overMcp.run({
      root: fixture.root,
      argv: buildArgv(fixture.root, 'list', {}),
      timeoutMs: CEILING,
    })
    const bySpawn = await overProcess.run(asked('list'))

    expect(payload(byFallback.stdout)).toBe(payload(bySpawn.stdout))
  })

  it('spawns for an argument the tool schema does not publish (RG122)', async () => {
    // The gap the handshake cannot see. `brief` is published, so the tool set says yes —
    // and its schema takes `id`, `block`, `designed` and `have` and no `claim`, which is
    // withheld from this surface on purpose because a read that writes is a read a caller
    // stops making freely. Nothing but calling it says so, so a refusal has to be a
    // fall-through: reported here, the one read that writes reached the client as
    // unreadable prose.
    let spawned = 0
    const counting = {
      run: async (request: Parameters<typeof overProcess.run>[0]) => {
        spawned += 1
        return overProcess.run(request)
      },
    }
    const routed = createMcpTransport({
      engine: ['python', LAUNCHER],
      fallback: counting,
      timeoutMs: CEILING,
    })

    try {
      const claimed = await routed.run({
        root: fixture.root,
        argv: buildArgv(fixture.root, 'brief', { claim: true }),
        call: buildCall('brief', { claim: true }),
        timeoutMs: CEILING,
      })

      expect(spawned).toBe(1)
      // The whole point of falling back: what comes out is the document the CLI prints,
      // and the claim actually happened.
      expect(claimed.code).toBe(0)
      expect(JSON.parse(payload(claimed.stdout))).toMatchObject({ claimed: { taken: true } })
    } finally {
      await routed.close()
    }
  })

  it('spawns for a verb the tool set does not publish, and not for one it does', async () => {
    // The case the design named: the CLI runs verbs this surface does not. `stats` is one
    // of two reads in that gap, and what makes the transport a drop-in rather than a
    // narrower one is that it sends those to the transport that spawns instead of refusing
    // them. Counted rather than asserted about, because the whole claim is *which* one ran.
    let spawned = 0
    const counting = {
      run: async (request: Parameters<typeof overProcess.run>[0]) => {
        spawned += 1
        return overProcess.run(request)
      },
    }
    const routed = createMcpTransport({
      engine: ['python', LAUNCHER],
      fallback: counting,
      timeoutMs: CEILING,
    })

    try {
      const published = await routed.run(asked('list'))
      // Named when it fails (RG135). This went red once as `expected 1 to be +0` with nothing
      // near it changed — a server started mid-save that did not import — and learning that
      // took a `git log` in another repository. The reason is kept now; this prints it.
      expect(
        spawned,
        `a read the surface publishes was spawned: ${routed.unheld.get(fixture.root) ?? 'no handshake failed'}`,
      ).toBe(0)
      expect(payload(published.stdout)).not.toBe('')

      const unpublished = await routed.run(asked('stats'))
      expect(spawned).toBe(1)
      expect(payload(unpublished.stdout)).toBe(
        payload((await overProcess.run(asked('stats'))).stdout),
      )
    } finally {
      await routed.close()
    }
  })
})
