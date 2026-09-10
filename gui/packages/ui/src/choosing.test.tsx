import { BASE, DEFAULT_SETTINGS, LOCALE_NAMES, LOCALE_TAGS, type RendererBridge } from '@rk/core'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { toast } from '@viglet/viglet-design-system'
import i18next, { changeLanguage } from 'i18next'
import { act } from 'react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { AREA_WORDING } from './areas'
import { drawWindow } from './harness'
import { SPOKEN_LOCALES, startSpeaking } from './speaking'

/**
 * RG116: choosing a language without editing a file.
 *
 * The app has spoken two languages since RG86 and the only way to pick one was to open
 * `settings.json` by hand — the window had no control at all. What is held here is the whole
 * path: the menu is in the chrome, it is reachable by name and by keyboard, and choosing a
 * language moves both translation systems *and* reaches the file.
 *
 * The last of those is the half a screenshot cannot show, and the half the design system's
 * menu does not do: it persists to the browser cache and stops there, which is right until
 * the next launch and then wrong. The keeping is hung on i18next's own event instead of on
 * the menu, so it holds for that menu and for whatever replaces it.
 */
function bridge(over: Partial<RendererBridge> = {}): RendererBridge {
  return {
    identify: () => Promise.reject(new Error('not asked')),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: 'en' }),
    saveTheme: () => Promise.resolve(),
    saveLocale: () => Promise.resolve(),
    ...over,
  }
}

function withBridge(one: RendererBridge): void {
  Object.defineProperty(window, 'roadkeep', { value: one, configurable: true })
}

/** A bridge that records the tags the window sent back to the file. */
function recording(): { kept: string[] } {
  const kept: string[] = []
  withBridge(
    bridge({
      saveLocale: (locale) => {
        kept.push(locale)
        return Promise.resolve()
      },
    }),
  )
  return { kept }
}

/** What the menu calls itself, which is this app's string and not the package's default. */
function menuName(language: 'en' | 'pt'): string {
  return (AREA_WORDING[language]['language'] as { toggle: string }).toggle
}

beforeEach(() => {
  // Sonner's store outlives a render, so a notice one test raised is one the next draws.
  toast.dismiss()
})

afterEach(async () => {
  Reflect.deleteProperty(window, 'roadkeep')
  // i18next is a singleton, so a tag left behind is the next file's starting state.
  if (i18next.isInitialized) await changeLanguage('en')
})

describe('RG116: the choice reaches the file', () => {
  it('keeps whatever language is now being spoken, which browser storage alone cannot', async () => {
    await startSpeaking('en')
    const { kept } = recording()

    await changeLanguage('pt-BR')

    expect(i18next.language).toBe('pt-BR')
    await waitFor(() => {
      expect(kept).toEqual(['pt-BR'])
    })
  })

  it('says so when the write is refused, rather than looking kept until the next launch', async () => {
    await startSpeaking('en')
    withBridge(bridge({ saveLocale: () => Promise.reject(new Error('the disk is full')) }))
    drawWindow({ initial: 'light' })

    await act(async () => {
      await changeLanguage('pt-BR')
    })

    expect(await screen.findByText(BASE['settings.unsaved'])).toBeTruthy()
  })

  it('changes the language with no bridge at all, which is a plain browser tab', async () => {
    await startSpeaking('en')

    // No `window.roadkeep`: the language still moves, and nothing throws on the way out.
    await changeLanguage('pt-BR')

    expect(i18next.language).toBe('pt-BR')
  })
})

describe('RG116: the menu in the chrome', () => {
  it('offers every locale this build ships, each named in its own language', () => {
    expect(SPOKEN_LOCALES.map((row) => row.code)).toEqual([...LOCALE_TAGS])
    expect(SPOKEN_LOCALES.map((row) => row.label)).toEqual(
      LOCALE_TAGS.map((tag) => LOCALE_NAMES[tag]),
    )
    // No flags: a flag is a country, and the package's own default list pairs English with
    // one. An endonym is what the reader who cannot read this screen is looking for.
    expect(SPOKEN_LOCALES.every((row) => row.flag === undefined)).toBe(true)
  })

  it('is reachable by its own name, in the language the window is speaking', async () => {
    withBridge(bridge())
    await startSpeaking('en')
    drawWindow({ initial: 'light' })

    expect(screen.getByRole('button', { name: menuName('en') })).toBeTruthy()

    // The name is this app's own string and translated, which is the whole reason it is in
    // `AREA_WORDING`: the package ships no `language` namespace, so its own fallback is an
    // English sentence a Portuguese window would still be wearing.
    await act(async () => {
      await changeLanguage('pt-BR')
    })
    expect(screen.getByRole('button', { name: menuName('pt') })).toBeTruthy()
  })

  it('opens from the keyboard and lists every language by name', async () => {
    withBridge(bridge())
    await startSpeaking('en')
    drawWindow({ initial: 'light' })

    // A keystroke and not a pointer: a menu only a mouse can open is one a person
    // navigating by keyboard cannot use to leave a language they cannot read.
    fireEvent.keyDown(screen.getByRole('button', { name: menuName('en') }), { key: 'Enter' })

    const offered = await screen.findAllByRole('menuitem')
    expect(offered.map((one) => one.textContent)).toEqual(
      LOCALE_TAGS.map((tag) => LOCALE_NAMES[tag]),
    )
  })

  it('sends the choice through i18next, so one click moves both systems and the file', async () => {
    await startSpeaking('en')
    const { kept } = recording()
    drawWindow({ initial: 'light' })
    fireEvent.keyDown(screen.getByRole('button', { name: menuName('en') }), { key: 'Enter' })
    // By its name and not by its position: a menu that reordered would otherwise keep
    // passing while clicking whatever had moved into the last row.
    const portuguese = await screen.findByRole('menuitem', { name: LOCALE_NAMES['pt-BR'] })

    await act(async () => {
      fireEvent.click(portuguese)
      await Promise.resolve()
    })

    expect(i18next.language).toBe('pt-BR')
    await waitFor(() => {
      expect(kept).toEqual(['pt-BR'])
    })
  })
})
