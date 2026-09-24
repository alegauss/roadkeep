import { describe, expect, it } from 'vitest'

import { LOCALE_TAGS } from './locales'
import { isPreferenceKey, PREFERENCES, withPreference } from './preferences'
import { DEFAULT_SETTINGS, readSettings, settingsText, type Settings } from './settings'

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
    // The ground and the language (RG207), how a session draws its notes (RG208), the order
    // the portfolio opens in (RG241), where a session's cards sit (RG276) and how wide its
    // side bars are (RG279).
    expect(Object.keys(PREFERENCES).sort()).toEqual([
      'locale',
      'portfolioOrder',
      'sessionLayout',
      'sessionNotes',
      'sessionSides',
      'theme',
    ])
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

  it('writes the order the portfolio opens in (RG241)', () => {
    expect(withPreference(HELD, 'portfolioOrder', 'open-descending')).toEqual({
      ...HELD,
      portfolioOrder: 'open-descending',
    })
  })

  it("writes where a session's cards sit (RG276)", () => {
    const layout = { left: ['moved', 'handed'], right: ['files'] }

    expect(withPreference(HELD, 'sessionLayout', layout)).toEqual({
      ...HELD,
      sessionLayout: layout,
    })
  })

  it('refuses an arrangement the reader would repair, not only one it would reset (RG276)', () => {
    // Each of these reads back as something else, so storing it is a choice not kept.
    for (const repaired of [
      { left: ['handed'], right: ['moved'] },
      { left: ['handed', 'moved'], right: ['moved', 'files'] },
      { left: ['handed', 'stream'], right: ['moved', 'files'] },
      { left: ['handed'], right: ['moved', 'files'], extra: [] },
      'handed',
    ]) {
      expect(withPreference(HELD, 'sessionLayout', repaired)).toBeNull()
    }
  })

  it('writes how wide the session side bars are, and refuses a width the reader would clamp (RG279)', () => {
    expect(withPreference(HELD, 'sessionSides', { left: null, right: 30.5 })).toEqual({
      ...HELD,
      sessionSides: { left: null, right: 30.5 },
    })
    expect(withPreference(HELD, 'sessionSides', { left: 90, right: null })).toBeNull()
    expect(withPreference(HELD, 'sessionSides', { right: 30 })).toBeNull()
  })

  it('refuses a value the reader would reset, so the file never holds one', () => {
    expect(withPreference(HELD, 'portfolioOrder', 'open')).toBeNull()
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

    const ordered = withPreference(HELD, 'portfolioOrder', 'name-descending')
    if (ordered === null) throw new Error('refused an order the reader accepts')

    expect(readSettings(ordered)).toEqual({ settings: ordered, reset: [] })

    const arranged = withPreference(HELD, 'sessionLayout', {
      left: [],
      right: ['files', 'handed', 'moved'],
    })
    if (arranged === null) throw new Error('refused an arrangement the reader accepts')

    expect(readSettings(JSON.parse(settingsText(arranged)))).toEqual({
      settings: arranged,
      reset: [],
    })
  })
})
