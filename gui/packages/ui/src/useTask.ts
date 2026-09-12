import {
  nameOf,
  projectDeclares,
  designFrom,
  detailFrom,
  graphOfBrief,
  lineOf,
  meaningOf,
  openingUnreadable,
  openOver,
  underway,
  whereaboutsOf,
  workingMarker,
  type BriefAnswer,
  type BriefPayload,
  type ConfigPayload,
  type Design,
  type Filings,
  type Graph,
  type ListPayload,
  type OpenProject,
  type ReadOutcome,
  type Refusal,
  type TaskDetail,
  type Underway,
  type Unreadable,
  type Whereabouts,
} from '@rk/core'
import { useEffect, useState } from 'react'

import { getBridge } from './bridge'
import { useGovernedMoves } from './following'

/** A line that opened: the one brief, laid out by `core` and nothing added. */
export interface OpenedTask {
  readonly kind: 'open'
  /**
   * What the project calls itself, or its folder (RG202). Carried here because the back
   * label on this screen is navigation: recomputing it from the path is how five screens
   * came to agree with each other and with nothing else.
   */
  readonly name: string
  readonly detail: TaskDetail
  readonly design: Design
  readonly graph: Graph
  readonly underway: Underway
  /** What the line's marker is for here, read off the config's key names. Empty if none. */
  readonly meaning: string
  /** Whether this project names a working marker, which is what makes the pair answerable. */
  readonly asksWorking: boolean
}

export type TaskView =
  | { readonly kind: 'absent' }
  | { readonly kind: 'opening' }
  /** The project did not open, or the brief could not be read. */
  | { readonly kind: 'refused'; readonly unreadable: Unreadable }
  /** The brief refused, and the three listings said where the id went (RG80). */
  | { readonly kind: 'elsewhere'; readonly whereabouts: Whereabouts }
  | OpenedTask

const ABSENT: TaskView = { kind: 'absent' }
const OPENING: TaskView = { kind: 'opening' }

/** The brief, laid out by `core`, with what the project's config says about its marker. */
function openedTask(line: BriefPayload, config: ConfigPayload | null, root: string): OpenedTask {
  const detail = detailFrom(line)
  const working = config === null ? '' : workingMarker(config)
  return {
    kind: 'open',
    // The same config this already reads for the working marker, which is why naming the
    // project here costs nothing extra (RG202).
    name: nameOf(config === null ? null : projectDeclares(config), root),
    detail,
    design: designFrom(line),
    graph: graphOfBrief(line),
    underway: underway(detail, working),
    meaning: config === null ? '' : (meaningOf(config, line.status)?.label ?? ''),
    asksWorking: working !== '',
  }
}

/**
 * What a brief that did not answer the line said instead.
 *
 * A brief naming an id answers the line or refuses; an empty answer is kept as the engine's
 * own sentence all the same, rather than drawn as a line with no id.
 */
function refusalOf(brief: ReadOutcome<BriefAnswer>): Refusal {
  if (brief.kind === 'refused') return brief.refusal
  const said = brief.kind === 'read' && 'empty' in brief.value ? brief.value.reason : ''
  return { refused: [], beside: '', about: '', said }
}

/** The roadmap, the ledger and the store, each where it answered: a listing nobody read is absent. */
function filingsOf([roadmap, ledger, store]: readonly ReadOutcome<ListPayload>[]): Filings {
  return {
    ...(roadmap?.kind === 'read' ? { roadmap: roadmap.value } : {}),
    ...(ledger?.kind === 'read' ? { ledger: ledger.value } : {}),
    ...(store?.kind === 'read' ? { store: store.value } : {}),
  }
}

/**
 * One line, opened as one `brief` (RG150). Block D's first criterion is that the screen is one
 * read and not six, and `core` already lays the payload out: the detail, the design as the file
 * stores it, the graph the brief resolved and the marker beside the claim.
 *
 * `config` rides beside it, and it is the project's and not the line's: it names the working
 * marker the claim is compared with, and what each marker is for.
 *
 * **A refusal goes looking, and nothing else does** (RG80). A paused line refuses with every
 * typed field empty, so only then are the three listings asked where the id went — the
 * ordinary open line pays for none of them.
 *
 * It rereads when the files move (RG144), keeping what it drew until the new answer lands —
 * and past it, where the reread could not be read at all.
 */
export function useTask(root: string, id: string): TaskView {
  const [view, setView] = useState<TaskView>(() => (getBridge() === undefined ? ABSENT : OPENING))
  const [project, setProject] = useState<OpenProject | null>(null)
  const [generation, setGeneration] = useState(0)
  useGovernedMoves(project === null ? null : root, () => {
    setGeneration((one) => one + 1)
  })

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) {
      setView(ABSENT)
      return undefined
    }
    let live = true
    const stillHere = (): boolean => live
    void openOver(bridge, root).then((reached) => {
      if (!stillHere()) return
      if (reached.kind === 'open') setProject(reached.project)
      else setView({ kind: 'refused', unreadable: openingUnreadable(reached) })
    })
    return () => {
      live = false
    }
  }, [root])

  useEffect(() => {
    if (project === null) return undefined
    let live = true
    const stillHere = (): boolean => live

    void (async () => {
      const [config, brief] = await Promise.all([
        project.client.call(root, 'config', {}),
        project.client.call(root, 'brief', { id }),
      ])
      if (!stillHere()) return

      const line = brief.kind === 'read' ? lineOf(brief.value) : null
      if (line !== null) {
        setView(openedTask(line, config.kind === 'read' ? config.value : null, root))
        return
      }
      if (brief.kind === 'unreadable') {
        // A reread that failed keeps the line it drew: the files moved under it, a write
        // caught halfway is the likeliest reason, and the next move answers again.
        const reread = generation > 0
        setView((was) =>
          reread && was.kind === 'open' ? was : { kind: 'refused', unreadable: brief.unreadable },
        )
        return
      }

      const [roadmap, ledger, store] = await Promise.all([
        project.client.call(root, 'list', {}),
        project.client.call(root, 'list', { role: 'changelog' }),
        project.client.call(root, 'list', { stale: true }),
      ])
      if (!stillHere()) return
      const filings = filingsOf([roadmap, ledger, store])
      setView({
        kind: 'elsewhere',
        whereabouts: whereaboutsOf(root, id, refusalOf(brief), filings),
      })
    })()

    return () => {
      live = false
    }
  }, [project, root, id, generation])

  return view
}
