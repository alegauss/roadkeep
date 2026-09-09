import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { DEFAULT_SETTINGS, SETTINGS_VERSION } from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { loadSettings, SETTINGS_FILE, saveSettings, settingsPath } from './settings-file'

/** Real directories, because what this module does is put a file in one and get it back. */
const scratch: string[] = []

function userData(): string {
  const home = mkdtempSync(path.join(tmpdir(), 'rk-settings-'))
  scratch.push(home)
  return home
}

afterAll(() => {
  for (const home of scratch) rmSync(home, { recursive: true, force: true })
})

describe('RG47: where the settings live', () => {
  it('round-trips what it saved', () => {
    const home = userData()
    const settings = {
      ...DEFAULT_SETTINGS,
      roots: [{ path: 'D:/Git', depth: 3 }],
      theme: 'dark' as const,
      locale: 'pt-BR',
    }

    saveSettings(home, settings)

    expect(loadSettings(home)).toEqual({ settings, reset: [] })
  })

  it('makes the directory on a first launch, which has none', () => {
    const home = path.join(userData(), 'not', 'there', 'yet')

    saveSettings(home, DEFAULT_SETTINGS)

    expect(JSON.parse(readFileSync(settingsPath(home), 'utf8'))).toEqual(DEFAULT_SETTINGS)
  })

  it('says nothing at all for a missing file, because that is a first launch', () => {
    const read = loadSettings(userData())

    expect(read.settings).toEqual(DEFAULT_SETTINGS)
    expect(read.reset).toEqual([])
  })

  it('leaves nothing behind after a write', () => {
    // Written by rename, so a crash cannot leave half a settings file — and the temporary
    // one does not survive a successful write either.
    const home = userData()
    saveSettings(home, DEFAULT_SETTINGS)

    expect(readdirSync(home)).toEqual([SETTINGS_FILE])
  })

  it('replaces a file that was already there', () => {
    const home = userData()
    saveSettings(home, DEFAULT_SETTINGS)
    saveSettings(home, { ...DEFAULT_SETTINGS, width: 12 })

    expect(loadSettings(home).settings.width).toBe(12)
  })
})

describe('RG47: a file that cannot be read', () => {
  it('uses defaults, says so, and leaves the file alone', () => {
    // Somebody hand-edited it into invalidity. Overwriting is how their fix becomes
    // impossible, so the broken file stays exactly as it is.
    const home = userData()
    writeFileSync(settingsPath(home), '{ this is not json', 'utf8')

    const read = loadSettings(home)

    expect(read.settings).toEqual(DEFAULT_SETTINGS)
    expect(read.reset).toHaveLength(1)
    expect(read.reset[0]).toContain('not readable as JSON')
    expect(readFileSync(settingsPath(home), 'utf8')).toBe('{ this is not json')
  })

  it('recovers a file that is JSON of the wrong shape, field by field', () => {
    // A different failure from the one above, and the one `core` owns.
    const home = userData()
    writeFileSync(
      settingsPath(home),
      JSON.stringify({ version: SETTINGS_VERSION, roots: [{ path: 'D:/Git' }], width: 'lots' }),
      'utf8',
    )

    const read = loadSettings(home)

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: 2 }])
    expect(read.settings.width).toBe(DEFAULT_SETTINGS.width)
    expect(read.reset[0]).toContain('pool width')
  })
})

describe('RG87: keeping one field without losing the rest', () => {
  it('leaves the roots and the locale alone when only the ground changed', () => {
    // The shape the bridge's theme handler writes: re-read, replace one field, save. A
    // handler that remembered the settings at startup instead would drop a root somebody
    // added by hand a minute earlier, and the click that dropped it would be a colour.
    const home = userData()
    saveSettings(home, {
      ...DEFAULT_SETTINGS,
      roots: [{ path: 'D:/Git', depth: 3 }],
      locale: 'pt-BR',
    })

    saveSettings(home, { ...loadSettings(home).settings, theme: 'dark' })

    expect(loadSettings(home).settings).toEqual({
      ...DEFAULT_SETTINGS,
      roots: [{ path: 'D:/Git', depth: 3 }],
      locale: 'pt-BR',
      theme: 'dark',
    })
  })
})
