import {
  BASE,
  BASE_LOCALE,
  DARK_QUERY,
  DEFAULT_SETTINGS,
  identityFrom,
  THEME_ORDER,
  type RendererBridge,
  type Theme,
} from '@rk/core'
import { act, fireEvent, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GROUND_CACHE_KEY } from './ground'
import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG52: the ground, from the outside.
 *
 * What is asserted is what a person would see: which ground the document is in, that the
 * control says which of the three settings is in force, and that the words on screen do
 * not change with the ground. The switch itself is the design system's, so what is held
 * here is this app's use of it and not the library.
 */

/** jsdom has no `matchMedia`, so the desktop is something a test says rather than has. */
function desktopIsDark(isDark: boolean): void {
  Object.defineProperty(window, 'matchMedia', {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: query === DARK_QUERY ? isDark : false,
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    }),
  })
}

function drawIn(initial: Theme) {
  return drawWindow({ initial })
}

/** What the window is actually painted in, read where the tokens are read from. */
function paintedGround(): 'light' | 'dark' {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

async function painted(ground: 'light' | 'dark'): Promise<void> {
  await waitFor(() => {
    expect(paintedGround()).toBe(ground)
  })
}

/**
 * Every piece of text the screen shows, which is what must not move with the ground.
 *
 * `script` is skipped because `next-themes` injects one to set the class before the first
 * paint: it carries the chosen theme in its source and is not something anybody reads.
 */
const UNREAD = new Set(['SCRIPT', 'STYLE'])

function visibleText(root: HTMLElement): string[] {
  const seen: string[] = []
  for (const node of root.querySelectorAll('*')) {
    if (node.children.length > 0 || UNREAD.has(node.tagName)) continue
    const text = node.textContent.trim()
    if (text !== '') seen.push(text)
  }
  return seen.toSorted()
}

function labelOfControl(): string {
  return screen.getByTestId('ground').textContent.trim()
}

/** A bridge that records what the ground control sent back to the file. */
function recordingBridge(): { kept: Theme[] } {
  const kept: Theme[] = []
  const bridge: RendererBridge = stubBridge({
    identify: () =>
      Promise.resolve({
        transport: 'ipc',
        build: identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' }),
      }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: BASE_LOCALE }),
    saveTheme: (theme) => {
      kept.push(theme)
      return Promise.resolve()
    },
    saveLocale: () => Promise.resolve(),
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
  return { kept }
}

beforeEach(() => {
  desktopIsDark(false)
  localStorage.clear()
})

afterEach(() => {
  document.documentElement.className = ''
  document.documentElement.removeAttribute('style')
  localStorage.clear()
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG52: which ground the window is in', () => {
  it('paints dark when dark was chosen', async () => {
    drawIn('dark')

    await painted('dark')
  })

  it('paints light when light was chosen, whatever the desktop says', async () => {
    desktopIsDark(true)
    drawIn('light')

    await painted('light')
  })

  it('follows the desktop when nobody chose, which is the default', async () => {
    desktopIsDark(true)
    drawIn('system')

    await painted('dark')
  })

  it('follows it the other way too, so the default is not just dark by another name', async () => {
    drawIn('system')

    await painted('light')
  })
})

describe('RG52: the control', () => {
  it('says which of the three is set, not which of the two it resolved to', async () => {
    // `system` and `light` paint the same thing on a machine set to light, and the whole
    // reason `system` is a setting is that they are not the same choice.
    drawIn('system')

    await painted('light')
    expect(labelOfControl()).toBe(BASE['ground.system'])
  })

  it('walks the settings and comes back, so there is a way to the desktop', async () => {
    drawIn('system')
    await painted('light')

    const said: string[] = []
    for (let step = 0; step < THEME_ORDER.length; step += 1) {
      said.push(labelOfControl())
      await act(async () => {
        fireEvent.click(screen.getByTestId('ground'))
        await Promise.resolve()
      })
    }

    expect(said).toEqual([BASE['ground.system'], BASE['ground.light'], BASE['ground.dark']])
    expect(labelOfControl()).toBe(BASE['ground.system'])
  })

  it('actually repaints when it is used', async () => {
    drawIn('light')
    await painted('light')

    await act(async () => {
      fireEvent.click(screen.getByTestId('ground'))
      await Promise.resolve()
    })

    await painted('dark')
  })
})

describe('RG87: which copy of the setting wins', () => {
  it('paints what the file says, over what this window remembered last', async () => {
    // The whole defect: `next-themes` prefers its stored value to `defaultTheme`, so a
    // window that had been switched to dark would keep painting dark whatever the file
    // said, and the field a person edited by hand would look broken.
    localStorage.setItem(GROUND_CACHE_KEY, 'dark')
    drawIn('light')

    await painted('light')
  })

  it('leaves the cache holding the file, so the next first frame is right too', async () => {
    localStorage.setItem(GROUND_CACHE_KEY, 'dark')
    drawIn('light')

    await painted('light')
    expect(localStorage.getItem(GROUND_CACHE_KEY)).toBe('light')
  })

  it('sends a change back to the file and not only to browser storage', async () => {
    const bridge = recordingBridge()
    drawIn('light')
    await painted('light')

    await act(async () => {
      fireEvent.click(screen.getByTestId('ground'))
      await Promise.resolve()
    })

    expect(bridge.kept).toEqual(['dark'])
  })

  it('leaves the cache alone when no file answered, which is a browser tab', async () => {
    // The other direction of the same rule: with no source to refresh from, what the
    // browser remembers is the only record there is, and seeding it would lose the choice
    // on every reload.
    localStorage.setItem(GROUND_CACHE_KEY, 'dark')
    drawWindow()

    await painted('dark')
    expect(localStorage.getItem(GROUND_CACHE_KEY)).toBe('dark')
  })

  it('still switches with no bridge, which is what a browser tab gives it', async () => {
    // The file is the source and the window is not held hostage to it: somebody running
    // this as a page still gets the ground they asked for, for as long as the tab lives.
    drawIn('light')
    await painted('light')

    await act(async () => {
      fireEvent.click(screen.getByTestId('ground'))
      await Promise.resolve()
    })

    await painted('dark')
  })
})

describe('RG52: what has to hold in both', () => {
  it('says exactly the same thing in either ground', async () => {
    // The ground changes the palette and never the words: a screen that told somebody
    // something by colour alone would have nothing left to say here.
    //
    // The setting is held at `system` on both runs and the *desktop* is what moves, so the
    // only difference between them is the ground. Choosing `light` then `dark` would move
    // the setting too, and the control says the setting - which would be a difference this
    // is not looking for.
    desktopIsDark(false)
    const light = drawIn('system')
    await painted('light')
    const inLight = visibleText(light.container)
    light.unmount()
    document.documentElement.className = ''

    desktopIsDark(true)
    const dark = drawIn('system')
    await painted('dark')
    const inDark = visibleText(dark.container)

    expect(inDark).toEqual(inLight)
    expect(inDark.length).toBeGreaterThan(0)
  })

  it('leaves the ground on the document element, where a portal can see it', async () => {
    // A dialog or a toast renders outside anything this app wraps, so a class on a wrapper
    // would be a dialog that stays light while the window goes dark.
    drawIn('dark')

    await painted('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('tells the browser too, so the scrollbars and the native controls follow', async () => {
    // A dark window with a white scrollbar is the tell that only the stylesheet moved.
    drawIn('dark')

    await waitFor(() => {
      expect(document.documentElement.style.colorScheme).toBe('dark')
    })
  })
})
