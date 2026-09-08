import {
  listedTasks,
  type ListPayload,
  type Over,
  type RefusedLine,
  type Standing,
  type TaskLine,
} from './payloads'

/**
 * One project's backlog, as the file has it.
 *
 * `stats` answers per block and per marker, which is a shape and not the work: the eight
 * hundred lines under those counts are what somebody opened the project to read. This is
 * those lines.
 *
 * **Both halves are drawn.** The listing carries the lines it accepted *and* the
 * marker-bearing lines the grammar refused, and the refused ones are the half a person
 * most needs — a line with a marker that no verb can read is invisible to every count and
 * every pick while sitting in the file looking exactly like the ones that work. A listing
 * that looks complete when it is not is the failure that read was built to avoid, so
 * hiding them here would undo it one layer up.
 *
 * **The order is the file's own**: the blocks as their headings run, the ids under them.
 * Not because it is the best order but because it is the order every other roadkeep
 * answer speaks in — `brief` says a line is under block C, and a screen that sorted C
 * above A would make that sentence wrong.
 *
 * **A listing can arrive with no lines at all.** A project declaring `[reads] list` gets a
 * listing past that bound answered as its blocks and their counts, the lines withdrawn.
 * That is a narrower answer and not a broken one, so it opens into the same backlog with
 * the blocks it named, no lines under them, and `over` saying what to ask for instead.
 */

export interface BacklogBlock {
  readonly block: string
  /** The heading as written, where the payload carried it. Empty where it did not. */
  readonly name: string
  readonly lines: readonly TaskLine[]
  /** Refused lines the engine could place under this block. */
  readonly refused: readonly RefusedLine[]
  /**
   * How many lines this block holds. The same as `lines.length` for an ordinary listing,
   * and the engine's own count for a bounded one — which is the only number there is when
   * the lines did not come.
   */
  readonly counted: number
}

export interface Backlog {
  readonly file: string
  /** What the listing counted. Not the same as the number of lines in the file. */
  readonly total: number
  /** Blocks in the order the file runs them. */
  readonly blocks: readonly BacklogBlock[]
  /** Every refused line, including the ones no block could be worked out for. */
  readonly refused: readonly RefusedLine[]
  /** Refused lines the engine could not place. Shown on their own rather than dropped. */
  readonly unplaced: readonly RefusedLine[]
  /** Present when the listing was scoped to one block. */
  readonly standing: Standing | null
  /**
   * The bound the lines did not fit under, with the narrower call the engine offers. Null
   * for every listing that carried its lines, which is nearly all of them.
   */
  readonly over: Over | null
  /** False when anything was refused or withheld: the answer is narrower than the file. */
  readonly complete: boolean
}

export function backlogFrom(payload: ListPayload): Backlog {
  const order: string[] = []
  const byBlock = new Map<string, { name: string; lines: TaskLine[]; refused: RefusedLine[] }>()

  const bucket = (block: string, name = '') => {
    let held = byBlock.get(block)
    if (held === undefined) {
      held = { name, lines: [], refused: [] }
      byBlock.set(block, held)
      order.push(block)
    }
    return held
  }

  // The blocks the bound named come first and in its order, so a listing with no lines
  // still opens into the headings the file runs. Nothing invents one: this is the engine's
  // own list, and it is empty for every answer that was not bounded.
  const counts = new Map<string, number>()
  for (const block of payload.over?.blocks ?? []) {
    bucket(block.label, block.name)
    counts.set(block.label, block.counted)
  }

  // Tasks arrive in file order, so first appearance is heading order. Nothing is sorted.
  for (const task of listedTasks(payload)) bucket(task.block).lines.push(task)

  const unplaced: RefusedLine[] = []
  for (const refused of payload.uncounted) {
    if (refused.block === '') {
      unplaced.push(refused)
      continue
    }
    bucket(refused.block).refused.push(refused)
  }

  return {
    file: payload.file,
    total: payload.total,
    blocks: order.map((block) => {
      const held = byBlock.get(block)
      const lines = held?.lines ?? []
      return {
        block,
        name: held?.name ?? '',
        lines,
        refused: held?.refused ?? [],
        counted: counts.get(block) ?? lines.length,
      }
    }),
    refused: payload.uncounted,
    unplaced,
    standing: payload.standing,
    over: payload.over,
    complete: payload.uncounted.length === 0 && payload.over === null,
  }
}

/** Every line, flattened back into file order. */
export function allLines(backlog: Backlog): TaskLine[] {
  return backlog.blocks.flatMap((block) => block.lines)
}

/**
 * What to say about a listing that is narrower than its file.
 *
 * A sentence rather than a count, because "3 uncounted" is a number somebody has to go
 * and interpret, and the reasons are already in the payload.
 */
export function refusedSummary(backlog: Backlog): string {
  if (backlog.over !== null) {
    const door = backlog.over.narrows
    return (
      `${String(backlog.total)} line${backlog.total === 1 ? '' : 's'} in ${backlog.file} ` +
      `were not listed: this read is ${String(backlog.over.characters)} characters against ` +
      `the ${String(backlog.over.limit)} this project declares` +
      (door === ''
        ? ', and no block is small enough to ask for on its own'
        : `, so ask for ${door}`)
    )
  }

  const count = backlog.refused.length
  if (count === 0) return ''

  const one = count === 1
  const reasons = [...new Set(backlog.refused.map((line) => line.reason))]
  return (
    `${String(count)} line${one ? '' : 's'} in ${backlog.file} ${one ? 'carries' : 'carry'} ` +
    `a marker the grammar did not accept, so nothing counts or picks ` +
    `${one ? 'it' : 'them'}: ${reasons.join('; ')}`
  )
}
