import type { ReactElement } from 'react'

import { App } from './App'
import { HOME_ROUTE } from './areas'

/**
 * Every route this app serves, written once (RG117).
 *
 * RG63 left this spelled three times: `main` mounted the routes, `harness` mounted them
 * again so a test could render the same window, and `Shell.test.tsx` kept a third list to
 * check the rail's entries against. Only the first is what a window runs, and the third is
 * what decides whether the check passes — so a surface added to the router and forgotten in
 * the set weakened the guard without failing anything, and one added to the set alone made
 * it pass against a screen nobody had written.
 *
 * **This is not the map.** `AREAS` says what a reader is offered and this says what the
 * router answers, which are different questions: a surface can be routed and deliberately
 * unlisted, and that is why the check between them is a subset and not an equality.
 *
 * `.tsx` rather than a field on `areas.ts`, and that is the whole reason it is a file of
 * its own: an element is JSX, and `areas.ts` is read by the rail and the palette, neither
 * of which should have to compile a component to answer what exists.
 */
export interface Surface {
  /** The path the router matches, which is also what a nav entry points at. */
  readonly path: string
  /**
   * What answers it, built here and not per render: a `Route`'s `element` is configuration
   * the router reads rather than a prop a component renders, so a fresh one every pass is
   * a remount of the whole page.
   */
  readonly element: ReactElement
}

export const SURFACES: readonly Surface[] = [{ path: HOME_ROUTE, element: <App /> }]

/** Just the paths, which is what a check about the map needs and all it needs. */
export const ROUTED: readonly string[] = SURFACES.map((surface) => surface.path)
