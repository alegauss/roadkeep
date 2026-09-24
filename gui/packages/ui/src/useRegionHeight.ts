import { REGION_FLOOR_REM, regionHeight } from '@rk/core'
import { useLayoutEffect, useState, type RefObject } from 'react'

/**
 * How much room a region has below its own top (RG217).
 *
 * The measuring half of `regionHeight`, which is `core`'s: this reads the four numbers off the
 * page and that one does the arithmetic. Split because jsdom measures nothing — every rect it
 * reports is zero — so a rule written here could only ever be asserted in a browser, and the
 * part worth asserting is the arithmetic.
 *
 * **Read before paint and again on every resize.** A layout effect, so the region is never
 * drawn at the wrong height first; a `resize` listener, because a window the reader drags is
 * the case a fixed subtraction handles worst.
 *
 * **The gutter is read, not written down.** It is the shell's own bottom padding, off the
 * computed style of the `main` this region is inside — a number copied into a constant here
 * would be a second copy of a stylesheet rule, wrong on the day somebody changes the one that
 * draws.
 *
 * Null until it has measured, which is the first frame of a server-rendered or test tree, and
 * the caller draws without a bound rather than with a guess.
 */
export function useRegionHeight(
  region: RefObject<HTMLElement | null>,
  /**
   * What sits under the region and has to stay in view with it (RG269), whose height is taken off
   * the room as the gutter is. The session's reply box is one: a region measured to the window's
   * bottom leaves anything under it below the fold.
   */
  below?: RefObject<HTMLElement | null>,
  /**
   * Whether anything is under the region now. It is what the room is measured again for: `below`
   * is a ref, which changes nothing when what it points at appears.
   */
  reserving = false,
): number | null {
  const [room, setRoom] = useState<number | null>(null)

  // The function lives in the effect rather than in a `useCallback` above it: what it reads
  // is `region.current`, which a dependency list cannot name, and the compiler says so.
  useLayoutEffect(() => {
    const measure = () => {
      const element = region.current
      if (element === null) return

      const rect = element.getBoundingClientRect()
      const main = element.closest('main')
      const root = element.ownerDocument.documentElement
      const em = Number.parseFloat(getComputedStyle(root).fontSize) || 16

      setRoom(
        regionHeight({
          // The document's coordinates and not the viewport's: a reader part-way down the
          // page is not a reader with less room.
          top: rect.top + window.scrollY,
          viewport: window.innerHeight,
          gutter:
            (main === null ? 0 : Number.parseFloat(getComputedStyle(main).paddingBottom) || 0) +
            (reserving ? (below?.current?.getBoundingClientRect().height ?? 0) : 0),
          floor: REGION_FLOOR_REM * em,
        }),
      )
    }

    measure()
    window.addEventListener('resize', measure)
    return () => {
      window.removeEventListener('resize', measure)
    }
  }, [region, below, reserving])

  return room
}
