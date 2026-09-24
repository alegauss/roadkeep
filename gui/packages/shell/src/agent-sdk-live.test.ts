import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { REPO } from './live'

/**
 * RG273: the Agent SDK carries a session, and its own Claude Code never ships.
 *
 * `@anthropic-ai/claude-agent-sdk` installs a native Claude Code for this platform as an optional
 * dependency — over two hundred megabytes, and a `claude` signed in as nobody the person chose.
 * The SDK runs it when it is told no executable; `startSession` always tells it one. What this
 * file holds is the other half: that the binary is in the install tree and nowhere near what the
 * executable is packaged from.
 *
 * Read off the tree and the built output rather than asserted about a package build, which is
 * minutes and a network this gate does not take.
 */

const MAIN = path.join(REPO, 'packages', 'shell', 'dist', 'main.js')

/** The platform package the SDK would install here, by the name its manifest gives it. */
function nativePackage(): string {
  const manifest = JSON.parse(
    readFileSync(
      path.join(REPO, 'node_modules', '@anthropic-ai', 'claude-agent-sdk', 'package.json'),
      'utf8',
    ),
  ) as { optionalDependencies: Record<string, string> }
  const name = Object.keys(manifest.optionalDependencies).find((one) =>
    one.endsWith(`-${process.platform}-${process.arch}`),
  )
  if (name === undefined) throw new Error(`the SDK names no package for ${process.platform}`)
  return path.join(REPO, 'node_modules', ...name.split('/'))
}

/** Every file under a directory, recursively. */
function filesUnder(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(directory, entry.name)
    return entry.isDirectory() ? filesUnder(full) : [full]
  })
}

describe('RG273: the SDK in the build, and its Claude Code out of it', () => {
  it('reads a tree where the SDK installed its own Claude Code, which is what makes the rest mean anything', () => {
    // The control: an install run with optional dependencies left out would pass every check
    // below for a reason that is not the good one.
    const binaries = filesUnder(nativePackage()).filter((file) => statSync(file).size > 50_000_000)

    expect(binaries.length).toBeGreaterThan(0)
  })

  it('bundles the SDK into the main process, so nothing under node_modules is needed at runtime', () => {
    expect(existsSync(MAIN)).toBe(true)
    expect(readFileSync(MAIN, 'utf8')).toContain('spawnClaudeCodeProcess')
  })

  it('builds nothing the size of a Claude Code, so the packaged output carries none', () => {
    const built = ['core', 'shell', 'ui'].flatMap((name) => {
      const dist = path.join(REPO, 'packages', name, name === 'core' ? 'dist-types' : 'dist')
      return existsSync(dist) ? filesUnder(dist) : []
    })

    expect(built.length).toBeGreaterThan(0)
    for (const file of built) {
      expect(statSync(file).size, `${file} is built output the size of a binary`).toBeLessThan(
        20_000_000,
      )
    }
  })

  it('packages built output only, so the install tree the binary sits in never ships', () => {
    const config = readFileSync(path.join(REPO, 'electron-builder.yml'), 'utf8')
    const listed = config
      .split('\n')
      .map((line) => /^\s+-\s+'?(!?[^'\s]+)'?\s*$/.exec(line)?.[1])
      .filter((entry): entry is string => entry?.includes('/') === true)

    expect(listed.length).toBeGreaterThan(0)
    for (const entry of listed) expect(entry).not.toContain('node_modules')
  })
})
