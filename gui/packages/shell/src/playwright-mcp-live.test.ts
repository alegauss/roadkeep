import { spawn, type ChildProcess } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { setTimeout as after } from 'node:timers/promises'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { INSPECT_PORT } from './launch'
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
/** The development launcher as `npm run dev:inspect` runs it, already built (RG298). */
const DEV = path.join(REPO, 'packages', 'shell', 'dist', 'dev.js')

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

describe('RG298: the first window a development run opens', () => {
  it('answers on the debugging port with nothing touched, which is what the skill says to do', async () => {
    // The whole defect, held where it was: the switches were declared below `start()`, so the
    // first window opened with none of them and only a window the watcher restarted had a
    // port. Anybody following the skill started `npm run dev:inspect`, reached for Playwright
    // MCP, and found nothing listening — then edited a file and it worked.
    const run = spawn(process.execPath, [DEV, '--inspect'], {
      cwd: REPO,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
      // Electron started from an editor terminal runs as plain Node without this stripped,
      // which `spawnElectron` does for the child — this is the launcher's own process.
      env: { ...process.env, ELECTRON_RUN_AS_NODE: '' },
    })
    try {
      const until = Date.now() + 120000
      let answered = ''
      while (Date.now() < until && answered === '') {
        try {
          const said = await fetch(`http://127.0.0.1:${String(INSPECT_PORT)}/json/version`)
          if (said.ok) answered = await said.text()
        } catch {
          // Not up yet: Vite has to bind and Electron has to start before anything listens.
        }
        if (answered === '') await after(500)
      }

      // Chromium's own answer, which is the port being open rather than this test's guess.
      expect(answered, `nothing answered on ${String(INSPECT_PORT)}`).toContain('Browser')
    } finally {
      run.kill()
    }
  }, 180000)
})
