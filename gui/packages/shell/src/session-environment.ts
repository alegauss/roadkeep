import { loggedIn, type Transport } from '@rk/core'

/**
 * The environment a session runs in (RG205).
 *
 * `claude -p` takes `ANTHROPIC_API_KEY` over a login whenever the variable is set, and never
 * asks — the interactive CLI does ask. A machine that carries the variable for other tools
 * then bills a session to that key while the person's own terminal runs on their plan, and a
 * key with no credit ends the session before it starts.
 *
 * **The login is asked without the key.** Where the variable is set, `claude auth status`
 * runs with it left out; a login that answers on its own means the session is spawned
 * without it too. Every other answer keeps the environment as it was, so a machine whose one
 * credential is the key still starts a session, exactly as before.
 *
 * **One variable and nothing else.** `ANTHROPIC_AUTH_TOKEN` goes with `ANTHROPIC_BASE_URL` to
 * a gateway, and a login sent there would be refused. Nothing is written either: the person's
 * environment stays theirs, and only this child does not inherit the one name.
 */

/** The variable that overrides a login in a headless session. */
export const OVERRIDING_KEY = 'ANTHROPIC_API_KEY'

/** Long enough for a cold start; a check that hangs past it keeps the environment. */
const CEILING_MS = 15000

/** A transport for this command, spawned with this environment. */
export type EnvironmentTransportFor = (
  command: readonly string[],
  env: NodeJS.ProcessEnv,
) => Transport

/**
 * The environment without the overriding key, or null where it holds none.
 *
 * Matched whatever the case, because Windows reads `Anthropic_Api_Key` as the same variable
 * and a copy of `process.env` keeps the spelling it was set with.
 */
export function withoutKey(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv | null {
  let found = false
  const kept: NodeJS.ProcessEnv = {}
  for (const [name, value] of Object.entries(env)) {
    if (name.toUpperCase() === OVERRIDING_KEY) {
      if (value !== undefined && value !== '') found = true
      continue
    }
    kept[name] = value
  }
  return found ? kept : null
}

export interface SessionEnvironmentOptions {
  /** The environment a session would otherwise inherit. `process.env` unless a test says. */
  readonly env?: NodeJS.ProcessEnv
  readonly timeoutMs?: number
}

export async function sessionEnvironment(
  transportFor: EnvironmentTransportFor,
  command: readonly string[],
  root: string,
  options: SessionEnvironmentOptions = {},
): Promise<NodeJS.ProcessEnv> {
  const env = options.env ?? process.env
  const kept = withoutKey(env)
  // No key, nothing to ask: the session inherits what it always did.
  if (kept === null) return env

  try {
    const answer = await transportFor(command, kept).run({
      root,
      argv: ['auth', 'status'],
      timeoutMs: options.timeoutMs ?? CEILING_MS,
    })
    return loggedIn(answer.stdout) ? kept : env
  } catch {
    // Unspawnable, timed out or cancelled: no login was shown, so the key stays.
    return env
  }
}
