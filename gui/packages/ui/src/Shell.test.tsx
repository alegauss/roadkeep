import { BASE, SESSIONS_ROUTE, SETTINGS_ROUTE } from '@rk/core'
import { BENTO_SHELL_SHORTCUTS, bentoNavTarget } from '@viglet/viglet-design-system/bento'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { AREAS, surfacesIn } from './areas'
import { columnAt, COLUMN_CLASS, FULL_WIDTH } from './column'
import { drawWindow } from './harness'
import { ROUTED, SURFACES } from './routes'
import { Session } from './Session'

/**
 * RG63: the chrome, before any screen is written against it.
 *
 * What is asserted is the shell's own contract rather than the design system's components —
 * that the rail is mounted and reserves its gutter, that the two global keys reach the two
 * dialogs, and that the map the rail and the palette share is one array and not two. The
 * components themselves carry the package's own tests.
 */

/**
 * Every route this app serves, read off the table the window mounts (RG117).
 *
 * Written out here, this was a third copy — and the one that decided whether the check
 * below passed, which is the worst of the three to let drift.
 */
const ROUTES = new Set<string>(ROUTED)

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  document.documentElement.className = ''
  localStorage.clear()
})

async function press(key: string, modifier: { ctrlKey?: boolean } = {}): Promise<void> {
  await act(async () => {
    fireEvent.keyDown(window, { key, ...modifier })
    await Promise.resolve()
  })
}

describe('RG63: the shell is mounted, not invented per page', () => {
  it('reserves the rail`s gutter on whatever wraps the routed page', () => {
    // The rail is `fixed`, so without this the first screen renders underneath it and the
    // defect looks like a margin somebody forgot rather than like a missing class.
    const { container } = drawWindow()

    expect(container.querySelector('.bento-rail-gutter')).not.toBeNull()
  })

  it('draws the wordmark and the palette prompt in the chrome, not in the page', () => {
    // Scoped to the header rather than to the document: the home page's own heading is the
    // product name too, which is what a home page's heading is, and the assertion worth
    // making is that the chrome carries its copy and not that only one exists.
    drawWindow()
    // The one outside `main` (RG145). A page's hero is a `header` too, and inside `main` that
    // is not a banner in a browser — the scoping rule jsdom's role table does not apply, so
    // it is applied here rather than by picking whichever banner came first.
    const banner = screen.getAllByRole('banner').find((one) => one.closest('main') === null)
    if (banner === undefined) throw new Error('the chrome drew no banner')
    const header = within(banner)

    expect(header.getByText(BASE['app.name'])).toBeTruthy()
    expect(header.getByText(BASE['shell.palette'])).toBeTruthy()
  })

  it('keeps the ground control in the header, where it is chrome and not one screen`s', () => {
    drawWindow({ initial: 'light' })

    expect(screen.getByTestId('ground')).toBeTruthy()
  })

  it('sets the reading column once, so no page has to', () => {
    // A page setting its own max width is the defect that exists only between two screens,
    // which is why the assertion is that the shell owns it rather than that a page does not.
    const { container } = drawWindow()
    const column = container.querySelector('main')

    expect(column?.className).toMatch(/max-w-/)
    expect(column?.className).toMatch(/mx-auto/)
  })
})

describe('RG237: the shell offers the full width by route, never a page', () => {
  it('draws a session across the window and every other route in the column', () => {
    // Every route the router serves, so a surface added later is read in the column unless
    // the table says otherwise. The width itself is measured in `surfaces.browser.test.tsx`.
    //
    // What a route should get is read off what it draws, never written beside it (RG264): this
    // expected the one session route by name, so when RG263 added a second the check expected
    // the narrow column for it too, and passed over the very screen it exists to hold.
    for (const { path: route, element } of SURFACES) {
      const at = route.replace(':root', 'r').replace(':id', 'RG1').replace(':key', 'k')
      const { container, unmount } = drawWindow({ at })
      const main = container.querySelector('main')
      const wanted = element.type === Session ? 'full' : 'reading'

      expect({ route, column: main?.dataset['column'] }).toEqual({ route, column: wanted })
      expect(main?.className).toContain(COLUMN_CLASS[wanted])
      unmount()
    }
  })

  it('gives the width to every route the session screen answers, and to nothing else', () => {
    // The table against the router's own: a route drawn by `Session` and missing from the list
    // is a narrow session, and one listed that draws something else is a page with no column.
    const drawnBySession = SURFACES.filter((surface) => surface.element.type === Session)

    expect([...FULL_WIDTH].sort()).toEqual(drawnBySession.map((surface) => surface.path).sort())
    expect(drawnBySession.length).toBeGreaterThan(1)
    expect(columnAt('/project/r/task/RG1')).toBe('reading')
    expect(columnAt('/project/r/gate/session/k')).toBe('full')
  })
})

describe('RG267: the keys the shortcuts sheet lists', () => {
  it('opens what the sheet says for every key in the set it reads', async () => {
    // The sheet is the package's and lists the package's set. This window bound two keys of its
    // own, so when the set grew `/` the sheet taught a key that did nothing. Read off the set,
    // so a binding added to it and not answered here is a red run.
    for (const shortcut of BENTO_SHELL_SHORTCUTS) {
      const { unmount } = drawWindow()

      await press(shortcut.key, shortcut.mod === true ? { ctrlKey: true } : {})

      const dialog = await screen.findByRole('dialog')
      // The palette is the one with a box to type in; the sheet has none.
      const typing = within(dialog).queryByRole('combobox') !== null
      expect({ key: shortcut.key, opened: typing ? 'palette' : 'shortcuts' }).toEqual({
        key: shortcut.key,
        opened: shortcut.action,
      })
      unmount()
    }
  })

  it('hints at a key the set binds, and at no other', () => {
    drawWindow()
    const chord = BENTO_SHELL_SHORTCUTS.find((one) => one.action === 'palette' && one.mod === true)

    expect(
      within(screen.getByTestId('palette-trigger')).getByText(
        `Ctrl ${chord?.key.toUpperCase() ?? ''}`,
      ),
    ).toBeTruthy()
  })
})

