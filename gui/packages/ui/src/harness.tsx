import type { Theme, Wording } from '@rk/core'
import { render, type RenderResult } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { App } from './App'
import { HOME_ROUTE } from './areas'
import { GroundProvider } from './ground'
import { AppShell } from './Shell'
import { WordingProvider } from './wording'

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
 * components render `Link` and a test has no location bar to start from; it takes the routes
 * `main` mounts, so a route added there and not here fails a test rather than a window.
 */
// The same routes `main` mounts, built once: a `Route`'s `element` is configuration the
// router reads rather than a prop a component renders.
const SHELL = <AppShell />
const HOME = <App />

/** Where a render starts. One route so far, so this is the whole of it. */
const AT_HOME = [HOME_ROUTE]

export function drawWindow(
  options: { readonly initial?: Theme; readonly over?: Wording } = {},
): RenderResult {
  return render(
    <GroundProvider initial={options.initial}>
      <WordingProvider over={options.over}>
        <MemoryRouter initialEntries={AT_HOME}>
          <Routes>
            <Route element={SHELL}>
              <Route path={HOME_ROUTE} element={HOME} />
            </Route>
          </Routes>
        </MemoryRouter>
      </WordingProvider>
    </GroundProvider>,
  )
}
