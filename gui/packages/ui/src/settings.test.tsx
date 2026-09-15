import {
  BASE,
  DEFAULT_SETTINGS,
  LOCALE_NAMES,
  type PreferenceKey,
  type RendererBridge,
} from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { toast } from '@viglet/viglet-design-system'
import i18next, { changeLanguage } from 'i18next'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { SETTINGS_ROUTE } from './areas'
import { drawWindow } from './harness'
import { holdSessionNotes } from './preferring'
import { startSpeaking } from './speaking'
import { stubBridge } from './stub-bridge'

/**
 * RG207: the preferences on one screen, written through the one method that writes them.
 *
 * What is held is that the screen routes, that each choice lands on the file as the row it
 * is — the ground as `theme`, the language as `locale` — that the screen and the header move
 * the same state, and that a write refused is said rather than looking kept.
 */

function recording(over: Partial<RendererBridge> = {}): [PreferenceKey, unknown][] {
  const kept: [PreferenceKey, unknown][] = []
  Object.defineProperty(window, 'roadkeep', {
    value: stubBridge({
      settings: () =>
        Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: 'en', projectsAtOnce: 0 }),
      savePreference: (key, value) => {
        kept.push([key, value])
        return Promise.resolve()
      },
      ...over,
    }),
    configurable: true,
  })
  return kept
}

beforeEach(async () => {
  toast.dismiss()
  await startSpeaking('en')
})

afterEach(async () => {
  Reflect.deleteProperty(window, 'roadkeep')
  // One value for the window's life, so a choice one test made is the next test's start.
  holdSessionNotes('shown')
  if (i18next.isInitialized) await changeLanguage('en')
})

describe('RG207: the settings screen', () => {
  it('routes, and groups the ground and the language under appearance', async () => {
    recording()
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    expect(await screen.findByRole('heading', { name: BASE['settings.title'] })).toBeTruthy()
    const appearance = within(screen.getByTestId('appearance'))
    expect(appearance.getByRole('radiogroup', { name: BASE['settings.ground'] })).toBeTruthy()
    expect(appearance.getByRole('radiogroup', { name: BASE['settings.language'] })).toBeTruthy()
  })

  it('writes a ground as the theme row, and the header moves with it', async () => {
    const kept = recording()
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    const grounds = within(await screen.findByRole('radiogroup', { name: BASE['settings.ground'] }))
    fireEvent.click(grounds.getByRole('radio', { name: BASE['settings.ground.dark'] }))

    await waitFor(() => {
      expect(kept).toEqual([['theme', 'dark']])
    })
    expect(grounds.getByRole('radio', { name: BASE['settings.ground.dark'] })).toHaveProperty(
      'ariaChecked',
      'true',
    )
    // Marked, and only there: the package's accent alone is a shade the dark ground hides.
    const marked = grounds.getAllByRole('radio').filter((one) => one.querySelector('svg') !== null)
    expect(marked.map((one) => one.textContent)).toEqual([BASE['settings.ground.dark']])
    // One state and not two: the window is painted the ground chosen here, which is what the
    // header's menu draws its icon from (RG238).
    await waitFor(() => {
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })
  })

  it('writes nothing for a click on the ground already chosen', async () => {
    const kept = recording()
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    const grounds = within(await screen.findByRole('radiogroup', { name: BASE['settings.ground'] }))
    // Radix answers this with an empty value, which is no ground at all.
    fireEvent.click(grounds.getByRole('radio', { name: BASE['settings.ground.light'] }))

    expect(kept).toEqual([])
  })

  it('writes a language as the locale row, by moving i18next as the header menu does', async () => {
    const kept = recording()
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    const languages = within(
      await screen.findByRole('radiogroup', { name: BASE['settings.language'] }),
    )
    await act(async () => {
      fireEvent.click(languages.getByRole('radio', { name: LOCALE_NAMES['pt-BR'] }))
      await Promise.resolve()
    })

    expect(i18next.language).toBe('pt-BR')
    await waitFor(() => {
      expect(kept).toEqual([['locale', 'pt-BR']])
    })
  })

  it('writes how a session draws its notes as the sessionNotes row, under sessions', async () => {
    const kept = recording()
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    const sessions = within(await screen.findByTestId('sessions-settings'))
    const notes = within(sessions.getByRole('radiogroup', { name: BASE['settings.notes'] }))
    // Every note drawn is the default, so that is the one marked before anything is chosen.
    expect(
      notes.getByRole('radio', { name: BASE['settings.notes.shown'] }).getAttribute('aria-checked'),
    ).toBe('true')

    fireEvent.click(notes.getByRole('radio', { name: BASE['settings.notes.hidden'] }))

    await waitFor(() => {
      expect(kept).toEqual([['sessionNotes', 'hidden']])
    })
    expect(
      notes
        .getByRole('radio', { name: BASE['settings.notes.hidden'] })
        .getAttribute('aria-checked'),
    ).toBe('true')
  })

  it('says a refused write was not kept, rather than looking kept until the next launch', async () => {
    recording({ savePreference: () => Promise.reject(new Error('theme cannot be set')) })
    drawWindow({ initial: 'light', at: SETTINGS_ROUTE })

    const grounds = within(await screen.findByRole('radiogroup', { name: BASE['settings.ground'] }))
    fireEvent.click(grounds.getByRole('radio', { name: BASE['settings.ground.dark'] }))

    expect(await screen.findByText(BASE['settings.unsaved'])).toBeTruthy()
  })
})
