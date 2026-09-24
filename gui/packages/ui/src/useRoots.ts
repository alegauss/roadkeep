import { addRoot, checkRoot, DEFAULT_DEPTH, type KnownRoot } from '@rk/core'
import { toast } from '@viglet/viglet-design-system'
import { useCallback, useEffect, useState } from 'react'

import { getBridge } from './bridge'
import { useWording } from './wording'

/** The roots, as the window holds them: not asked yet, no bridge to ask, or known. */
export type RootsView =
  | { readonly kind: 'absent' }
  | { readonly kind: 'asking' }
  | { readonly kind: 'known'; readonly roots: readonly KnownRoot[] }

export interface Roots {
  readonly view: RootsView
  /** Ask the shell for a folder, and keep it if one was picked. */
  readonly add: () => void
  /** Stop looking under a folder the settings name. */
  readonly remove: (path: string) => void
  /**
   * Look one level deeper or one shallower under a root the file already holds (RG169).
   *
   * A depth out of what `checkRoot` allows is not saved and not reported: the control that
   * offers it is disabled at both ends, so reaching here with one is a caller that ignored
   * the answer, and saving it would be this side arguing with the rule.
   */
  readonly deepen: (path: string, by: number) => void
}

const ABSENT: RootsView = { kind: 'absent' }
const ASKING: RootsView = { kind: 'asking' }

/**
 * Where the window looks, read and written through the bridge (RG146).
 *
 * The list is the person's statement, and until this line the only way to make it was to
 * edit the settings file by hand. A root is added by picking a folder in the shell's dialog
 * and never by typing one, and it is removed by name; every change is saved whole and the
 * answer is the list as the file now holds it, each root marked present or missing.
 *
 * `changed` runs after a save lands, which is where the portfolio walks again: a root just
 * named should show its projects without a second click. A save that fails says so, because
 * a root that looked added and was not is one the person finds missing at the next launch.
 */
export function useRoots(changed: () => void): Roots {
  const say = useWording()
  const [view, setView] = useState<RootsView>(() => (getBridge() === undefined ? ABSENT : ASKING))

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) return undefined
    let live = true
    const stillHere = (): boolean => live
    bridge.roots().then(
      (roots) => {
        if (stillHere()) setView({ kind: 'known', roots })
      },
      () => {
        // Not `known` and empty: a read that failed says nothing about what the file holds,
        // and drawing "no root is named" over a list that has three would be the wrong claim.
        if (stillHere()) setView(ABSENT)
      },
    )
    return () => {
      live = false
    }
  }, [])

  const save = useCallback(
    async (next: readonly { readonly path: string; readonly depth: number }[]) => {
      const bridge = getBridge()
      if (bridge === undefined) return
      try {
        setView({ kind: 'known', roots: await bridge.saveRoots(next) })
        changed()
      } catch (cause) {
        toast.error(
          say('roots.unsaved', { reason: cause instanceof Error ? cause.message : String(cause) }),
        )
      }
    },
    [changed, say],
  )

  const held = view.kind === 'known' ? view.roots : null

  const add = useCallback(() => {
    const bridge = getBridge()
    if (bridge === undefined || held === null) return
    void bridge.chooseRoot().then(async (picked) => {
      if (picked === null) return
      await save([
        ...held.map(({ path, depth }) => ({ path, depth })),
        { path: picked, depth: DEFAULT_DEPTH },
      ])
    })
  }, [held, save])

  const remove = useCallback(
    (path: string) => {
      if (held === null) return
      void save(
        held
          .filter((root) => root.path !== path)
          .map(({ path: kept, depth }) => ({ path: kept, depth })),
      )
    },
    [held, save],
  )

  const deepen = useCallback(
    (path: string, by: number) => {
      if (held === null) return
      const root = held.find((one) => one.path === path)
      if (root === undefined) return
      const checked = checkRoot(path, root.depth + by)
      if (!checked.ok) return
      // The whole list, with one number moved: `addRoot` replaces a depth in place and
      // keeps the position, so the strip does not reorder under the person changing it.
      void save(
        addRoot(
          held.map(({ path: kept, depth }) => ({ path: kept, depth })),
          checked.value,
          (one) => one,
        ),
      )
    },
    [held, save],
  )

  return { view, add, remove, deepen }
}
