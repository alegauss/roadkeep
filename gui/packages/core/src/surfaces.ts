/**
 * Every route the window answers, as the patterns a router matches (RG209).
 *
 * These lived in `ui/areas.ts`, which was right while the router was their only reader. The
 * screenshot run is a second one, and it is in `shell`, which may not import the renderer —
 * so the patterns are here, where both halves read the same list, and `routes.tsx` keeps the
 * elements. A surface routed and never photographed is then a test failing in `shell`, and
 * not a screen an agent is never shown.
 *
 * Patterns only. What each surface is for, and which are on the rail, is still `areas.ts`'s.
 */

/** The portfolio (RG145). */
export const HOME_ROUTE = '/'
/** One project's backlog (RG148), the root in the path. */
export const PROJECT_ROUTE = '/project/:root'
/** Filing a line into one project (RG151). */
export const FILE_ROUTE = '/project/:root/file'
/** One project's gate (RG152). */
export const GATE_ROUTE = '/project/:root/gate'
/** One line of one project (RG150). */
export const TASK_ROUTE = '/project/:root/task/:id'
/** One session this window started, beside the line it was handed (RG153). */
export const SESSION_ROUTE = '/project/:root/task/:id/session/:key'
/** Every session this window started (RG153). */
export const SESSIONS_ROUTE = '/sessions'
/** The preferences a person chooses (RG207). */
export const SETTINGS_ROUTE = '/settings'

/** Every route, once. What the router serves and what the screenshot run visits. */
export const SURFACE_ROUTES: readonly string[] = [
  HOME_ROUTE,
  PROJECT_ROUTE,
  TASK_ROUTE,
  SESSION_ROUTE,
  SESSIONS_ROUTE,
  FILE_ROUTE,
  GATE_ROUTE,
  SETTINGS_ROUTE,
]

/** The parameters a pattern names, in order: `:root` and `:id` for a line. */
export function routeParams(pattern: string): string[] {
  return pattern
    .split('/')
    .filter((segment) => segment.startsWith(':'))
    .map((segment) => segment.slice(1))
}

/**
 * A pattern with every parameter filled and encoded, or null where one has no value.
 *
 * Encoded whole, because a root carries slashes and a drive colon and an id's shape is the
 * project's — the same encoding `areas.ts`'s path builders apply.
 */
export function filledRoute(
  pattern: string,
  values: Readonly<Record<string, string>>,
): string | null {
  let filled = pattern
  for (const name of routeParams(pattern)) {
    const value = values[name]
    if (value === undefined || value === '') return null
    filled = filled.replace(`:${name}`, encodeURIComponent(value))
  }
  return filled
}
