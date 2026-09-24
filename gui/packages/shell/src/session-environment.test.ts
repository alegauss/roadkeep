import { EngineCallFailed, type EngineResult, type EngineRequest } from '@rk/core'
import { describe, expect, it } from 'vitest'

import {
  OVERRIDING_KEY,
  sessionEnvironment,
  withoutKey,
  type EnvironmentTransportFor,
} from './session-environment'

/**
 * RG205: which environment a session inherits, with the `auth status` call faked.
 *
 * What is held is the order and the default: the login is asked with the key already left
 * out, a login that answers is the only thing that drops it, and every other answer leaves
 * the environment exactly as the process had it.
 */

const CLAUDE = ['claude']
const ROOT = '/proj'
const KEY = 'sk-ant-api-not-a-real-one'

interface Asked {
  readonly command: readonly string[]
  readonly env: NodeJS.ProcessEnv
  readonly request: EngineRequest
}

function answering(answer: Partial<EngineResult> | Error): {
  transportFor: EnvironmentTransportFor
  asked: Asked[]
} {
  const asked: Asked[] = []
  return {
    asked,
    transportFor: (command, env) => ({
      run(request) {
        asked.push({ command, env, request })
        if (answer instanceof Error) return Promise.reject(answer)
        return Promise.resolve({ code: 0, stdout: '', stderr: '', durationMs: 1, ...answer })
      },
    }),
  }
}

const LOGGED_IN = { stdout: '{"loggedIn": true, "authMethod": "claude.ai"}' }
const NO_LOGIN = { code: 1, stdout: '{"loggedIn": false, "authMethod": "none"}' }

describe('RG205: a key the machine carries, beside a login', () => {
  it('asks nothing and changes nothing where no key is set', async () => {
    const env = { PATH: '/bin', CLAUDE_CONFIG_DIR: '/c' }
    const { transportFor, asked } = answering(LOGGED_IN)

    expect(await sessionEnvironment(transportFor, CLAUDE, ROOT, { env })).toBe(env)
    expect(asked).toEqual([])
  })

  it('leaves the key out where a login answers without it', async () => {
    const env = { PATH: '/bin', [OVERRIDING_KEY]: KEY }
    const { transportFor, asked } = answering(LOGGED_IN)

    const inherited = await sessionEnvironment(transportFor, CLAUDE, ROOT, { env })

    expect(inherited).toEqual({ PATH: '/bin' })
    // The login was asked of the same agent, in the project, and already without the key —
    // asked with it, `auth status` reports the key and says nothing about a login.
    const [call] = asked
    expect(call?.command).toEqual(CLAUDE)
    expect(call?.request.argv).toEqual(['auth', 'status'])
    expect(call?.request.root).toBe(ROOT)
    expect(call?.env).toEqual({ PATH: '/bin' })
    // And the person's own environment is untouched.
    expect(env[OVERRIDING_KEY]).toBe(KEY)
  })

  it('keeps the key where no login answers, so a key-only machine still starts', async () => {
    const env = { PATH: '/bin', [OVERRIDING_KEY]: KEY }
    const { transportFor } = answering(NO_LOGIN)

    expect(await sessionEnvironment(transportFor, CLAUDE, ROOT, { env })).toBe(env)
  })

  it('keeps the key where the check could not be made or did not answer in JSON', async () => {
    const env = { [OVERRIDING_KEY]: KEY }

    const failed = answering(new EngineCallFailed('timeout', 'ran past', 15000))
    expect(await sessionEnvironment(failed.transportFor, CLAUDE, ROOT, { env })).toBe(env)

    const prose = answering({ code: 1, stdout: "error: unknown command 'auth'" })
    expect(await sessionEnvironment(prose.transportFor, CLAUDE, ROOT, { env })).toBe(env)
  })
})

describe('RG205: which variable is the key', () => {
  it('matches the name whatever its case, as Windows reads it', () => {
    expect(withoutKey({ Anthropic_Api_Key: KEY, Path: 'C:\\bin' })).toEqual({ Path: 'C:\\bin' })
  })

  it('treats an empty key as no key, and leaves every other credential alone', () => {
    expect(withoutKey({ [OVERRIDING_KEY]: '' })).toBeNull()
    expect(withoutKey({ ANTHROPIC_AUTH_TOKEN: 't', ANTHROPIC_BASE_URL: 'https://gw' })).toBeNull()
    expect(withoutKey({ [OVERRIDING_KEY]: KEY, ANTHROPIC_AUTH_TOKEN: 't' })).toEqual({
      ANTHROPIC_AUTH_TOKEN: 't',
    })
  })
})
