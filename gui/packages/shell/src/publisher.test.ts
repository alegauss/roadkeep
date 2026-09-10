import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG139: who the executable says made it.
 *
 * RG138 turned on the edit that writes the Windows version resources, and `CompanyName` came
 * out as `GitHub, Inc.` — Electron's default, surviving because the manifest named no author
 * to replace it. So the file-properties dialog, the installer's publisher line and anything
 * that inventories installed software said GitHub made this app.
 *
 * electron-builder reads the field from the root `package.json`, and what it says is a
 * statement made in public on every installer — the maintainer's to choose, and chosen: a
 * name, with no address. Held here without packaging, as `icon.test.ts` holds the icon,
 * because the default returns silently the day the field goes.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

function manifest(): { author?: unknown } {
  return JSON.parse(readFileSync(path.join(REPO, 'package.json'), 'utf8')) as { author?: unknown }
}

describe('RG139: the name the executable gives as its maker', () => {
  it('is one the manifest names, so Electron`s default does not survive', () => {
    const { author } = manifest()

    expect(typeof author, 'package.json names no author, so the .exe says GitHub made it').toBe(
      'string',
    )
    expect(author).not.toBe('')
    expect(author).not.toMatch(/github/i)
  })

  it('carries no address, which would be published on every installer', () => {
    // A string rather than an object, and no `<mail>` in it: the maintainer chose a name.
    expect(manifest().author).not.toMatch(/[<@>]/)
  })
})
