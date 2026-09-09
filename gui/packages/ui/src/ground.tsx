import { DARK_QUERY, groundFor, nextTheme, type Ground, type Theme } from '@rk/core'
import { ThemeProvider, useTheme } from '@viglet/viglet-design-system'
import { useCallback, useEffect, useState, type ReactNode } from 'react'

import { getBridge } from './bridge'

/**
 * The ground, and who owns it.
 *
 * **The design system owns the switch.** It ships `ThemeProvider` over `next-themes`, and
 * its own `Toaster` reads `useTheme` from that same library, so a provider of this app's
 * own would be a second theme system writing the class from a second key — which is the
 * defect the package's own notes say it was consolidated to fix. `next-themes` is a
 * declared dependency of this package for exactly that reason.
 *
 * **`core` owns the resolution.** `useTheme` deliberately reports the *setting*: `system`
 * stays `system`, because the setting is what a person chose. A stylesheet has two grounds
 * and the setting has three, so somebody has to resolve one into the other — that is
 * `groundFor`, it is pure, and it is not the package's job.
 *
 * **The file owns it and the browser caches it.** `next-themes` persists the choice to
 * `localStorage` and reads it back before React runs, which is what stops the first frame
 * being the wrong colour — but a stored value wins over `defaultTheme`, so handing the
 * settings file's answer in as a default would lose to whatever this window remembered
 * last. The cache is written from the setting at mount and written again through the
 * bridge when somebody chooses, so the two cannot drift apart in either direction.
 *
 * What is left here is the join: the desktop's answer, the setting, and the resolved
 * ground a screen can read.
 */

/**
 * The key the design system's `ThemeProvider` persists under, named here because two
 * things now write it: the library, and the seed below. The library takes it as a prop
 * and the default is this — passing it explicitly is what keeps the two from drifting if
 * the package ever changes its own.
 */
export const GROUND_CACHE_KEY = 'vite-ui-theme'

/**
 * Refresh the cache from the setting.
 *
 * Wrapped because storage is not always there: a browser with site data denied throws on
 * the write, and a window that failed to paint its cache is still a window that paints.
 */
function seedGroundCache(theme: Theme): null {
  try {
    localStorage.setItem(GROUND_CACHE_KEY, theme)
  } catch {
    // The setting still reaches the provider; only the first frame of the next launch is
    // at risk, and it falls back to what was handed in.
  }
  return null
}

/**
 * Send the choice back to the file, which is the half browser storage cannot do.
 *
 * Nothing waits on it and a failure is swallowed: the ground has already changed on
 * screen, and a person who cannot write settings has a problem no toast on this control
 * would explain.
 */
function keepGround(theme: Theme): void {
  void getBridge()
    ?.saveTheme(theme)
    .catch(() => undefined)
}

/**
 * What the desktop says, now and whenever it changes.
 *
 * A listener rather than a read at startup: somebody who switches at sunset does not
 * restart their tools, and a window that only looked once is the one still glowing white.
 */
export function useSystemIsDark(): boolean {
  const [isDark, setIsDark] = useState(
    () => typeof matchMedia === 'function' && matchMedia(DARK_QUERY).matches,
  )

  useEffect(() => {
    // `undefined` rather than a bare return: the other path hands React a cleanup.
    if (typeof matchMedia !== 'function') return undefined

    const query = matchMedia(DARK_QUERY)
    const answer = () => {
      setIsDark(query.matches)
    }
    answer()
    query.addEventListener('change', answer)

    return () => {
      query.removeEventListener('change', answer)
    }
  }, [])

  return isDark
}

export interface GroundState {
  /** What is being painted right now. Always one of two. */
  readonly ground: Ground
  /** What was chosen, which is not the same thing — `system` is not a ground. */
  readonly theme: Theme
  readonly setTheme: (theme: Theme) => void
  /** Walk to the next setting, `system` included. */
  readonly cycle: () => void
}

/**
 * What is being painted, what was chosen, and how to change it.
 *
 * Every way of changing it goes through one function, so the write back to the file cannot
 * be the thing a second call site forgets.
 */
export function useGround(): GroundState {
  const { theme, setTheme } = useTheme()
  const systemIsDark = useSystemIsDark()

  const choose = useCallback(
    (next: Theme) => {
      setTheme(next)
      keepGround(next)
    },
    [setTheme],
  )

  const cycle = useCallback(() => {
    choose(nextTheme(theme))
  }, [theme, choose])

  return { ground: groundFor(theme, systemIsDark), theme, setTheme: choose, cycle }
}

/**
 * Mount the ground for the whole window.
 *
 * The class lands on the document element, which is where the tokens are read from: fixed
 * and portalled elements — a dialog, a toast, a popover — render outside whatever this app
 * wraps, and a token they cannot see is a dialog that stays light while the window goes
 * dark. `next-themes` also writes `color-scheme` there, so the scrollbars and the native
 * controls follow; a dark window with a white scrollbar is the tell.
 */
export function GroundProvider({
  initial,
  children,
}: {
  /**
   * The setting as the file holds it. **Absent means no file answered** — a plain browser
   * tab — and is not the same as `system`: with no source to refresh from, what the browser
   * already remembers is the only record of the choice and is left where it is.
   */
  readonly initial?: Theme
  readonly children: ReactNode
}) {
  // Before the child renders, because that is where `next-themes` reads the cache and
  // injects its blocking script. An effect would run after both and repaint the window a
  // frame later, which is the flash this whole arrangement exists to avoid.
  useState(() => (initial === undefined ? null : seedGroundCache(initial)))

  return (
    <ThemeProvider
      defaultTheme={initial ?? 'system'}
      storageKey={GROUND_CACHE_KEY}
      enableSystem
      attribute="class"
    >
      {children}
    </ThemeProvider>
  )
}
