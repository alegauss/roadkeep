import { BASE_LOCALE, DEFAULT_SETTINGS, type RendererBridge, type Theme } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { choicesFromBridge } from './launch'

/**
 * RG86 and RG87: what the renderer asks for before it draws anything.
 *
 * The bridge is passed in rather than read off `window`, so these are about the answer and
 * not about how a page is served — which is the seam the whole transport design rests on.
 */
function answering(locale: string, theme: Theme = DEFAULT_SETTINGS.theme): RendererBridge {
  return {
    identify: () => Promise.reject(new Error('not asked')),
    settings: () =>
      Promise.resolve({ settings: { ...DEFAULT_SETTINGS, theme }, reset: [], locale }),
    saveTheme: () => Promise.reject(new Error('not asked')),
  }
}

const CLOSED: RendererBridge = {
  identify: () => Promise.reject(new Error('channel closed')),
  settings: () => Promise.reject(new Error('channel closed')),
  saveTheme: () => Promise.reject(new Error('channel closed')),
}

describe('RG86: the locale the window opens in', () => {
  it('is whatever the shell already resolved', async () => {
    expect((await choicesFromBridge(answering('pt-BR'))).locale).toBe('pt-BR')
  })

  it('is the base with no bridge at all, which is what a browser tab gives it', async () => {
    expect((await choicesFromBridge(undefined)).locale).toBe(BASE_LOCALE)
  })

  it('is the base when the channel refuses, rather than a window that never mounts', async () => {
    expect((await choicesFromBridge(CLOSED)).locale).toBe(BASE_LOCALE)
  })
})

describe('RG87: the ground the window opens in', () => {
  it('is the one the settings file holds', async () => {
    expect((await choicesFromBridge(answering('en', 'dark'))).theme).toBe('dark')
  })

  it('comes out of the same call as the locale, so neither is asked for twice', async () => {
    let asked = 0
    const counting: RendererBridge = {
      identify: () => Promise.reject(new Error('not asked')),
      settings: () => {
        asked += 1
        return Promise.resolve({
          settings: { ...DEFAULT_SETTINGS, theme: 'light' },
          reset: [],
          locale: 'pt-BR',
        })
      },
      saveTheme: () => Promise.resolve(),
    }

    expect(await choicesFromBridge(counting)).toEqual({ locale: 'pt-BR', theme: 'light' })
    expect(asked).toBe(1)
  })

  it('says nothing answered with no bridge, rather than saying `system`', async () => {
    // A page with no bridge has no file to be the source of the ground, and the copy the
    // browser holds is then the only record of what somebody chose. `system` here would
    // overwrite that on every reload, which is the reverse of the defect being fixed.
    expect((await choicesFromBridge(undefined)).theme).toBeNull()
  })

  it('says nothing answered when the channel refuses', async () => {
    expect((await choicesFromBridge(CLOSED)).theme).toBeNull()
  })
})
