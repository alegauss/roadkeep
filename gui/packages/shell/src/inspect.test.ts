import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { INSPECT_PORT } from './launch'

/**
 * RG212: the port the development window opens and the port Playwright MCP is pointed at are
 * one number, written in two files that cannot import each other.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

function playwrightArgs(): string[] {
  const config: unknown = JSON.parse(readFileSync(path.join(REPO, '.mcp.json'), 'utf8'))
  const servers =
    typeof config === 'object' && config !== null && 'mcpServers' in config
      ? config.mcpServers
      : null
  const playwright =
    typeof servers === 'object' && servers !== null && 'playwright' in servers
      ? servers.playwright
      : null
  const args =
    typeof playwright === 'object' && playwright !== null && 'args' in playwright
      ? playwright.args
      : []
  return Array.isArray(args) ? args.filter((one): one is string => typeof one === 'string') : []
}

describe('RG212: Playwright MCP, pointed where the development window listens', () => {
  it('names the port dev:inspect opens', () => {
    const args = playwrightArgs()
    const endpoint = args[args.indexOf('--cdp-endpoint') + 1]

    expect(endpoint).toBe(`http://127.0.0.1:${String(INSPECT_PORT)}`)
  })

  it('runs the copy this repository installs, not whatever npx fetches that day', () => {
    expect(playwrightArgs()[0]).toMatch(/node_modules\/@playwright\/mcp\/cli\.js$/)
  })
})
