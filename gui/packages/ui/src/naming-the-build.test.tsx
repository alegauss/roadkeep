import { DEFAULT_SETTINGS, identityFrom, PRODUCT, type RendererBridge, saidOfBuild } from '@rk/core'
import { screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { drawWindow } from './harness'

/**
 * RG118: the window says which build it is.
 *
 * Block G's criterion is that a user can say which build they are running and where it came
 * from, and every part of the answer was already in hand: the main process stamps it, the
 * bridge carries it, a live test asserts the field is there. Nothing drew it — so the
 * criterion was unmet by a screen and not by a mechanism, and a person reporting a bad read
 * had a version, a commit and a signature to quote and quoted none of them.
 *
 * Asserted through the whole window because it is chrome: the footer is mounted once by the
 * shell for every page, which is the rule `authoring.md` states for that region.
 */
const BUILT = identityFrom({
  version: '0.4.2',
  commit: '8d2800b',
  signed: 'signed',
  packaged: true,
})

function bridge(over: Partial<RendererBridge> = {}): RendererBridge {
  return {
    identify: () => Promise.resolve({ transport: 'ipc' as const, build: BUILT }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: 'en' }),
    saveTheme: () => Promise.resolve(),
    saveLocale: () => Promise.resolve(),
    ...over,
  }
}

function withBridge(one: RendererBridge | null): void {
  if (one === null) {
    Reflect.deleteProperty(window, 'roadkeep')
    return
  }
  Object.defineProperty(window, 'roadkeep', { value: one, configurable: true })
}

afterEach(() => {
  withBridge(null)
})

describe('RG118: the build, where every screen carries it', () => {
  it('prints the line a defect report quotes, whole', async () => {
    // The whole line and not a version alone: the commit is the half that says *which*
    // 0.4.2, and asking for it afterwards is the conversation this exists to skip.
    withBridge(bridge())

    drawWindow({ initial: 'light' })

    const footer = await screen.findByRole('contentinfo')
    await waitFor(() => {
      expect(within(footer).getByText(saidOfBuild(BUILT))).toBeTruthy()
    })
  })

  it('names the product before the bridge has answered, rather than a blank or a guess', () => {
    // The first frame draws with nothing known yet. A footer that appeared late would move
    // the page under a reader; one that invented a version would be worse than silent.
    withBridge(bridge({ identify: () => new Promise(() => undefined) }))

    drawWindow({ initial: 'light' })

    const footer = screen.getByRole('contentinfo')
    expect(footer.textContent).toContain(PRODUCT)
    expect(footer.textContent).not.toContain('(')
  })

  it('says the same in a plain browser tab, where no bridge will ever answer', async () => {
    // Not an error state: the renderer is the half a web service would serve, and a page
    // with no preload is a real way to run it. It knows the product and not the build.
    withBridge(null)

    drawWindow({ initial: 'light' })

    const footer = screen.getByRole('contentinfo')
    await waitFor(() => {
      expect(footer.textContent.trim()).toBe(PRODUCT)
    })
  })

  it('is the shell`s and not a page`s, so no screen has to carry its own', () => {
    // `authoring.md`: either the shell carries a footer for every page or the chrome has
    // none, and what must not happen is one page growing one. One landmark is that rule.
    withBridge(bridge())

    const { container } = drawWindow({ initial: 'light' })

    expect(container.querySelectorAll('footer')).toHaveLength(1)
    expect(container.querySelector('main')?.querySelector('footer')).toBeNull()
  })
})
