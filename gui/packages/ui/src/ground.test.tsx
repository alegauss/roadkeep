import {
  BASE,
  BASE_LOCALE,
  DARK_QUERY,
  DEFAULT_SETTINGS,
  identityFrom,
  isTheme,
  PT_BR,
  PT_BR_LOCALE,
  translator,
  type RendererBridge,
  type Theme,
} from '@rk/core'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import i18next, { changeLanguage } from 'i18next'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { GROUND_CACHE_KEY } from './ground'
import { drawWindow } from './harness'
import { stubBridge } from './stub-bridge'

/**
 * RG52: the ground, from the outside.
 *
 * What is asserted is what a person would see: which ground the document is in, that the
 * header's menu offers all three settings, and that the words on screen do not change with
 * the ground. The switch and the menu are both the design system's (RG238), so what is held
 * here is this app's use of them and not the library.
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

/** The header's ground menu, which is the package's `ModeToggle` inside this app's handle. */
function groundMenu(): HTMLElement {
  return within(screen.getByTestId('ground')).getByRole('button')
}

/**
 * Choose a ground from the header's menu (RG238).
 *
 * By a key and not a click: the package's menu is Radix, which opens on a pointer down or a
 * keystroke, and a keystroke is both what jsdom delivers faithfully and the door a keyboard
 * has. The row is found by its words, which are the settings screen's.
 */
async function chooseInHeader(label: string): Promise<void> {
  fireEvent.keyDown(groundMenu(), { key: 'Enter' })
  const row = await screen.findByRole('menuitem', { name: label })

  await act(async () => {
    fireEvent.click(row)
    await Promise.resolve()
  })
}

/** A bridge that records what reached the file, refusing the first `refusing` writes. */
function recordingBridge(refusing = 0): { kept: Theme[]; refused: Theme[] } {
  const kept: Theme[] = []
  const refused: Theme[] = []
  const bridge: RendererBridge = stubBridge({
    identify: () =>
      Promise.resolve({
        transport: 'ipc',
        build: identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' }),
      }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: BASE_LOCALE }),
    savePreference: (key, value) => {
      if (key !== 'theme' || !isTheme(value)) return Promise.resolve()
      if (refused.length < refusing) {
        refused.push(value)
        return Promise.reject(new Error('the disk is full'))
      }
      kept.push(value)
      return Promise.resolve()
    },
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
  return { kept, refused }
}

/** Let a write that was fired and not awaited land, or be refused. */
async function settle(): Promise<void> {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

beforeEach(() => {
  desktopIsDark(false)
  localStorage.clear()
})

afterEach(async () => {
  document.documentElement.className = ''
  document.documentElement.removeAttribute('style')
  localStorage.clear()
  Reflect.deleteProperty(window, 'roadkeep')
  // i18next is a singleton, so a language one test moved to is the next test's start.
  if (i18next.language !== BASE_LOCALE) await changeLanguage(BASE_LOCALE)
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

describe('RG238: the header`s menu', () => {
  it('offers all three in the settings screen`s words, so there is a way back to the desktop', async () => {
    // `system` and `light` paint the same thing on a machine set to light, and the icon
    // shows the ground being painted — so the menu is where `system` is said, and a menu
    // without it would leave a person who chose a ground no way back to the desktop.
    drawIn('dark')
    await painted('dark')

    fireEvent.keyDown(groundMenu(), { key: 'Enter' })
    const rows = await screen.findAllByRole('menuitem')

    expect(rows.map((row) => row.textContent).toSorted()).toEqual(
      [
        BASE['settings.ground.system'],
        BASE['settings.ground.light'],
        BASE['settings.ground.dark'],
      ].toSorted(),
    )
  })

  it('actually repaints when it is used', async () => {
    drawIn('light')
    await painted('light')

    await chooseInHeader(BASE['settings.ground.dark'])

    await painted('dark')
  })

  it('goes back to following the desktop', async () => {
    drawIn('dark')
    await painted('dark')

    await chooseInHeader(BASE['settings.ground.system'])

    await painted('light')
  })

  it('says this app`s words in the window`s language, not the package`s', async () => {
    // The package ships its own `theme` words — *Alternar tema*, *Sistema* — and a window in
    // Portuguese would wear them beside a settings screen saying *Seguir o sistema*.
    const say = translator(PT_BR, PT_BR_LOCALE)
    await act(async () => {
      await changeLanguage(PT_BR_LOCALE)
    })
    drawIn('light')
    await painted('light')

    expect(groundMenu().textContent).toBe(say('ground.action'))
    fireEvent.keyDown(groundMenu(), { key: 'Enter' })
    const rows = await screen.findAllByRole('menuitem')

    expect(rows.map((row) => row.textContent).toSorted()).toEqual(
      [
        say('settings.ground.system'),
        say('settings.ground.light'),
        say('settings.ground.dark'),
      ].toSorted(),
    )
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
    // The package's menu calls the package's `setTheme` and nothing of this app's, which is
    // the whole reason the write watches the state (RG238): wired to a handler, this was [].
    const bridge = recordingBridge()
    drawIn('light')
    await painted('light')

    await chooseInHeader(BASE['settings.ground.dark'])

    await waitFor(() => {
      expect(bridge.kept).toEqual(['dark'])
    })
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

    await chooseInHeader(BASE['settings.ground.dark'])

    await painted('dark')
  })
})

describe('RG238: what the file is sent, watched on the state and not on a control', () => {
  it('writes nothing at launch, which hands over the ground the file already holds', async () => {
    // A keeper that wrote every ground it saw would write the file back to itself on every
    // start, and the launch is the first ground it sees.
    const bridge = recordingBridge()
    localStorage.setItem(GROUND_CACHE_KEY, 'dark')
    drawIn('light')

    await painted('light')
    await settle()
    expect(bridge.kept).toEqual([])
  })

  it('takes the first ground as what the file holds when no file answered', async () => {
    // A settings read that timed out hands the provider nothing, and the browser's copy is
    // what paints. Writing it would be a person "choosing" whatever this window remembered.
    const bridge = recordingBridge()
    localStorage.setItem(GROUND_CACHE_KEY, 'dark')
    drawWindow()
    await painted('dark')
    await settle()
    expect(bridge.kept).toEqual([])

    await chooseInHeader(BASE['settings.ground.light'])

    await waitFor(() => {
      expect(bridge.kept).toEqual(['light'])
    })
  })

  it('after a refusal, knows the file still holds what it held', async () => {
    // Light on file, dark refused: the file is still light, so choosing light is no write
    // and choosing dark again is one — not a shrug because dark was the last thing sent.
    const bridge = recordingBridge(1)
    drawIn('light')
    await painted('light')

    await chooseInHeader(BASE['settings.ground.dark'])
    await waitFor(() => {
      expect(bridge.refused).toEqual(['dark'])
    })
    await settle()

    await chooseInHeader(BASE['settings.ground.light'])
    await painted('light')
    await settle()
    expect(bridge.kept).toEqual([])

    await chooseInHeader(BASE['settings.ground.dark'])
    await waitFor(() => {
      expect(bridge.kept).toEqual(['dark'])
    })
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
