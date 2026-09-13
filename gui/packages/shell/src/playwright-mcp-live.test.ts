import { spawn, type ChildProcess } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { setTimeout as after } from 'node:timers/promises'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { startApp, type RunningApp } from './running-app'

/**
 * RG212: Playwright MCP attaches to this app's window, which its documentation never says.
 *
 * The server's own docs name Chrome, Firefox, WebKit and Edge, and nothing about Electron, so the
 * attach an agent relies on is held here rather than trusted: the built app is started with a
 * debugging port, the repository's own copy of the server is pointed at it over
 * `--cdp-endpoint`, and a snapshot is asked for over the protocol an MCP client speaks — one JSON
 * message a line on stdio.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const CLI = path.join(REPO, 'node_modules', '@playwright', 'mcp', 'cli.js')

let app: RunningApp
let server: ChildProcess
let heard = ''

function send(message: unknown): void {
  server.stdin?.write(`${JSON.stringify(message)}\n`)
}

/** The answer to one request id, or null once the ceiling passes. */
async function answer(id: number, ceilingMs: number): Promise<unknown> {
  const until = Date.now() + ceilingMs
  while (Date.now() < until) {
    for (const line of heard.split('\n')) {
      if (line.trim() === '') continue
      const parsed: unknown = JSON.parse(line)
      if (typeof parsed === 'object' && parsed !== null && 'id' in parsed && parsed.id === id) {
        return parsed
      }
    }
    await after(100)
  }
  return null
}

beforeAll(async () => {
  let profile = ''
  app = await startApp({}, (directory) => {
    profile = directory
  })
  const port = readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0] ?? ''

  server = spawn(process.execPath, [CLI, '--cdp-endpoint', `http://127.0.0.1:${port}`], {
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: true,
  })
  server.stdout?.setEncoding('utf8')
  server.stdout?.on('data', (chunk: string) => {
    heard += chunk
  })
}, 60000)

afterAll(async () => {
  server.kill()
  await app.close()
})

describe('RG212: an agent reads the running window through Playwright MCP', () => {
  it('starts, and speaks the protocol', async () => {
    send({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2025-06-18',
        capabilities: {},
        clientInfo: { name: 'rk', version: '0' },
      },
    })

    expect(JSON.stringify(await answer(1, 30000))).toContain('"serverInfo"')
    send({ jsonrpc: '2.0', method: 'notifications/initialized' })
  }, 40000)

  it("attaches over the window's debugging port and reads what it draws", async () => {
    send({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: { name: 'browser_snapshot', arguments: {} },
    })
    const snapshot = JSON.stringify(await answer(2, 30000))

    // The page is this app's bundle and the tree is its own: the header's name, a real control.
    expect(snapshot).toContain('packages/ui/dist/index.html')
    expect(snapshot).toContain('banner')
    expect(snapshot).toContain('roadkeep')
  }, 40000)
})
