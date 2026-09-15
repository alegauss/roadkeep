import { describe, expect, it } from 'vitest'

import { DEFAULT_LIMITS } from './limits'
import { isRowOrder } from './portfolio'
import { DEPTH_CEILING } from './roots'
import { DEFAULT_POLICY } from './scanning'
import {
  DEFAULT_SETTINGS,
  isSessionNotes,
  isTheme,
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
  sessionNotes: 'hidden',
  portfolioOrder: 'open-descending',
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
    // The portfolio's order is a choice too, and not the ranking it produced (RG241).
    expect(Object.keys(DEFAULT_SETTINGS).sort()).toEqual([
      'locale',
      'portfolioOrder',
      'roots',
      'sessionNotes',
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
    // The code and the value it names, since RG123 — the sentence is the catalogue's, and
    // the default this reset to is the field the sentence has a hole for.
    expect(read.reset).toEqual([{ lost: 'width', fields: { width: DEFAULT_SETTINGS.width } }])
  })

  it('drops the roots it cannot read and counts them, keeping the rest', () => {
    const read = readSettings({
      ...WRITTEN,
      roots: [{ path: 'D:/Git', depth: 2 }, { depth: 1 }, 'not a root', { path: '' }],
    })

    expect(read.settings.roots).toEqual([{ path: 'D:/Git', depth: 2 }])
    expect(read.reset).toEqual([{ lost: 'dropped', fields: { count: 3 } }])
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
      sessionNotes: 'whispered',
      portfolioOrder: 'by mood',
    })

    // One code per field, in the order the fields are read.
    expect(read.reset.map((lost) => lost.lost)).toEqual([
      'roots',
      'skip',
      'width',
      'theme',
      'locale',
      'sessionNotes',
      'portfolioOrder',
    ])
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
      expect(read.reset).toEqual([{ lost: 'file' }])
    }
  })
})

describe('RG47: the version is read first', () => {
  it('leaves a file from a future build alone and uses defaults', () => {
    // Its fields might mean something else. Guessing is how a newer build's settings get
    // overwritten by an older one.
    const read = readSettings({ ...WRITTEN, version: SETTINGS_VERSION + 1 })

    expect(read.settings).toEqual(DEFAULT_SETTINGS)
    // Both versions travel as fields: what the file said and what this build reads, which
    // is the whole of what makes the sentence worth showing.
    expect(read.reset).toEqual([
      { lost: 'version', fields: { found: SETTINGS_VERSION + 1, reads: SETTINGS_VERSION } },
    ])
  })

  it('reads a file that names no version as this build writes them', () => {
    const read = readSettings({ roots: WRITTEN.roots })

    expect(read.settings.roots).toEqual(WRITTEN.roots)
    expect(read.reset).toEqual([{ lost: 'unversioned' }])
  })

  it('reads an older version, because there is nothing yet to migrate', () => {
    const read = readSettings({ ...WRITTEN, version: 0 })

    expect(read.settings.theme).toBe('dark')
    expect(read.settings.version).toBe(SETTINGS_VERSION)
  })
})

describe('RG208: how a session draws its notes', () => {
  it('draws every note where the file says nothing, which is what every earlier build did', () => {
    // A file from before the choice existed: no loss, and nothing changes on screen.
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.sessionNotes).toBe('shown')
    expect(read.reset).toEqual([])
  })

  it('knows the two choices and refuses anything else', () => {
    expect(['shown', 'hidden'].every(isSessionNotes)).toBe(true)
    for (const junk of ['', 'Hidden', 'folded', true, 0, null, undefined]) {
      expect(isSessionNotes(junk)).toBe(false)
    }
  })
})

describe('RG241: the order the portfolio opens in', () => {
  it("opens in the record's order where the file says nothing, which is what every earlier build did", () => {
    const read = readSettings({ version: SETTINGS_VERSION, theme: 'dark' })

    expect(read.settings.portfolioOrder).toBe('record')
    expect(read.reset).toEqual([])
  })

  it('resets an order this build does not know, says so, and keeps every other field', () => {
    const read = readSettings({ ...WRITTEN, portfolioOrder: 'open' })

    expect(read.settings).toEqual({ ...WRITTEN, portfolioOrder: 'record' })
    expect(read.reset).toEqual([{ lost: 'portfolioOrder' }])
  })

  it('knows the five orders and refuses anything else', () => {
    expect(
      ['record', 'name-ascending', 'name-descending', 'open-descending', 'open-ascending'].every(
        isRowOrder,
      ),
    ).toBe(true)
    // `toString` is inherited by every object, and not an order.
    for (const junk of ['', 'open', 'name', 'Record', 'toString', 0, null, undefined, ['record']]) {
      expect(isRowOrder(junk)).toBe(false)
    }
  })
})

describe('RG87: which grounds this build knows', () => {
  it('accepts the three the setting has, `system` included', () => {
    expect(['system', 'light', 'dark'].every(isTheme)).toBe(true)
  })

  it('refuses anything else, which is what the bridge leans on', () => {
    // The main process takes a theme the renderer named, and this is the check standing
    // between that argument and the settings file. A resolved ground is not a setting.
    for (const junk of ['', 'Dark', 'auto', 'light dark', 0, null, undefined, {}, ['dark']]) {
      expect(isTheme(junk)).toBe(false)
    }
  })
})
