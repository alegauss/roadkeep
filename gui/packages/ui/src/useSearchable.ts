import { folderName, listedTasks, openOver, type SearchableProject, type TaskLine } from '@rk/core'
import { useCallback, useEffect, useRef, useState } from 'react'

import { getBridge } from './bridge'

/**
 * The lines every open project holds, for a search across all of them (RG147).
 *
 * RG20's `search` matches over payloads this app is holding and never over files. Nothing
 * held any: a portfolio row is built from `stats` and `pick`, and `useProject` keeps a
 * backlog for the one project somebody opened. So this is the store that makes the search
 * possible, and its shape is the one `search` takes.
 *
 * **Read when the palette opens, and never on launch.** A listing per project is a read per
 * project, and paying seventeen of them for a window nobody has typed into is the cold start
 * RG17 exists to bound. Asked on the first open and kept for the session after that: the
 * carrier holds one engine per root and caches against a stamp over the governed files, so
 * the second ask is neither a spawn nor a stale answer.
 *
 * **A project still being read is `null`, not absent.** That is `search`'s own word for
 * *not covered*, and it is what lets the palette say how much of the backlog its answer is
 * about rather than presenting a partial answer as a whole one — which matters most when the
 * answer is empty, since an empty answer is exactly when somebody concludes a line does not
 * exist.
 */
export interface Searchable {
  /** Every project the catalogue holds, each with its lines or null while unread. */
  readonly projects: readonly SearchableProject[]
  /** Start reading, if this has not already. Called when the palette opens. */
  readonly ask: () => void
  /** Whether any project's listing is still in flight. */
  readonly pending: boolean
}

interface Known {
  readonly path: string
  readonly name: string
  readonly lines: readonly TaskLine[] | null
}

export function useSearchable(): Searchable {
  const [known, setKnown] = useState<readonly Known[]>([])
  const [pending, setPending] = useState(false)
  // Asked once per session: the ref and not state, so calling `ask` twice in one render
  // cannot start two sweeps.
  const asked = useRef(false)
  const mounted = useRef(true)
  // Read through a function, the way every effect in this app gives its answer up: a ref
  // read directly narrows to a constant and the gate reports the check as dead.
  const stillHere = useCallback(() => mounted.current, [])

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const ask = useCallback(() => {
    if (asked.current) return
    asked.current = true
    const bridge = getBridge()
    if (bridge === undefined) return

    setPending(true)
    void bridge.projects().then(
      async (catalogue) => {
        const present = catalogue.projects.filter((one) => one.presence === 'present')
        if (!stillHere()) return
        // Named before anything is read, so the palette can say what it does not cover yet
        // rather than looking like it covers everything it has found.
        setKnown(
          present.map((one) => ({ path: one.path, name: folderName(one.path), lines: null })),
        )

        await Promise.all(
          present.map(async (one) => {
            const reached = await openOver(bridge, one.path)
            if (!stillHere() || reached.kind !== 'open') return
            const listed = await reached.project.client.call(one.path, 'list', {})
            if (!stillHere() || listed.kind !== 'read') return
            const lines = listedTasks(listed.value)
            setKnown((was) =>
              was.map((held) => (held.path === one.path ? { ...held, lines } : held)),
            )
          }),
        )
        if (stillHere()) setPending(false)
      },
      () => {
        // A carrier that will not say leaves the store empty, which reads as nothing
        // searched rather than as nothing found.
        if (stillHere()) setPending(false)
      },
    )
  }, [stillHere])

  return { projects: known, ask, pending }
}
