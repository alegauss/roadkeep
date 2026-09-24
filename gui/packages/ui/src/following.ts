import { useEffect, useRef } from 'react'

import { getBridge } from './bridge'

/**
 * Be told when a project's governed files move, for as long as the calling screen is mounted
 * (RG144).
 *
 * What a screen does with it is read again: an agent or a terminal wrote, and the answer the
 * carrier holds is keyed on a stamp of the same files, so rereading is the whole reaction and
 * a spurious move costs one read. Nothing here polls.
 *
 * **The subscription goes with the screen.** It is taken in an effect and given back in that
 * effect's cleanup, so unmounting a screen or opening another project releases the watch main
 * holds for it. The latest `moved` is called without resubscribing, since a screen hands a
 * fresh function on every render and each one would otherwise be a new watch.
 *
 * With no bridge — a test, a plain tab — nothing is heard, which is what that page has.
 */
export function useGovernedMoves(root: string | null, moved: () => void): void {
  const latest = useRef(moved)
  useEffect(() => {
    latest.current = moved
  })

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined || root === null) return undefined
    return bridge.subscribe('governed', root, () => {
      latest.current()
    })
  }, [root])
}
