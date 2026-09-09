import { BASE, DEFAULT_SETTINGS, type RendererBridge } from '@rk/core'
import { toast } from '@viglet/viglet-design-system'
import { act, fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { drawWindow } from './harness'
import { choicesAtLaunch } from './launch'

/**
 * RG115: what a person is told when a setting did not stick.
 *
 * Two halves of one gap. `readSettings` composes a sentence for every field it had to reset
 * and `LaunchSettings` has carried them since RG47 — and nothing read them, so somebody
 * whose roots were dropped found out by noticing the list was short. The mirror is RG87's
 * write back: a ground that could not be saved looked saved until the next launch.
 *
 * Asserted through the window rather than against `toast`, because what is being held is
 * that a person sees it: the surface is the design system's and it is mounted in the chrome.
 */
function bridge(over: Partial<RendererBridge> = {}): RendererBridge {
  return {
    identify: () => Promise.reject(new Error('not asked')),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: 'en' }),
    saveTheme: () => Promise.resolve(),
    ...over,
  }
}

function withBridge(one: RendererBridge): void {
  Object.defineProperty(window, 'roadkeep', { value: one, configurable: true })
}

/** The launch is what fills the notice list, so a test that wants one has to run it. */
async function launched(reset: readonly string[]): Promise<void> {
  withBridge(
    bridge({
      settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset, locale: 'en' }),
    }),
  )
  await choicesAtLaunch()
}

beforeEach(() => {
  localStorage.clear()
  // Sonner's store outlives a render, so a notice one test raised is one the next test's
  // Toaster would draw again. Cleared here rather than asserted around.
  toast.dismiss()
})

afterEach(async () => {
  // The list lives with the launch, so the next test's launch is what clears it.
  await launched([])
  Reflect.deleteProperty(window, 'roadkeep')
  document.documentElement.className = ''
})

describe('RG115: a settings file that lost a field', () => {
  it('says so, in the app`s own voice, with the sentence the reader composed', async () => {
    await launched(['2 root(s) could not be read and were dropped'])

    drawWindow({ initial: 'light' })

    expect(await screen.findByText(BASE['settings.reset'])).toBeTruthy()
    expect(await screen.findByText(/2 root\(s\) could not be read/)).toBeTruthy()
  })

  it('says one thing per field, because two losses are two things to act on', async () => {
    await launched([
      'the roots were not a list, so none were read',
      'the pool width was not a whole number',
    ])

    drawWindow({ initial: 'light' })

    await waitFor(() => {
      expect(screen.getAllByText(BASE['settings.reset'])).toHaveLength(2)
    })
  })

  it('says nothing at all on a clean read, which is every other launch', async () => {
    await launched([])

    drawWindow({ initial: 'light' })

    await waitFor(() => {
      expect(screen.getByTestId('ground')).toBeTruthy()
    })
    await waitFor(() => {
      expect(screen.queryByText(BASE['settings.reset'])).toBeNull()
    })
  })
})

describe('RG115: a choice that could not be saved', () => {
  it('says so rather than letting it look kept until the next launch', async () => {
    withBridge(bridge({ saveTheme: () => Promise.reject(new Error('the disk is full')) }))
    drawWindow({ initial: 'light' })

    await act(async () => {
      fireEvent.click(screen.getByTestId('ground'))
      await Promise.resolve()
    })

    expect(await screen.findByText(BASE['settings.unsaved'])).toBeTruthy()
  })

  it('says nothing when the write lands, which is every ordinary click', async () => {
    withBridge(bridge())
    drawWindow({ initial: 'light' })

    await act(async () => {
      fireEvent.click(screen.getByTestId('ground'))
      await Promise.resolve()
    })

    expect(screen.queryByText(BASE['settings.unsaved'])).toBeNull()
  })
})
