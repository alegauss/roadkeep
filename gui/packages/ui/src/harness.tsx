import type { Theme, Wording } from '@rk/core'
import { render, type RenderResult } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { HOME_ROUTE } from './areas'
import { RoutedSurfaces } from './routes'
import { ProviderStack } from './stack'

/**
 * The whole window, as a test renders it.
 *
 * A test instrument and not shipped code — nothing in `main` imports it — kept here because
 * the alternative is every test file spelling the provider stack itself, which is how a
 * piece added to the shell comes to be missing from half the suite.
 *
 * **It renders the shell and not just the page.** Since RG63 the ground control, the palette
 * trigger and the rail are chrome, so a test that rendered `App` alone would be asserting
 * against half a window. `MemoryRouter` rather than `HashRouter` because the routed
 * components render `Link` and a test has no location bar to start from.
 *
 * **The routes are `routes`' and not a second list** (RG117). It used to spell them out
 * beside `main`'s copy, which meant a surface could be added to the window and missed here
 * — and the test that would have caught it renders through this.
 *
 * **And the providers are `stack`'s** (RG126), for the same reason one level up: this
 * mounted the ground, the wording and the route tree beside `main`'s own copy, so a provider
 * added to the window was missing from every test and failed none of them. What is left
 * here is the one thing only a test has — a router with no location bar to start from.
 */

/** Where a render starts unless a test says otherwise, which is the one surface so far. */
const AT_HOME = [HOME_ROUTE]

/**
 * One array per path, kept rather than made.
 *
 * `initialEntries` is a prop, and a fresh array on every render is a router asked to start
 * somewhere new each time — which is also what `react-perf` refuses to let past.
 */
const ENTRIES = new Map<string, string[]>([[HOME_ROUTE, AT_HOME]])

function entriesAt(route: string): string[] {
  const known = ENTRIES.get(route)
  if (known) return known

  const made = [route]
  ENTRIES.set(route, made)
  return made
}

export function drawWindow(
  options: {
    readonly initial?: Theme
    readonly over?: Wording
    /** Which surface to open on, for a test about a route rather than about the chrome. */
    readonly at?: string
  } = {},
): RenderResult {
  return render(
    <ProviderStack initial={options.initial} over={options.over}>
      <MemoryRouter initialEntries={entriesAt(options.at ?? HOME_ROUTE)}>
        <RoutedSurfaces />
      </MemoryRouter>
    </ProviderStack>,
  )
}
