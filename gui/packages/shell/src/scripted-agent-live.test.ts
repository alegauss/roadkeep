import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { loggedIn, resolveAgent, sessionCall, type SessionEvent } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { REPO } from './live'
import { createProcessTransport } from './process-transport'
import { removeTree } from './scratch'
import { scriptedAgent } from './scripted-agent'
import { startSession } from './session-process'

/**
 * RG210: the scripted agent, as the app resolves and runs it.
 *
 * Started for real — it is a node script — through the same resolution, login check and
 * session process a window uses, so what the screenshot run points the app at is held to
 * behave like the agent it stands in for, and to keep running until it is stopped.
 */

const agent = scriptedAgent({ tail: 8, intervalMs: 5 })

/**
 * Where the replayed session runs.
 *
 * A directory of its own and not this repository: a session runs in the project it was
 * handed a line from, and the replay writes a file there the way a command a session runs
 * writes one (RG247). Pointed at the checkout, that file would land in the checkout.
 */
const root = mkdtempSync(path.join(tmpdir(), 'rk-scripted-run-'))

afterAll(() => {
  agent.dispose()
  removeTree(root)
})

const transportFor = (command: readonly string[]) =>
  createProcessTransport({ command: command[0] ?? '', prefixArgs: command.slice(1) })

describe('RG210: a scripted agent resolves like Claude Code', () => {
  it('answers --version with a version, so RG43 resolves it', async () => {
    const resolution = await resolveAgent(transportFor, REPO, [agent.command], { timeoutMs: 30000 })

    expect(resolution.kind).toBe('resolved')
    if (resolution.kind !== 'resolved') throw new Error('unreachable')
    expect(resolution.agent.version).toBe('2.1.263')
  })

  it('answers auth status with a login, so RG205 runs it on one', async () => {
    const answer = await transportFor(agent.command).run({
      root: REPO,
      argv: ['auth', 'status'],
      timeoutMs: 30000,
    })

    expect(loggedIn(answer.stdout)).toBe(true)
  })
})

describe('RG210: a scripted run', () => {
  it('writes every line it replays, then stays running until it is stopped', async () => {
    const [command = '', ...prefix] = agent.command
    const call = sessionCall(command, root, 'a prompt nobody reads')
    const events: SessionEvent[] = []
    const session = startSession(
      { ...call, argv: [...prefix, ...call.argv] },
      { onEvent: (event) => events.push(event) },
    )

    await expect
      .poll(() => events.length, { timeout: 20000, interval: 50 })
      .toBeGreaterThanOrEqual(agent.lines)
    // No result line, so nothing has told the session it is done.
    expect(events.some((event) => event.kind === 'finished')).toBe(false)

    session.cancel()
    expect((await session.finished).state).toBe('cancelled')
  }, 30000)
})
