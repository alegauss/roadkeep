import { describe, expect, it } from 'vitest'

import { LOCALE_TAGS } from './locales'
import { isPreferenceKey, PREFERENCES, withPreference } from './preferences'
import { DEFAULT_SETTINGS, readSettings, type Settings } from './settings'

/**
 * RG207: the one way a page writes a preference.
 *
 * What is held is the boundary: a key outside the table reaches nothing, a value the reader
 * would reset is never written, and a write carries every other field — the roots above all —
 * exactly as it found them.
 */

const HELD: Settings = {
  ...DEFAULT_SETTINGS,
  roots: [{ path: 'D:\\code', depth: 2 }],
  skip: ['node_modules'],
}

describe('RG207: the table', () => {
  it('names the preferences a page chooses, and nothing that decides a scan', () => {
    // The ground and the language (RG207), and how a session draws its notes (RG208).
    expect(Object.keys(PREFERENCES).sort()).toEqual(['locale', 'sessionNotes', 'theme'])
    for (const reaching of ['roots', 'skip', 'width', 'version']) {
      expect(isPreferenceKey(reaching)).toBe(false)
    }
  })

  it('refuses a key that is not a string or only looks like an own field', () => {
    expect(isPreferenceKey(undefined)).toBe(false)
    expect(isPreferenceKey(['theme'])).toBe(false)
    // Inherited from every object, and not a row: `in` would have said yes.
    expect(isPreferenceKey('toString')).toBe(false)
  })
})

describe('RG207: writing one', () => {
  it('writes a ground and carries every other field as it was', () => {
    expect(withPreference(HELD, 'theme', 'dark')).toEqual({ ...HELD, theme: 'dark' })
  })

  it('writes a language this build ships, with a region', () => {
    const shipped = LOCALE_TAGS.find((tag) => tag.includes('-')) ?? LOCALE_TAGS[0]

    expect(withPreference(HELD, 'locale', shipped)?.locale).toBe(shipped)
  })

  it('writes how a session draws its notes', () => {
    expect(withPreference(HELD, 'sessionNotes', 'hidden')).toEqual({
      ...HELD,
      sessionNotes: 'hidden',
    })
  })

  it('refuses a value the reader would reset, so the file never holds one', () => {
    expect(withPreference(HELD, 'sessionNotes', 'folded')).toBeNull()
    expect(withPreference(HELD, 'theme', 'midnight')).toBeNull()
    expect(withPreference(HELD, 'locale', 'ja')).toBeNull()
    expect(withPreference(HELD, 'locale', 42)).toBeNull()
  })

  it('refuses a field outside the table whatever the value', () => {
    expect(withPreference(HELD, 'roots', [])).toBeNull()
    expect(withPreference(HELD, 'width', 4)).toBeNull()
  })

  it('writes nothing the reader then takes back', () => {
    // The round trip that makes the validator the reader's: whatever the table accepts, a
    // launch reads back unchanged and with nothing reset.
    const written = withPreference(HELD, 'theme', 'light')
    if (written === null) throw new Error('refused a ground the reader accepts')

    expect(readSettings(written)).toEqual({ settings: written, reset: [] })
  })
})
