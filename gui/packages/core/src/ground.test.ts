import { describe, expect, it } from 'vitest'

import { followsSystem, GROUNDS, groundFor, THEME_ORDER } from './ground'
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

describe('RG52: the choice', () => {
  it('offers a way back to the desktop, which a two-state switch would not (RG238)', () => {
    expect(THEME_ORDER[0]).toBe('system')
  })

  it('lists every setting once', () => {
    const every: readonly Theme[] = ['system', 'light', 'dark']

    expect([...THEME_ORDER].sort()).toEqual([...every].sort())
    expect(new Set(THEME_ORDER).size).toBe(THEME_ORDER.length)
  })

  it('says when the desktop is the one deciding', () => {
    expect(followsSystem('system')).toBe(true)
    expect(followsSystem('light')).toBe(false)
    expect(followsSystem('dark')).toBe(false)
  })
})
