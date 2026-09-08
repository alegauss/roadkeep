import { openProject, type Opening, type OpenOptions } from '@rk/core'

import { engineCandidates, samePathPart, type CandidateOptions } from './engine-candidates'
import { stampGoverned } from './governed-stamp'
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
 */

export interface OpenHereOptions extends Omit<OpenOptions, 'stampFor' | 'samePart'> {
  /** The interpreter and the PATH name, for a machine that spells them differently. */
  readonly candidates?: CandidateOptions
}

export function openHere(root: string, options: OpenHereOptions = {}): Promise<Opening> {
  const { candidates, ...rest } = options

  return openProject(
    root,
    engineCandidates(root, candidates ?? {}),
    (engine) => createProcessTransport({ command: engine[0] ?? '', prefixArgs: engine.slice(1) }),
    {
      ...rest,
      // The comparison `core` cannot make, and the stamp it cannot take (RG65, RG7).
      samePart: samePathPart,
      stampFor: (asked, governed) => Promise.resolve(stampGoverned(asked, governed)),
    },
  )
}
