import { BASE } from '@rk/core'
import { bentoNavTarget } from '@viglet/viglet-design-system/bento'
import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { AREAS, surfacesIn } from './areas'
import { drawWindow } from './harness'
import { ROUTED } from './routes'

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
