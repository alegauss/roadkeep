import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import path from 'node:path'

/**
 * Where to look for the command that runs a session, in the order to look.
 *
 * The half of agent resolution that needs a filesystem, which is why it is here and not in
 * `core`. It discovers nothing about versions — that is `--version`'s answer and this only
 * supplies the ways of asking.
 *
 * **A `claude` on PATH comes first**, because it is the one the person's own shell would
 * run and therefore the one their authentication and settings belong to. The install
 * locations after it are for a machine whose PATH a windowed app did not inherit, which on
 * macOS and Windows is the ordinary case rather than the exception.
 *
 * Nothing bundled ever appears here, for the reason the engine list gives: a `claude`
 * shipped inside this app would sign somebody's work in with an account they did not
 * choose.
 */

export interface AgentCandidateOptions {
  /** The name a Claude Code on PATH would go by. */
  readonly onPath?: string
  /** The person's home directory. Taken as an argument so a test can point it elsewhere. */
  readonly home?: string
}

/** Where an install puts the executable, relative to a home directory. */
const UNDER_HOME = [
  path.join('.local', 'bin', 'claude'),
  path.join('.claude', 'local', 'claude'),
  path.join('AppData', 'Local', 'Programs', 'claude', 'claude.exe'),
]

export function agentCandidates(
  options: AgentCandidateOptions = {},
): readonly (readonly string[])[] {
  const onPath = options.onPath ?? 'claude'
  const home = options.home ?? homedir()
  const candidates: string[][] = [[onPath]]

  for (const relative of UNDER_HOME) {
    const full = path.join(home, relative)
    if (existsSync(full)) candidates.push([full])
  }

  return candidates
}