describe('RG63: the two global keys', () => {
  it('opens the palette on Ctrl K and closes it on the same keys', async () => {
    drawWindow()

    await press('k', { ctrlKey: true })
    expect(await screen.findByRole('dialog')).toBeTruthy()

    await press('k', { ctrlKey: true })
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull()
    })
  })

  it('opens the palette from the header too, for a reader who never learns the key', async () => {
    drawWindow()

    await act(async () => {
      fireEvent.click(screen.getByTestId('palette-trigger'))
      await Promise.resolve()
    })

    expect(await screen.findByRole('dialog')).toBeTruthy()
  })

  it('opens the shortcuts sheet on `?`', async () => {
    drawWindow()

    await press('?')

    expect(await screen.findByRole('dialog')).toBeTruthy()
  })

  it('leaves `?` alone inside something a person is typing into', async () => {
    // A global that fires in a search box is a search box that cannot hold a question mark.
    drawWindow()
    const typed = document.createElement('input')
    document.body.append(typed)
    typed.focus()

    await act(async () => {
      fireEvent.keyDown(typed, { key: '?', bubbles: true })
      await Promise.resolve()
    })

    expect(screen.queryByRole('dialog')).toBeNull()
    typed.remove()
  })

  it('reaches the sheet by a control as well, since there is no user menu to hold it', async () => {
    // The package's own way in is the user menu, which a non-goal forbids here. A shortcut
    // nothing on screen mentions is a shortcut nobody finds.
    drawWindow()

    await act(async () => {
      fireEvent.click(screen.getByTestId('shortcuts'))
      await Promise.resolve()
    })

    expect(await screen.findByRole('dialog')).toBeTruthy()
  })
})

describe('RG63: the map is this app`s and it is one array', () => {
  it('points every entry at a route this app serves', () => {
    // An entry appears when its route does. Vacuous while the rail is Home alone, and the
    // assertion that stops the first added surface from linking to a screen nobody wrote.
    const missing = surfacesIn(AREAS)
      .map((item) => bentoNavTarget(item))
      .filter((route) => !ROUTES.has(route))

    expect(missing).toEqual([])
  })

  it('serves every route the table names, which is what makes this window the window', () => {
    // The other half of RG117. One table is only worth having if what it says is what
    // mounts, so each path is opened and asked for the page inside the chrome — an entry
    // whose element does not render is a route the router matches and nobody can read.
    for (const route of ROUTED) {
      const { container, unmount } = drawWindow({ at: route })

      expect(container.querySelector('main')?.childElementCount).toBeGreaterThan(0)
      unmount()
    }
  })

  it('hands the palette the same surfaces the rail was given', () => {
    // Two arrays would be two answers to what exists, and the one nobody looks at is the
    // one that goes stale.
    const railed = AREAS.flatMap((group) => group.items.map((item) => item.id))

    expect(surfacesIn(AREAS).map((item) => item.id)).toEqual(railed)
  })
})

/**
 * RG221: what the rail actually reaches.
 *
 * `BentoNavRail` draws Home and then one tile per **section**, from `section.areaRoute` and
 * `section.icon` — its first act is to drop every group whose section declares no route.
 * `AREAS` carried the routes on the *items* inside each section, which the rail never reads,
 * so the rail was the Home button alone and the settings and the sessions were reached by the
 * palette or by typing a route. The palette does reach them, which is why it went unseen.
 */
describe('RG221: the rail reaches the surfaces about no project', () => {
  /** Every link the rail draws, by the name a reader hears. */
  function railed(): string[] {
    const rail = document.querySelector('nav')
    if (rail === null) throw new Error('the shell drew no rail')
    return [...rail.querySelectorAll('a')].map(
      (link) => link.getAttribute('aria-label') ?? link.textContent.trim(),
    )
  }

  it('draws a tile for the sessions and one for the settings, beside Home', async () => {
    drawWindow()
    await waitFor(() => {
      expect(railed().length).toBeGreaterThan(1)
    })

    // By their section's label and not their item's: the rail is a strip of sections, which
    // is the package's own contract — `Work` leads to the sessions and `This app` to the
    // settings, each the one surface its section holds.
    expect(railed()).toEqual(['Home', 'Work', 'This app'])
  })

  it('points each tile at the surface its section names', () => {
    drawWindow()
    const rail = document.querySelector('nav')
    const targets = [...(rail?.querySelectorAll('a') ?? [])].map((link) =>
      (link.getAttribute('href') ?? '').replace(/^#/, ''),
    )

    expect(targets).toContain(SESSIONS_ROUTE)
    expect(targets).toContain(SETTINGS_ROUTE)
  })

  it('draws no second tile for the portfolio, which is where Home already leads', () => {
    // The one section deliberately without a route: a rail with two buttons to one screen
    // is worse than the rail that reached nothing.
    const withRoutes = AREAS.filter((group) => group.section.areaRoute !== undefined)

    expect(withRoutes.map((group) => group.section.id)).toEqual(['work', 'app'])
    expect(AREAS.every((group) => group.section.labelKey !== undefined)).toBe(true)
  })
})
