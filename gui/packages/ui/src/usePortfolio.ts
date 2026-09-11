import {
  coldStart,
  gatedRows,
  openingUnreadable,
  openOver,
  pendingRow,
  present,
  rowStages,
  type OpenProject,
  type ProjectGate,
  type ProjectRow,
  type RecordedProject,
  type RowStage,
} from '@rk/core'
import { useCallback, useEffect, useState } from 'react'

import { getBridge } from './bridge'

/** The stage still running, and how far through it the rows are. */
export interface ReadingProgress {
  readonly stage: RowStage
  readonly done: number
  readonly total: number
}

/** The command lines resolution tried, by project path, for a project that did not open. */
export type Tried = Readonly<Record<string, readonly (readonly string[])[]>>

/**
 * What the portfolio has to draw (RG145). Four states and not a nullable list: no bridge,
 * asking, a bridge that would not say, and the list — each drawn differently, and a screen
 * handed an empty array for the first three would claim a machine with no projects on it.
 */
export type PortfolioView =
  | { readonly kind: 'absent' }
  | { readonly kind: 'asking' }
  | { readonly kind: 'failed'; readonly reason: string }
  | {
      readonly kind: 'listed'
      /** In the record's order, never completion order — `coldStart`'s rule. */
      readonly rows: readonly ProjectRow[]
      /** Null once every row has had every read it will get. */
      readonly progress: ReadingProgress | null
      readonly tried: Tried
    }

const ABSENT: PortfolioView = { kind: 'absent' }
const ASKING: PortfolioView = { kind: 'asking' }

/**
 * The projects under the person's roots, read in the renderer over the bridge.
 *
 * Every piece is `core`'s: the carrier's catalogue, `openOver` for each project, and
 * `coldStart` running `rowStages` so rows fill as they land, bounded by the carrier's pool.
 * What is here is the lifetime — one run per mount, and a run whose screen went away draws
 * nothing, which is also what keeps StrictMode's second mount from drawing twice.
 *
 * Each project is opened once and remembered for the second stage, and a project that did
 * not open fails the first with the reason it gave, so `coldStart` never asks it again.
 *
 * `rescan` runs it again from the walk (RG146): the carrier folds a fresh one into its record,
 * so a root just added is walked and one just removed is not. The rows on screen stay until
 * the new list arrives, which is the list the reader was looking at, not an empty one.
 */
export function usePortfolio(): { readonly view: PortfolioView; readonly rescan: () => void } {
  const [view, setView] = useState<PortfolioView>(() =>
    getBridge() === undefined ? ABSENT : ASKING,
  )
  const [generation, setGeneration] = useState(0)
  const rescan = useCallback(() => {
    setGeneration((one) => one + 1)
  }, [])

  useEffect(() => {
    const bridge = getBridge()
    if (bridge === undefined) {
      setView(ABSENT)
      return undefined
    }

    // Asked through a call and not read off a `let`: the cleanup flips it while a read is
    // awaited, which is a change a narrowed boolean would say cannot happen.
    let live = true
    const stillHere = (): boolean => live
    const tried: Record<string, readonly (readonly string[])[]> = {}
    const opened = new Map<string, Promise<OpenProject>>()
    const reach = (recorded: RecordedProject): Promise<OpenProject> => {
      const held = opened.get(recorded.path)
      if (held !== undefined) return held
      const reaching = openOver(bridge, recorded.path).then((reached) => {
        if (reached.kind === 'open') return reached.project
        if (reached.kind === 'unresolved') tried[recorded.path] = reached.tried
        throw openingUnreadable(reached)
      })
      opened.set(recorded.path, reaching)
      return reaching
    }
    const stages = rowStages(reach)
    const stageOf = (name: string): RowStage =>
      stages.find((stage) => stage.name === name)?.name ?? 'counting'

    // A rescan keeps the rows the reader is looking at and says the walk is under way again,
    // rather than blanking a list that is about to come back mostly the same.
    if (generation > 0) {
      setView((was) =>
        was.kind === 'listed'
          ? { ...was, progress: { stage: 'counting', done: 0, total: was.rows.length } }
          : was,
      )
    }

    // What the gate last said, off the carrier's ledger (RG152). A read of what is on record
    // and never a run, so a list of seventeen projects costs nothing to draw and a project
    // nobody has gated stays `unknown` rather than being called clean. It is held here and
    // put on every list below, because the reads that fill a row land after it and a merge
    // done once would be undone by the next stage that finishes.
    // Keyed by root rather than kept as a list, because two of them arrive: what the ledger
    // held when this screen opened, and what the carrier's own runs leave while it is open.
    // A later one about a project wins, whichever it came from, and a slow read of the
    // ledger cannot undo a verdict heard since.
    const verdicts = new Map<string, ProjectGate>()
    // Every subscription this run took, given back when the screen goes.
    const given: (() => void)[] = []
    const dressed = (rows: readonly ProjectRow[]): readonly ProjectRow[] =>
      gatedRows(rows, [...verdicts.values()])

    const redraw = (): void => {
      setView((was) => (was.kind === 'listed' ? { ...was, rows: dressed(was.rows) } : was))
    }

    /** A verdict that landed after the list did, put on its own row and kept for the rest. */
    const heard = (gate: ProjectGate): void => {
      if (!stillHere()) return
      verdicts.set(gate.root, gate)
      redraw()
    }

    const read = async (): Promise<void> => {
      const projects = present(await bridge.projects())
      if (!stillHere()) return
      setView({
        kind: 'listed',
        rows: projects.map(pendingRow),
        progress:
          projects.length === 0 ? null : { stage: 'counting', done: 0, total: projects.length },
        tried: {},
      })

      // The carrier runs the gate for a project whose files moved under its verdict (RG166),
      // which is work this screen did not ask for and cannot wait on — so each row is
      // listened to, and a verdict arriving hours later lands on the row it is about.
      for (const project of projects) {
        given.push(bridge.subscribe('gate', project.path, heard))
      }

      void bridge.gates().then(
        (gates) => {
          if (!stillHere()) return
          // Only where nothing has been heard since: this is the older answer of the two.
          for (const gate of gates) if (!verdicts.has(gate.root)) verdicts.set(gate.root, gate)
          redraw()
        },
        // A carrier that will not say is a column that stays unknown, which is what it says.
        () => undefined,
      )

      const rows = await coldStart(projects, stages, (progress) => {
        if (!stillHere()) return
        setView({
          kind: 'listed',
          rows: dressed(progress.rows),
          progress: { stage: stageOf(progress.stage), done: progress.done, total: progress.total },
          tried: { ...tried },
        })
      })
      if (stillHere()) {
        setView({ kind: 'listed', rows: dressed(rows), progress: null, tried: { ...tried } })
      }
    }

    read().catch((cause: unknown) => {
      if (stillHere()) {
        setView({ kind: 'failed', reason: cause instanceof Error ? cause.message : String(cause) })
      }
    })

    return () => {
      live = false
      for (const give of given) give()
    }
  }, [generation])

  return { view, rescan }
}
