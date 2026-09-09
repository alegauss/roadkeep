import { BASE_LOCALE, DEFAULT_SETTINGS, type RendererBridge } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { localeFromBridge } from './locale'

/**
 * RG86: what the renderer asks for before it draws anything.
 *
 * The bridge is passed in rather than read off `window`, so these are about the answer and
 * not about how a page is served — which is the seam the whole transport design rests on.
 */
function answering(locale: string): RendererBridge {
  return {
    identify: () => Promise.reject(new Error('not asked')),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale }),
  }
}

describe('RG86: the locale the window opens in', () => {
  it('is whatever the shell already resolved', async () => {
    expect(await localeFromBridge(answering('pt-BR'))).toBe('pt-BR')
  })

  it('is the base with no bridge at all, which is what a browser tab gives it', async () => {
    expect(await localeFromBridge(undefined)).toBe(BASE_LOCALE)
  })

  it('is the base when the channel refuses, rather than a window that never mounts', async () => {
    const broken: RendererBridge = {
      identify: () => Promise.reject(new Error('channel closed')),
      settings: () => Promise.reject(new Error('channel closed')),
    }

    expect(await localeFromBridge(broken)).toBe(BASE_LOCALE)
  })
})
