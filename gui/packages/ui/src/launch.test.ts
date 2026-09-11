import { BASE_LOCALE, DEFAULT_SETTINGS, type RendererBridge, type Theme } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { choicesFromBridge, LAUNCH_CEILING_MS } from './launch'
import { stubBridge } from './stub-bridge'

/**
 * RG86 and RG87: what the renderer asks for before it draws anything.
 *
 * The bridge is passed in rather than read off `window`, so these are about the answer and
 * not about how a page is served — which is the seam the whole transport design rests on.
 */
function answering(locale: string, theme: Theme = DEFAULT_SETTINGS.theme): RendererBridge {
  return stubBridge({
    settings: () =>
      Promise.resolve({ settings: { ...DEFAULT_SETTINGS, theme }, reset: [], locale }),
  })
}

const closed = (): Promise<never> => Promise.reject(new Error('channel closed'))
const CLOSED: RendererBridge = stubBridge({
  identify: closed,
  settings: closed,
  saveTheme: closed,
  saveLocale: closed,
})

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
    const counting: RendererBridge = stubBridge({
      settings: () => {
        asked += 1
        return Promise.resolve({
          settings: { ...DEFAULT_SETTINGS, theme: 'light' },
          reset: [],
          locale: 'pt-BR',
        })
      },
      saveTheme: () => Promise.resolve(),
      saveLocale: () => Promise.resolve(),
    })

    expect(await choicesFromBridge(counting)).toEqual({
      locale: 'pt-BR',
      theme: 'light',
      reset: [],
    })
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

describe('RG106: an answer that never comes', () => {
  it('mounts in English rather than waiting on a promise that never settles', async () => {
    // The failure this is about: a main process wedged in a synchronous read settles the
    // channel not at all, and Electron has already shown a window painted its background.
    const silent: RendererBridge = stubBridge({
      settings: () => new Promise(() => undefined),
      saveTheme: () => Promise.resolve(),
      saveLocale: () => Promise.resolve(),
    })

    const opened = await choicesFromBridge(silent, 20)

    expect(opened).toEqual({ locale: BASE_LOCALE, theme: null, reset: [] })
  })

  it('takes the answer when it arrives inside the deadline', async () => {
    // The other half: a deadline that fired on an ordinary round trip would lose somebody's
    // language for nothing.
    const slow: RendererBridge = stubBridge({
      settings: () =>
        new Promise((answer) =>
          setTimeout(
            () =>
              answer({
                settings: { ...DEFAULT_SETTINGS, theme: 'dark' },
                reset: [],
                locale: 'pt-BR',
              }),
            5,
          ),
        ),
      saveTheme: () => Promise.resolve(),
      saveLocale: () => Promise.resolve(),
    })

    expect(await choicesFromBridge(slow, 500)).toEqual({
      locale: 'pt-BR',
      theme: 'dark',
      reset: [],
    })
  })

  it('waits the deadline it was given and not longer', async () => {
    // A window that hangs for two seconds and one that hangs for ten are different windows.
    const silent: RendererBridge = stubBridge({
      settings: () => new Promise(() => undefined),
      saveTheme: () => Promise.resolve(),
      saveLocale: () => Promise.resolve(),
    })

    const startedAt = Date.now()
    await choicesFromBridge(silent, 30)

    expect(Date.now() - startedAt).toBeLessThan(400)
  })

  it('gives an ordinary answer room a real one never needs', () => {
    // Named rather than asserted about: what makes two seconds right is that a measured
    // round trip is single-digit milliseconds, which `running-app-live` holds.
    expect(LAUNCH_CEILING_MS).toBeGreaterThanOrEqual(1000)
  })
})
