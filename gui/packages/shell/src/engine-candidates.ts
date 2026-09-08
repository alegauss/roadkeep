import { existsSync } from 'node:fs'
import path from 'node:path'

import type { SamePart } from '@rk/core'

import { CASE_INSENSITIVE } from './root-paths'

/**
 * The command lines worth trying for a project, in the order they should be tried — and
 * how two of them are told apart.
 *
 * This is the half of engine resolution that needs a filesystem, which is why it is here
 * and not in `core`. It discovers nothing about *versions* — that is `engines --json`'s
 * answer and this only supplies the ways of asking.
 *
 * The order is the argument. The committed launcher comes first because it is the file
 * the project itself points its harness at, and because it does its own resolution:
 * `$ROADKEEP_HOME`, a sibling checkout, then a cached clone. A `roadkeep` on PATH comes
 * last and only as a fallback, since it is precisely the copy `engines` exists to say a
 * project may not be running.
 *
 * Nothing bundled ever appears here. An engine shipped inside this app would judge every
 * project by a version none of them declared.
 */

/** The launcher `roadkeep install --committed` writes into an adopting repository. */
export const COMMITTED_LAUNCHER = path.join('.claude', 'hooks', 'roadkeep-launch.py')

export interface CandidateOptions {
  /** The interpreter the committed launcher is run with. */
  readonly python?: string
  /** The name a roadkeep on PATH would go by. */
  readonly onPath?: string
}

export function engineCandidates(
  root: string,
  options: CandidateOptions = {},
): readonly (readonly string[])[] {
  const python = options.python ?? 'python'
  const onPath = options.onPath ?? 'roadkeep'
  const candidates: string[][] = []

  const launcher = path.join(root, COMMITTED_LAUNCHER)
  if (existsSync(launcher)) {
    candidates.push([python, launcher])
  }

  candidates.push([onPath])
  return candidates
}

/**
 * Whether two parts of a command line name the same thing on this machine.
 *
 * The comparison `resolveEngine` is handed, and the other half of "needs a filesystem".
 * `invoke` is written with posix separators while a candidate built here holds the
 * platform's, so on Windows `D:/proj/.claude/hooks/roadkeep-launch.py` and
 * `D:\proj\.claude\hooks\roadkeep-launch.py` are one file spelled twice — and a literal
 * comparison paid a second interpreter start, about 2.3 seconds, on every resolution to
 * discover that.
 *
 * Normalised rather than resolved: `path.resolve` would make a bare `roadkeep` a file in
 * whichever directory this process happens to be in, and a PATH lookup is not a path.
 * Case is folded only where the platform says it does not distinguish a file, which is why
 * this cannot live in `core` — on Linux a backslash is an ordinary character in a name,
 * and folding it there would report two different files as one.
 */
export const samePathPart: SamePart = (left, right) => {
  if (left === right) return true
  if (left === '' || right === '') return false

  const key = (part: string): string => {
    const normalised = path.normalize(part)
    return CASE_INSENSITIVE ? normalised.toLowerCase() : normalised
  }
  return key(left) === key(right)
}
