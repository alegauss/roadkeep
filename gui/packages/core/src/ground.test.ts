import { describe, expect, it } from 'vitest'

import { followsSystem, GROUNDS, groundFor, nextTheme, THEME_ORDER } from './ground'
import { DEFAULT_SETTINGS, type Theme } from './settings'

describe('RG52: which ground is in force', () => {
  it('takes an explicit choice whatever the desktop says', () => {
    expect(groundFor('dark', false)).toBe('dark')
    expect(groundFor('light', true)).toBe('light')
  })

  it('follows the desktop when nobody chose', () => {
    expect(groundFor('system', true)).toBe('dark')
    expect(groundFor('system', false)).toBe('light')
  })

  it('resolves to a ground for every setting there is, and never to nothing', () => {
    // The whole point: light is defined on bare `:root`, so an unresolved `system` would be
    // light for everybody rather than a window that follows the desktop.
    for (const theme of THEME_ORDER) {
      for (const dark of [true, false]) {
        expect(GROUNDS).toContain(groundFor(theme, dark))
      }
    }
  })

  it('starts from following the desktop, which is what the settings default to', () => {
    expect(DEFAULT_SETTINGS.theme).toBe('system')
    expect(followsSystem(DEFAULT_SETTINGS.theme)).toBe(true)
  })
})

describe('RG52: walking the choice', () => {
  it('comes back to where it started', () => {
    let theme: Theme = 'system'
    for (let step = 0; step < THEME_ORDER.length; step += 1) theme = nextTheme(theme)

    expect(theme).toBe('system')
  })

  it('offers a way back to the desktop, which a two-state switch would not', () => {
    expect(THEME_ORDER).toContain('system')
    expect(nextTheme('dark')).toBe('system')
  })

  it('visits every setting on the way round', () => {
    const walked: Theme[] = []
    let theme: Theme = 'system'
    for (let step = 0; step < THEME_ORDER.length; step += 1) {
      walked.push(theme)
      theme = nextTheme(theme)
    }

    expect([...walked].sort()).toEqual([...THEME_ORDER].sort())
  })

  it('says when the desktop is the one deciding', () => {
    expect(followsSystem('system')).toBe(true)
    expect(followsSystem('light')).toBe(false)
    expect(followsSystem('dark')).toBe(false)
  })
})
