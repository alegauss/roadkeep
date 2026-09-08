import { DARK_QUERY, groundFor, nextTheme, type Ground, type Theme } from '@rk/core'
import { ThemeProvider, useTheme } from '@viglet/viglet-design-system'
import { useCallback, useEffect, useState, type ReactNode } from 'react'

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
 * What is left here is the join: the desktop's answer, the setting, and the resolved
 * ground a screen can read.
 */

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
    if (typeof matchMedia !== 'function') return

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

/** What is being painted, what was chosen, and how to change it. */
export function useGround(): GroundState {
  const { theme, setTheme } = useTheme()
  const systemIsDark = useSystemIsDark()

  const cycle = useCallback(() => {
    setTheme(nextTheme(theme))
  }, [theme, setTheme])

  return { ground: groundFor(theme, systemIsDark), theme, setTheme, cycle }
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
  initial = 'system',
  children,
}: {
  /** The setting as it was loaded. Absent is following the desktop. */
  readonly initial?: Theme
  readonly children: ReactNode
}) {
  return (
    <ThemeProvider defaultTheme={initial} enableSystem attribute="class">
      {children}
    </ThemeProvider>
  )
}
