import {
  backlogFrom,
  detailFrom,
  filterAsInput,
  filterChoices,
  openingUnreadable,
  openMarkers,
  openOver,
  underway,
  workingMarker,
  type Backlog,
  type BacklogFilter,
  type BlockStanding,
  type FilterChoices,
  type OpenProject,
  type StatsPayload,
  type Underway,
  type Unreadable,
} from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'
import { useGovernedMoves } from './following'

/** What the project surface has, once the project opened (RG148). */
export interface OpenedSurface {
  readonly kind: 'open'
  readonly project: OpenProject
  readonly stats: StatsPayload | null
  readonly blocks: readonly BlockStanding[]
  readonly choices: FilterChoices
  /** The open markers `status` would accept, in the project's order: the marker chips. */
  readonly markers: readonly string[]
  /** This project's working marker, or empty where it has none. */
  readonly working: string
  /** The lines `list` answered for the filter, or null while that read is out. */
  readonly backlog: Backlog | null
  /** For a line carrying the working marker, the marker and the claim side by side (RG74). */
  readonly underway: Readonly<Record<string, Underway>>
}

export type ProjectView =
  | { readonly kind: 'absent' }
  | { readonly kind: 'opening' }
  | {
      readonly kind: 'refused'
      readonly unreadable: Unreadable
      readonly tried: readonly (readonly string[])[]
    }
  | OpenedSurface

const ABSENT: ProjectView = { kind: 'absent' }
const OPENING: ProjectView = { kind: 'opening' }

/**
 * One project, opened over the bridge and read the way its screen needs it (RG148).
 *
 * Every read is `core`'s and every narrowing goes to the verb: the filter is `filterAsInput`
 * handed to `list`, so the rows are what `roadkeep list` returned for it and never a filter
 * applied in React. Readiness is `deps` per line and never worked out here — one held-engine
 * read each, bounded by the carrier's pool — and only a line carrying the working marker
 * pays for a `brief`, which is the one read that names the claim.
 *
 * **It rereads when the files move** (RG144): a line an agent shipped leaves this list the
 * moment the carrier hears the file change, and the cache it rereads through is keyed on
 * the files, so the second answer is never the first one served again.
 */
export function useProject(root: string, filter: BacklogFilter): ProjectView {
  const [view, setView] = useState<ProjectView>(() =>
    getBridge() === undefined ? ABSENT : OPENING,
  )
  const [project, setProject] = useState<OpenProject | null>(null)
  const [working, setWorking] = useState('')
  const [generation, setGeneration] = useState(0)
  useGovernedMoves(project === null ? null : root, () => {
    setGeneration((one) => one + 1)
  })

  // Open once per root, and read what does not change with the filter.
  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) {
      setView(ABSENT)
      return undefined
    }
    let live = true
    const stillHere = (): boolean => live

    void (async () => {
      const reached = await openOver(bridge, root)
      if (!stillHere()) return
      if (reached.kind !== 'open') {
        setView({
          kind: 'refused',
          unreadable: openingUnreadable(reached),
          tried: reached.kind === 'unresolved' ? reached.tried : [],
        })
        return
      }

      const opened = reached.project
      const [config, stats, blocks] = await Promise.all([
        opened.client.call(root, 'config', {}),
        opened.client.call(root, 'stats', {}),
        opened.client.call(root, 'blockList', {}),
      ])
      if (!stillHere()) return
      const read = config.kind === 'read' ? config.value : null
      const counts = stats.kind === 'read' ? stats.value : null
      setProject(opened)
      setWorking(read === null ? '' : workingMarker(read))
      setView({
        kind: 'open',
        project: opened,
        stats: counts,
        blocks: blocks.kind === 'read' ? blocks.value.blocks : [],
        choices:
          read === null
            ? { blocks: [], roles: [], markers: [], requirements: [] }
            : filterChoices(read, counts),
        markers: read === null ? [] : openMarkers(read),
        working: read === null ? '' : workingMarker(read),
        backlog: null,
        underway: {},
      })
    })()

    return () => {
      live = false
    }
  }, [root])

  // The lines, again for every filter and every move of the files. The filter is the page's
  // state, so it is a new object only when somebody changed a narrowing.
  useEffect(() => {
    if (project === null) return undefined
    let live = true
    const stillHere = (): boolean => live
    const input = filterAsInput(filter)

    void (async () => {
      // The lines on screen stay until the new ones land: a file moving under an open screen
      // is a reread, and blanking the list for it would flash the rows away and back.
      const listed = await project.client.call(root, 'list', input)
      if (!stillHere() || listed.kind !== 'read') return
      const backlog = backlogFrom(listed.value)
      // After the files moved, each row keeps what it had until its own read
      // answers again, rather than every row flashing back to asking. A new narrowing is a
      // new list, and starts from nothing.
      const reread = generation > 0
      setView((was) =>
        was.kind === 'open'
          ? {
              ...was,
              backlog,
              underway: reread ? was.underway : {},
            }
          : was,
      )

      // Readiness comes off the listing now (RG170), so nothing is asked per row for it:
      // `list` already classifies every open line to produce its own `startable` count, and
      // a `deps` call per line was eight hundred reads to draw one screen.
      await Promise.all(
        backlog.blocks
          .flatMap((block) => block.lines)
          .map(async (line) => {
            if (working === '' || line.status !== working) return
            const brief = await project.client.call(root, 'brief', { id: line.id })
            if (!stillHere() || brief.kind !== 'read' || 'empty' in brief.value) return
            const state = underway(detailFrom(brief.value), working)
            setView((was) =>
              was.kind === 'open'
                ? { ...was, underway: { ...was.underway, [line.id]: state } }
                : was,
            )
          }),
      )
    })()

    return () => {
      live = false
    }
  }, [project, root, filter, working, generation])

  return view
}
