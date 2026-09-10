import type { Theme, Wording } from '@rk/core'
import type { ReactNode } from 'react'

import { GroundProvider } from './ground'
import { WordingProvider } from './wording'

/**
 * Everything above the router, written once (RG126).
 *
 * RG117 made the routes one array and left the tree above them spelled twice: `main`
 * mounted the ground, the wording and a router, and `harness` mounted the same three so a
 * test renders the same window. The harness exists so a piece added to the shell is not
 * missing from half the suite, and the stack was the one thing it restated rather than
 * read — so a provider added to `main` and missed there failed nothing. Every test would
 * render a window slightly unlike the one that ships, and pass against the smaller tree.
 *
 * **The router is the child and not a flag.** Two differences between the callers are
 * deliberate and both stay where they are. `main` wraps in `StrictMode` and a test does not,
 * because a double mount is what the launch notices are guarded against and a test asserting
 * one toast would see two. And the routers differ: `HashRouter` because a packaged build is
 * loaded from `file://`, `MemoryRouter` because a test has no location bar. So each caller
 * passes its own router in, with `RoutedSurfaces` inside it, and this knows neither — a
 * prop naming which caller it is would be the version that grows a second prop.
 *
 * A provider that needs the router, reading the location, goes in `RoutedSurfaces`, which is
 * inside it for both callers. One that does not goes here. Either way it is one place.
 */
export function ProviderStack({
  initial,
  over,
  children,
}: {
  /** The ground the settings file holds, or absent where no file answered. */
  readonly initial?: Theme
  /** A translation to force, which is a test's door. Absent is whatever i18next speaks. */
  readonly over?: Wording
  /** The router, with the surfaces inside it. */
  readonly children: ReactNode
}) {
  return (
    <GroundProvider initial={initial}>
      <WordingProvider over={over}>{children}</WordingProvider>
    </GroundProvider>
  )
}
