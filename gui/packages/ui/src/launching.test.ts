import { DEFAULT_SETTINGS, type RendererBridge } from '@rk/core'
import { changeLanguage } from 'i18next'
import { describe, expect, it } from 'vitest'

import { spokenLocale, startSpeaking } from './speaking'

/**
 * RG116: the one thing a launch must not do.
 *
 * An empty `locale` in the settings file means *whatever the desktop says*, and the shell
 * resolves it before the renderer sees it. So the launch always looks like a language
 * change — and the keeper that writes a chosen language back to the file would write that
 * resolution too, turning "follow the desktop" into a language pinned on the first start.
 * Nobody would see it go wrong: the first launch is right, and every launch after is right
 * for the wrong reason until the desktop's language changes.
 *
 * A file of its own because this is a claim about a *launch*: the module remembers what the
 * settings file means, and a second `startSpeaking` beside other tests would be starting
 * from a window that had already been somewhere. Here nothing has run before it.
 */
const kept: string[] = []

const bridge: RendererBridge = {
  identify: () => Promise.reject(new Error('not asked')),
  settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: 'pt-BR' }),
  saveTheme: () => Promise.resolve(),
  saveLocale: (locale) => {
    kept.push(locale)
    return Promise.resolve()
  },
}

describe('RG116: what the first launch writes', () => {
  it('speaks the tag the shell resolved and keeps nothing, which is the whole of it', async () => {
    Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })

    // What `main` does, in the order it does it.
    await startSpeaking('pt-BR')

    expect(spokenLocale()).toBe('pt-BR')
    expect(kept).toEqual([])
  })

  it('is listening by the time it returns, so the next change is kept', async () => {
    // The other half: attached late is right, attached never is the defect this replaced.
    await changeLanguage('en')

    expect(kept).toEqual(['en'])
  })
})
