import { openProject, type Opening, type OpenOptions, type Transport } from '@rk/core'

import { engineCandidates, samePathPart, type CandidateOptions } from './engine-candidates'
import { stampGoverned } from './governed-stamp'
import { createMcpTransport, type McpTransport } from './mcp-transport'
import { createProcessTransport } from './process-transport'

/**
 * Opening a project on this machine, which is the half of RG103 that needs a machine.
 *
 * `core` owns the order — resolve, pool, read `config`, cache on what it declared, read
 * `commands` — and owns it because that order is the same behind an HTTP handler as it is
 * behind a child process. What is here is the three things that order cannot supply for
 * itself: the command lines worth trying, a transport that starts one, and a stamp taken
 * over files on a disk.
 *
 * This is the call a screen makes. Everything above it reads through
 * `project.client`, and nothing above it assembles a transport again.
 *
 * **The transport it builds keeps the engine** (RG122). RG101 measured eight reads of this
 * repository at 5904ms spawned and 45ms held, and until this line the app's own open path
 * built the one that spawns — so the transport that reads in six milliseconds was proven by
 * a test and reached by nothing a person would run. What made that a task rather than a
 * one-word change is the process: a held engine outlives the call, so what this hands back
 * has a `close`, and a project nobody closes is a Python standing in a directory Windows
 * will then not let go of.
 *
 * **The engine that spawns is still here, underneath.** It answers three things the held one
 * cannot: resolution, which asks with an argv and no tool call; the reads `roadkeep mcp`
 * does not publish, `stats` and `commands` among them; and any project whose engine has no
 * `mcp` surface at all. It is built per candidate rather than shared, so a read that falls
 * through is answered by the copy standing behind that server and never by another one.
 */

export interface OpenHereOptions extends Omit<OpenOptions, 'stampFor' | 'samePart' | 'closing'> {
  /** The interpreter and the PATH name, for a machine that spells them differently. */
  readonly candidates?: CandidateOptions
}

export function openHere(root: string, options: OpenHereOptions = {}): Promise<Opening> {
  const { candidates, ...rest } = options

  // Every transport this open built, in the order it built them. Resolution asks each
  // candidate and the chosen one is asked again, so there are several — and all but the one
  // that answered hold nothing, since a request with no tool call reaches the fallback
  // before a process is started. A list and not a map: what `closing` owes is everything
  // this call made, and telling two identical command lines apart adds nothing to that.
  const made: McpTransport[] = []
  const transportFor = (engine: readonly string[]): Transport => {
    const held = createMcpTransport({
      engine,
      fallback: createProcessTransport({ command: engine[0] ?? '', prefixArgs: engine.slice(1) }),
      ...(options.timeoutMs === undefined ? {} : { timeoutMs: options.timeoutMs }),
    })
    made.push(held)
    return held
  }

  return openProject(root, engineCandidates(root, candidates ?? {}), transportFor, {
    ...rest,
    // The comparison `core` cannot make, and the stamp it cannot take (RG65, RG7).
    samePart: samePathPart,
    stampFor: (asked, governed) => Promise.resolve(stampGoverned(asked, governed)),
    // Awaited to the last exit rather than fired off: whoever closes a project is often the
    // one about to remove the directory that server had as its working directory.
    closing: async () => {
      await Promise.all(made.splice(0).map((held) => held.close()))
    },
  })
}
