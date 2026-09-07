import type { RecordedProject } from './catalogue'
import type { Unreadable } from './limits'
import { EngineCallFailed } from './transport'
import { pendingRow, readRow, unreadableRow, type ProjectRow, type RowReads } from './portfolio'

/**
 * The first screen, and what it costs.
 *
 * A cold start is the only moment every project is read at once, and the one with no cache
 * to answer from. Three things make it bearable and each is a decision rather than an
 * optimisation.
 *
 * **The fan-out is bounded**, by the pool the transport already goes through. Nothing here
 * counts processes: it hands every project to the transport at once and the pool decides
 * how many run, which is the same ceiling every other read obeys.
 *
 * **Results stream in as they arrive.** A screen that waited for the last project would be
 * blank for as long as the slowest one takes, and the slowest one is usually the broken
 * one.
 *
 * **The order is the recorded list, never completion order.** A list that reorders while
 * somebody is reading it is worse than one that fills in slowly — the row they were about
 * to click moves, for a reason they cannot see.
 *
 * And the reads are staged: the cheapest one that fills a row goes first, so the shape of
 * the screen exists before its detail does. A project that fails a stage is not put through
 * the later ones — three more calls to a project that already could not answer is time
 * taken from the projects that can.
 */

export interface ColdStartStage {
  /** What this stage is doing, in words a screen can show. */
  readonly name: string
  /** Read one project's part of a row. Rejecting is how a project becomes unreadable. */
  read(project: RecordedProject): Promise<RowReads>
}

export interface ColdStartProgress {
  /** The stage now running. */
  readonly stage: string
  /** Projects finished in this stage, out of how many it was given. */
  readonly done: number
  readonly total: number
  /** Every row as it currently stands, in the recorded order. */
  readonly rows: readonly ProjectRow[]
}

/**
 * Turn whatever a stage threw into the state a row carries.
 *
 * Two shapes arrive here and they spell the elapsed time differently: `EngineCallFailed`
 * calls it `durationMs`, an `Unreadable` calls it `elapsedMs`. Reading the wrong one is a
 * silent zero on the row, which is why this matches on the class rather than on a field.
 */
function asUnreadable(cause: unknown, stage: string): Unreadable {
  if (cause instanceof EngineCallFailed) {
    return {
      reason: cause.reason,
      message: cause.message,
      elapsedMs: cause.durationMs,
      argv: [],
      said: '',
    }
  }

  const thrown = cause as Partial<Unreadable> | undefined
  if (typeof thrown?.reason === 'string' && typeof thrown.message === 'string') {
    return {
      reason: thrown.reason,
      message: thrown.message,
      elapsedMs: thrown.elapsedMs ?? 0,
      argv: thrown.argv ?? [],
      said: thrown.said ?? '',
    }
  }

  return {
    reason: 'unreadable-payload',
    message: `${stage} failed: ${cause instanceof Error ? cause.message : String(cause)}`,
    elapsedMs: 0,
    argv: [],
    said: '',
  }
}

/**
 * Read every project, in stages, reporting as it goes.
 *
 * @param onProgress called once per project per stage, with every row as it stands. A
 *   screen redraws from this; nothing here decides how often that is worth doing.
 */
export async function coldStart(
  projects: readonly RecordedProject[],
  stages: readonly ColdStartStage[],
  onProgress: (progress: ColdStartProgress) => void = () => undefined,
): Promise<ProjectRow[]> {
  const rows = projects.map(pendingRow)
  const reads = projects.map((): RowReads => ({}))
  const broken = new Set<number>()

  for (const stage of stages) {
    const live = projects
      .map((project, index) => ({ project, index }))
      .filter(({ index }) => !broken.has(index))

    let done = 0
    await Promise.all(
      live.map(async ({ project, index }) => {
        try {
          const part = await stage.read(project)
          reads[index] = { ...reads[index], ...part }
          rows[index] = readRow(project, reads[index] ?? {})
        } catch (cause) {
          broken.add(index)
          rows[index] = unreadableRow(project, asUnreadable(cause, stage.name))
        }
        done += 1
        onProgress({ stage: stage.name, done, total: live.length, rows: [...rows] })
      }),
    )
  }

  return rows
}
