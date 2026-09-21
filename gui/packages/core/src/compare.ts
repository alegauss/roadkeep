/**
 * One file against what it was, line by line (RG282).
 *
 * The viewer shows each call's two halves (RG246), which answers what one call did and misses
 * what a formatter run after them did. This is the other question — the file now against the
 * file before the session touched it — and it is one comparison rather than ten blocks.
 *
 * **Owned here, with no dependency.** `core` takes none, and a line comparison is small enough
 * to keep: the greedy algorithm Myers published, over whole lines. Words inside a line are not
 * compared: a reviewer reading code reads the line, and a word comparison of code says a great
 * deal about punctuation and little about what changed.
 *
 * **Bounded, and said when it is.** Past `COMPARE_CEILING` lines on either side no comparison is
 * made at all, because the worst case is quadratic in how much differs and a window that hangs
 * on a generated file is worse than one that says it will not read it.
 *
 * Nothing here knows what a file means: it takes two strings and answers which lines are the
 * same, which arrived and which left.
 */

/** How a comparison marks one line. */
export type CompareMark = 'same' | 'added' | 'removed'

export interface CompareLine {
  readonly mark: CompareMark
  /** Its number in the file before, or 0 where the line is not in it. */
  readonly before: number
  /** Its number in the file now, or 0 where the line is not in it. */
  readonly after: number
  readonly text: string
}

/** A run of lines worth drawing, with the unchanged ones around it. */
export interface CompareHunk {
  /** Where this hunk starts on each side, counting from one. */
  readonly before: number
  readonly after: number
  readonly lines: readonly CompareLine[]
}

export interface Comparison {
  readonly hunks: readonly CompareHunk[]
  readonly added: number
  readonly removed: number
  /** True where the two sides are the same text, which is not the same as having no hunks. */
  readonly same: boolean
  /**
   * True where no comparison was made, one side being longer than this reads. The hunks are
   * empty and the counts are zero: an answer of *not compared* rather than *no difference*.
   */
  readonly refused: boolean
}

/** How many unchanged lines are kept around a run of changed ones. */
export const COMPARE_CONTEXT = 3

/**
 * The longest file this compares, in lines on either side.
 *
 * A bundle or a lock file is past it, and those are exactly the files whose comparison nobody
 * reads and whose cost is the highest.
 */
export const COMPARE_CEILING = 2000

/** The lines of a text, without the empty one a final line break leaves behind. */
export function linesOf(text: string): string[] {
  if (text === '') return []
  const lines = text.split('\n')
  if (lines.at(-1) === '') lines.pop()
  return lines
}

/** One line as the comparison walked it, before either side's numbers are on it. */
interface Step {
  readonly mark: CompareMark
  readonly text: string
}

/**
 * The shortest edit script between two line lists, by Myers' greedy algorithm.
 *
 * The trace is one copy of the frontier per round, which is what makes the path walkable
 * backwards; rounds cost what the two sides differ by, so identical files cost one.
 */
function stepsBetween(before: readonly string[], after: readonly string[]): Step[] {
  const n = before.length
  const m = after.length
  const max = n + m
  const offset = max
  const trace: Int32Array[] = []
  const frontier = new Int32Array(2 * max + 1)

  for (let d = 0; d <= max; d += 1) {
    trace.push(frontier.slice())
    for (let k = -d; k <= d; k += 2) {
      const down =
        k === -d || (k !== d && (frontier[k - 1 + offset] ?? 0) < (frontier[k + 1 + offset] ?? 0))
      let x = down ? (frontier[k + 1 + offset] ?? 0) : (frontier[k - 1 + offset] ?? 0) + 1
      let y = x - k
      while (x < n && y < m && before[x] === after[y]) {
        x += 1
        y += 1
      }
      frontier[k + offset] = x
      if (x >= n && y >= m) return walkedBack(trace, before, after, offset)
    }
  }
  return []
}

/** The path the rounds took, read from the end back to the start and then turned around. */
function walkedBack(
  trace: readonly Int32Array[],
  before: readonly string[],
  after: readonly string[],
  offset: number,
): Step[] {
  const steps: Step[] = []
  let x = before.length
  let y = after.length

  for (let d = trace.length - 1; d >= 0; d -= 1) {
    const frontier = trace[d] ?? new Int32Array()
    const k = x - y
    const down =
      k === -d || (k !== d && (frontier[k - 1 + offset] ?? 0) < (frontier[k + 1 + offset] ?? 0))
    const previous = down ? k + 1 : k - 1
    const atX = frontier[previous + offset] ?? 0
    const atY = atX - previous

    while (x > atX && y > atY) {
      steps.push({ mark: 'same', text: before[x - 1] ?? '' })
      x -= 1
      y -= 1
    }
    if (d === 0) break
    if (x === atX) {
      steps.push({ mark: 'added', text: after[y - 1] ?? '' })
      y -= 1
    } else {
      steps.push({ mark: 'removed', text: before[x - 1] ?? '' })
      x -= 1
    }
  }
  return steps.toReversed()
}

/** Each step with its number on the side it belongs to, and zero on the side it does not. */
function numbered(steps: readonly Step[]): CompareLine[] {
  let before = 0
  let after = 0
  return steps.map((step) => {
    if (step.mark !== 'added') before += 1
    if (step.mark !== 'removed') after += 1
    return {
      mark: step.mark,
      text: step.text,
      before: step.mark === 'added' ? 0 : before,
      after: step.mark === 'removed' ? 0 : after,
    }
  })
}

/** The runs worth drawing: what changed, with the unchanged lines around it and no more. */
function hunksOf(lines: readonly CompareLine[]): CompareHunk[] {
  const kept = lines.map((line) => line.mark !== 'same')
  const hunks: CompareHunk[] = []
  let at = 0

  while (at < lines.length) {
    if (!kept[at]) {
      at += 1
      continue
    }
    const from = Math.max(0, at - COMPARE_CONTEXT)
    let to = at
    // Take every change whose context reaches the next one's, so two edits a line apart are
    // one hunk rather than two with the same line drawn twice.
    for (let ahead = at; ahead < lines.length; ahead += 1) {
      if (kept[ahead]) to = ahead
      else if (ahead - to > COMPARE_CONTEXT * 2) break
    }
    const until = Math.min(lines.length, to + COMPARE_CONTEXT + 1)
    const run = lines.slice(from, until)
    const first = run[0]
    hunks.push({ before: first?.before ?? 0, after: first?.after ?? 0, lines: run })
    at = until
  }
  return hunks
}

/**
 * One file against what it was (RG282): the lines that differ, with what surrounds them.
 *
 * A created file's before is empty and every line is added; a deleted file's after is empty and
 * every line is removed. Both are answered without a comparison being run, which is also what
 * makes the common expensive case cheap.
 */
export function linesBetween(before: string, after: string): Comparison {
  const was = linesOf(before)
  const now = linesOf(after)
  const nothing = { hunks: [], added: 0, removed: 0 }

  if (was.length > COMPARE_CEILING || now.length > COMPARE_CEILING) {
    return { ...nothing, same: before === after, refused: true }
  }
  if (before === after) return { ...nothing, same: true, refused: false }

  const steps: Step[] =
    was.length === 0
      ? now.map((text) => ({ mark: 'added', text }) as const)
      : now.length === 0
        ? was.map((text) => ({ mark: 'removed', text }) as const)
        : stepsBetween(was, now)
  const lines = numbered(steps)

  return {
    hunks: hunksOf(lines),
    added: lines.filter((line) => line.mark === 'added').length,
    removed: lines.filter((line) => line.mark === 'removed').length,
    same: false,
    refused: false,
  }
}
