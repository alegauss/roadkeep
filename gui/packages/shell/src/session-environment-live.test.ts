import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { createProcessTransport } from './process-transport'
import { removeTree } from './scratch'
import { OVERRIDING_KEY, sessionEnvironment } from './session-environment'
import { startSession } from './session-process'

/**
 * RG205 through real processes, with a `claude` that is not Claude.
 *
 * A real `auth status` answers about this machine's login, which a runner does not have and
 * a developer's may, so nothing here asks the real one. The fake answers `loggedIn: true`
 * only where it cannot see the key — so a check that leaked the variable into its own child
 * reads as no login, and the key stays where the test says it must go.
 *
 * The session half is a node child that says whether it can see the key, started through
 * `startSession` with the environment the check decided.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const KEY = 'sk-ant-api-not-a-real-one'

const homes: string[] = []

afterAll(() => {
  for (const home of homes) removeTree(home)
})

/** A `claude` whose `auth status` reports a login, or none, and only when it sees no key. */
function fakeAuth(login: boolean): readonly string[] {
  const home = mkdtempSync(path.join(tmpdir(), 'rk-fake-auth-'))
  homes.push(home)
  const file = path.join(home, 'claude.mjs')
  writeFileSync(
    file,
    [
      'const [verb, sub] = process.argv.slice(2)',
      "if (verb !== 'auth' || sub !== 'status') process.exit(2)",
      `const keyed = Object.keys(process.env).some((name) => name.toUpperCase() === '${OVERRIDING_KEY}')`,
      `process.stdout.write(JSON.stringify({ loggedIn: ${String(login)} && !keyed }) + '\\n')`,
      `process.exit(${login ? '0' : '1'})`,
    ].join('\n'),
    'utf8',
  )
  return [process.execPath, file]
}

const transportFor = (command: readonly string[], env: NodeJS.ProcessEnv) =>
  createProcessTransport({ command: command[0] ?? '', prefixArgs: command.slice(1), env })

/** What a session started in this environment can see of the key. */
async function sessionSees(env: NodeJS.ProcessEnv): Promise<string> {
  const probe = [
    `const seen = process.env.${OVERRIDING_KEY} === undefined ? 'no key' : 'key'`,
    "process.stdout.write(JSON.stringify({ type: 'result', is_error: false, result: seen }) + '\\n')",
  ].join('\n')
  const session = startSession(
    { command: process.execPath, cwd: REPO, argv: ['-e', probe] },
    {},
    env,
  )
  return (await session.finished).result
}

describe('RG205: a machine with a login and the key', () => {
  it('asks without the key, and starts the session without it', async () => {
    const env: NodeJS.ProcessEnv = { ...process.env, [OVERRIDING_KEY]: KEY }

    const decided = await sessionEnvironment(transportFor, fakeAuth(true), REPO, { env })

    expect(Object.keys(decided)).not.toContain(OVERRIDING_KEY)
    expect(await sessionSees(decided)).toBe('no key')
    // The rest of the environment still reaches the session: PATH is how it finds anything.
    expect(decided['PATH'] ?? decided['Path']).toBe(env['PATH'] ?? env['Path'])
  })
})

describe('RG205: a machine with only the key', () => {
  it('keeps it, so the session still has a credential to start with', async () => {
    const env: NodeJS.ProcessEnv = { ...process.env, [OVERRIDING_KEY]: KEY }

    const decided = await sessionEnvironment(transportFor, fakeAuth(false), REPO, { env })

    expect(decided).toBe(env)
    expect(await sessionSees(decided)).toBe('key')
  })
})
