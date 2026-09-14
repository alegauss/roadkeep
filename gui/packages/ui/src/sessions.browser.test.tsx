import { screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { page } from 'vitest/browser'

import { SESSIONS_ROUTE } from './areas'
import { atSurface } from './surface-harness'

/**
 * RG228: the sessions list at phone width, measured.
 *
 * The list was `grid-cols-[8rem_minmax(0,1fr)_8rem]` on its heading row and on every row, so
 * at 400 wide the middle column had about seventy pixels: the headings *Project* and *State*
 * were drawn over each other and each project's name was cut to a letter. The page did not
 * scroll sideways, so RG214's width run passed it — which is why this reads the columns
 * themselves.
 */

/** The list, drawn and filled from the fixture's one session. */
async function theList(): Promise<HTMLElement> {
  await atSurface(SESSIONS_ROUTE)
  return screen.findByTestId('session')
}

function box(element: Element): DOMRect {
  return element.getBoundingClientRect()
}

beforeEach(async () => {
  localStorage.clear()
  await page.viewport(1280, 800)
})

afterEach(() => {
  localStorage.clear()
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG228: the sessions list at phone width', () => {
  it('gives the project the row at 400 wide, and draws no headings over each other', async () => {
    await page.viewport(400, 800)
    const row = await theList()
    const project = await screen.findByTestId('session-project')

    // Most of the row, where the gridded row left it seventy pixels.
    await waitFor(() => {
      expect(box(project).width).toBeGreaterThan(box(row).width * 0.7)
    })
    // No columns to name, so no names drawn over each other.
    expect(screen.getByTestId('sessions-columns').checkVisibility()).toBe(false)
  })

  it('keeps the three named columns at 1280, side by side', async () => {
    const row = await theList()
    const columns = screen.getByTestId('sessions-columns')

    // The row gridded, which a class check could not say (RG229): the project beside the id.
    const [link, named] = [...row.children].map(box)
    expect(named?.left).toBeGreaterThanOrEqual(link?.right ?? Number.POSITIVE_INFINITY)

    expect(columns.checkVisibility()).toBe(true)
    const [line, project, state] = [...columns.children].map(box)
    expect(line?.right).toBeLessThanOrEqual(project?.left ?? 0)
    expect(project?.right).toBeLessThanOrEqual(state?.left ?? 0)
  })
})
