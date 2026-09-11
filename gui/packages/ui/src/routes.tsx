import type { ReactElement } from 'react'
import { Route, Routes } from 'react-router-dom'

import { HOME_ROUTE, PROJECT_ROUTE, SESSION_ROUTE, TASK_ROUTE } from './areas'
import { Portfolio } from './Portfolio'
import { Project } from './Project'
import { Session } from './Session'
import { AppShell } from './Shell'
import { Task } from './Task'

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

/**
 * The portfolio at `/`, where the scaffold stood until RG145 retired it, one project's backlog
 * (RG148), one of its lines (RG150), and a session that line was handed to (RG153).
 */
export const SURFACES: readonly Surface[] = [
  { path: HOME_ROUTE, element: <Portfolio /> },
  { path: PROJECT_ROUTE, element: <Project /> },
  { path: TASK_ROUTE, element: <Task /> },
  { path: SESSION_ROUTE, element: <Session /> },
]

/** Just the paths, which is what a check about the map needs and all it needs. */
export const ROUTED: readonly string[] = SURFACES.map((surface) => surface.path)

/**
 * The chrome, as the layout route's element. Built once for the reason `Surface.element`
 * is: the router reads it as configuration, and a fresh one per render is a remounted shell.
 */
const SHELL = <AppShell />

/**
 * The table above as the router sees it: the shell as a layout, every surface inside it.
 *
 * Mounted by `main` and by the test harness alike (RG126), each inside its own router. It
 * was written out in both until then, beside two copies of the providers above it, so the
 * array was one and the tree that mounts it was still two.
 */
export function RoutedSurfaces() {
  return (
    <Routes>
      <Route element={SHELL}>
        {SURFACES.map((surface) => (
          <Route key={surface.path} path={surface.path} element={surface.element} />
        ))}
      </Route>
    </Routes>
  )
}
