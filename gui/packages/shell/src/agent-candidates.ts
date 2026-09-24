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
  /** A command put before every other candidate: what `agentOverride` read, or nothing. */
  readonly override?: readonly string[] | null
}

/** The variable an unpackaged app reads for an agent of somebody's choosing (RG210). */
export const AGENT_VAR = 'ROADKEEP_AGENT'

/**
 * The agent a variable names, or null (RG210).
 *
 * **Read only unpackaged.** A shipped window never runs an agent a variable chose: an
 * environment is easier to reach than a binary on PATH, and the person who installed the app
 * chose Claude Code, not whatever a variable says. Unpackaged — `npm run dev`, `npm start`,
 * the screenshot run — is a developer's own tree, and the session screen names the command it
 * started, so a scripted agent shows as one.
 *
 * **A JSON argv**, the one spelling that needs no quoting rules: a path with spaces is an
 * element, never something split. Anything else is ignored rather than guessed at.
 */
export function agentOverride(value: string | undefined, packaged: boolean): string[] | null {
  if (packaged || value === undefined || value === '') return null
  let parsed: unknown
  try {
    parsed = JSON.parse(value)
  } catch {
    return null
  }
  if (!Array.isArray(parsed) || parsed.length === 0) return null
  const argv: string[] = []
  for (const part of parsed) {
    if (typeof part !== 'string' || part === '') return null
    argv.push(part)
  }
  return argv
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
  const candidates: string[][] = [
    ...(options.override === undefined || options.override === null ? [] : [[...options.override]]),
    [onPath],
  ]

  for (const relative of UNDER_HOME) {
    const full = path.join(home, relative)
    if (existsSync(full)) candidates.push([full])
  }

  return candidates
}
