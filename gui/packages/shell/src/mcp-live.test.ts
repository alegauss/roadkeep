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
      expect(spawned).toBe(0)
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
