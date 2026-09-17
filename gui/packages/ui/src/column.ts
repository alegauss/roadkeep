import { GATE_SESSION_ROUTE, SESSION_ROUTE } from '@rk/core'
import { matchPath } from 'react-router-dom'

/**
 * How wide the shell draws a page, by route (RG237).
 *
 * The shell owns the reading column, and `authoring.md` makes a variant of it the shell's to
 * offer by name and never a class a page repeats: a page setting its own width is the defect
 * that exists only between two screens. So the variants are here, beside the one table that
 * says which route takes which.
 *
 * **`reading`** is every page: 64rem, which a line of prose and a form are both read at.
 *
 * **`full`** is a workspace, read for minutes rather than top to bottom. The session drew its
 * three regions inside the reading column, and at 1280 that left the stream — where tool calls,
 * their arguments and their output are read — about 360 pixels. Its side panels do not
 * collapse or remember a width, which the same contract refuses as the console era's sidebar.
 */
export type Column = 'reading' | 'full'

/**
 * The routes that take the whole width. A route not listed is read in the column.
 *
 * **Every route the session screen answers, and a test says so** (RG264). RG263 gave the screen a
 * second route and this list did not follow, so a session handed a gate finding came back into
 * the 64rem column RG237 took it out of. A list rather than a rule about path shapes, because a
 * route is full-width for what it draws and not for a word in its pattern; the guard in
 * `Shell.test.tsx` reads the router's own table, so a third route drawn by `Session` and missing
 * here is a red run rather than a narrow screen.
 */
export const FULL_WIDTH: readonly string[] = [SESSION_ROUTE, GATE_SESSION_ROUTE]

/** Each variant's class, written out whole so the stylesheet's scanner finds it. */
export const COLUMN_CLASS: Readonly<Record<Column, string>> = {
  reading: 'max-w-5xl',
  full: 'max-w-none',
}

/** Which column a location is drawn in. */
export function columnAt(pathname: string): Column {
  return FULL_WIDTH.some((route) => matchPath(route, pathname) !== null) ? 'full' : 'reading'
}
