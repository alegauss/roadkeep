import { describe, expect, it } from 'vitest'

import { DEFAULT_LIMITS } from './limits'
import { DEPTH_CEILING } from './roots'
import { DEFAULT_POLICY } from './scanning'
import {
  DEFAULT_SETTINGS,
  readSettings,
  SETTINGS_VERSION,
  settingsText,
  wasReset,
} from './settings'

/** A settings file as this build writes one. */
const WRITTEN = {
  version: SETTINGS_VERSION,
  roots: [{ path: 'D:/Git', depth: 2 }],
  skip: ['node_modules', 'dist'],
  width: 8,
  theme: 'dark',
  locale: 'pt-BR',
}

describe('RG47: the one thing this app owns', () => {
  it('reads back what it wrote', () => {
    const read = readSettings(WRITTEN)

    expect(wasReset(read)).toBe(false)
    expect(read.settings).toEqual({ ...WRITTEN, version: SETTINGS_VERSION })
  })

  it('starts from defaults that come from the modules that own them', () => {
    // Not a second copy of the ignore list or the pool width: the scan and the read limits
    // already declare theirs, and a settings file that disagreed would be a second rule.
    expect(DEFAULT_SETTINGS.skip).toBe(DEFAULT_POLICY.ignore)
    expect(DEFAULT_SETTINGS.width).toBe(DEFAULT_LIMITS.width)
    expect(DEFAULT_SETTINGS.roots).toEqual([])
  })

  it('holds no project data and no cached answer', () => {
    // `No store of its own`, restated as a file format. The project list is the
    // catalogue's, and this is only what somebody chose.
    expect(Object.keys(DEFAULT_SETTINGS).sort()).toEqual([
      'locale',
      'roots',
      'skip',
      'theme',
      'version',
      'width',
    ])
  })

  it('writes a file a person can read and edit', () => {
    const text = settingsText(DEFAULT_SETTINGS)

    expect(text.endsWith('\n')).toBe(true)
    expect(text).toContain('\n  "roots"')
    expect(JSON.parse(text)).toEqual(DEFAULT_SETTINGS)
  })

  it('stamps its own version on the way out, whatever it was handed', () => {
    expect(JSON.parse(settingsText({ ...DEFAULT_SETTINGS, version: 99 }))).toHaveProperty(
      'version',
      SETTINGS_VERSION,
    )
  })
})

describe('RG47: a bad file resets field by field, and says so', () => {
  it('keeps the roots when the pool width is unusable', () => {
    // The whole point: a width typed as a word should not cost somebody the roots they
    // spent a minute naming.
    const read = readSettings({ ...WRITTEN, width: 'eight' })

    expect(read.settings.roots).toEqual(WRITTEN.roots)
    expect(read.settings.width).toBe(DEFAULT_SETTINGS.width)
    expect(read.reset).toHaveLength(1)
    expect(read.reset[0]).toContain('pool width')
  })

  it('drops the roots it cannot read and counts them, keeping the rest', () => {
    const read = readSettings({
      ...WRITTEN,
      roots: [{ path: 'D:/Git', depth: 2 }, { depth: 1 }, 'not a root', { path: '' }],
    })

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: 2 }])
    expect(read.reset[0]).toBe('3 root(s) could not be read and were dropped')
  })

  it('holds a root depth to the ceiling rather than dropping the root', () => {
    // A depth of forty is a mistake, not a reason to lose the folder.
    const read = readSettings({ ...WRITTEN, roots: [{ path: 'D:/Git', depth: 40 }] })

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: DEPTH_CEILING }])
    expect(read.reset).toEqual([])
  })

  it('says every field it lost, not only the first', () => {
    const read = readSettings({
      version: SETTINGS_VERSION,
      roots: 'nope',
      skip: [1, 2],
      width: -3,
      theme: 'neon',
      locale: 42,
    })

    expect(read.reset).toHaveLength(5)
    expect(read.settings).toEqual(DEFAULT_SETTINGS)
  })

  it('takes a field that is simply absent without calling it a loss', () => {
    // A file written by a build with fewer settings, or by somebody who set what they
    // cared about.
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'light' })

    expect(read.reset).toEqual([])
    expect(read.settings.theme).toBe('light')
    expect(read.settings.width).toBe(DEFAULT_SETTINGS.width)
  })

  it('resets everything for a file that is not an object at all', () => {
    for (const source of [null, 'a string', 42, ['a', 'list']]) {
      const read = readSettings(source)

      expect(read.settings).toEqual(DEFAULT_SETTINGS)
      expect(read.reset).toHaveLength(1)
    }
  })
})

describe('RG47: the version is read first', () => {
  it('leaves a file from a future build alone and uses defaults', () => {
    // Its fields might mean something else. Guessing is how a newer build's settings get
    // overwritten by an older one.
    const read = readSettings({ ...WRITTEN, version: SETTINGS_VERSION + 1 })

    expect(read.settings).toEqual(DEFAULT_SETTINGS)
    expect(read.reset).toHaveLength(1)
    expect(read.reset[0]).toContain('left alone')
    expect(read.reset[0]).toContain(String(SETTINGS_VERSION + 1))
  })

  it('reads a file that names no version as this build writes them', () => {
    const read = readSettings({ roots: WRITTEN.roots })

    expect(read.settings.roots).toEqual(WRITTEN.roots)
    expect(read.reset[0]).toContain('names no version')
  })

  it('reads an older version, because there is nothing yet to migrate', () => {
    const read = readSettings({ ...WRITTEN, version: 0 })

    expect(read.settings.theme).toBe('dark')
    expect(read.settings.version).toBe(SETTINGS_VERSION)
  })
})
