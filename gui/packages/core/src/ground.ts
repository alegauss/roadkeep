import type { Theme } from './settings'

/**
 * Which ground the window paints, decided.
 *
 * The setting has three values and a stylesheet has two, so something has to resolve one
 * into the other. That is a pure function of the setting and what the desktop says, which
 * is why it is here and not in the renderer: the renderer's job is to stamp the answer.
 *
 * **`system` resolves to a ground, never to nothing.** The design system defines light on
 * bare `:root` and re-points every `--vg-*` under `.dark, [data-theme=dark]`, so leaving
 * the mark off is not *follow the desktop* — it is *light for everybody*, whatever their
 * desktop says.
 *
 * The switch itself is the design system's, which reports the setting and not the ground:
 * `system` stays `system` there, because the setting is what a person chose. This file is
 * the step that library deliberately does not take.
 */

/** What a stylesheet has. Two, always.  */
export type Ground = 'light' | 'dark'

export const GROUNDS: readonly Ground[] = ['light', 'dark']

/**
 * Resolve the setting against the desktop.
 *
 * @param systemIsDark what the desktop says right now. Passed in rather than queried,
 *   because `core` has no window to ask and a test needs to say when.
 */
export function groundFor(theme: Theme, systemIsDark: boolean): Ground {
  if (theme === 'light' || theme === 'dark') return theme
  return systemIsDark ? 'dark' : 'light'
}

/**
 * The order a toggle walks. `system` is in it and is first: a person who set a ground
 * explicitly needs a way back to following the desktop, and a two-state switch has none.
 */
export const THEME_ORDER: readonly Theme[] = ['system', 'light', 'dark']

export function nextTheme(theme: Theme): Theme {
  const at = THEME_ORDER.indexOf(theme)
  return THEME_ORDER[(at + 1) % THEME_ORDER.length] ?? 'system'
}

/**
 * Whether the desktop is what decides right now — which is what a label has to say, since
 * *system* and *light* look identical on a machine set to light.
 */
export function followsSystem(theme: Theme): boolean {
  return theme === 'system'
}

/** The media query that answers `systemIsDark`, named once so nobody retypes it. */
export const DARK_QUERY = '(prefers-color-scheme: dark)'
