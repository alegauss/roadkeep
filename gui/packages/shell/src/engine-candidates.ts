import { existsSync } from 'node:fs'
import path from 'node:path'

/**
 * The command lines worth trying for a project, in the order they should be tried.
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
