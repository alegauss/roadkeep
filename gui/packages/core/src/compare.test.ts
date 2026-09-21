import { describe, expect, it } from 'vitest'

import { actsIn, originalIn } from './acts'
import { COMPARE_CEILING, COMPARE_CONTEXT, linesBetween, linesOf } from './compare'
import EDIT_LINES from './captured/session-edits.jsonl?raw'

/**
 * RG282: one file against what it was, line by line.
 *
 * What is held here is the answer a reviewer reads: which lines arrived, which left, what
 * surrounds them, and what the two sides' numbers are — a hunk whose numbers are wrong sends
 * somebody to the wrong line of the file they are about to change.
 */

/** A file as a text, from its lines, the way one comes off a disk. */
function text(...lines: readonly string[]): string {
  return lines.length === 0 ? '' : `${lines.join('\n')}\n`
}

/** Ten lines, so a change has room for context on both sides of it. */
const TEN = Array.from({ length: 10 }, (_, at) => `line ${String(at + 1)}`)

describe('RG282: the lines between two versions of a file', () => {
  it('says nothing differs where nothing does, without a hunk to draw', () => {
    const answer = linesBetween(text(...TEN), text(...TEN))

    expect(answer.same).toBe(true)
    expect(answer.hunks).toEqual([])
    expect(answer.added).toBe(0)
    expect(answer.removed).toBe(0)
    expect(answer.refused).toBe(false)
  })

  it('marks a line that was put in the middle, and numbers both sides of it', () => {
    const after = [...TEN.slice(0, 5), 'the new line', ...TEN.slice(5)]
    const answer = linesBetween(text(...TEN), text(...after))

    expect(answer.added).toBe(1)
    expect(answer.removed).toBe(0)
    const [hunk] = answer.hunks
    if (hunk === undefined) throw new Error('no hunk')
    // Three unchanged lines either side of the one that arrived, and no more.
    expect(hunk.lines.map((line) => line.mark)).toEqual([
      'same',
      'same',
      'same',
      'added',
      'same',
      'same',
      'same',
    ])
    const arrived = hunk.lines.find((line) => line.mark === 'added')
    expect(arrived?.text).toBe('the new line')
    // It is the sixth line of the file now, and is in no line of the file before.
    expect(arrived?.after).toBe(6)
    expect(arrived?.before).toBe(0)
    expect(hunk.before).toBe(3)
    expect(hunk.after).toBe(3)
  })

  it('marks a line that went, keeping its number in the file it was in', () => {
    const after = TEN.filter((line) => line !== 'line 5')
    const answer = linesBetween(text(...TEN), text(...after))

    expect(answer.removed).toBe(1)
    const gone = answer.hunks[0]?.lines.find((line) => line.mark === 'removed')
    expect(gone?.text).toBe('line 5')
    expect(gone?.before).toBe(5)
    expect(gone?.after).toBe(0)
  })

  it('reads a replaced line as one that went and one that arrived', () => {
    const after = TEN.map((line) => (line === 'line 5' ? 'line five' : line))
    const answer = linesBetween(text(...TEN), text(...after))

    expect([answer.removed, answer.added]).toEqual([1, 1])
    const marks = answer.hunks[0]?.lines.map((line) => line.mark) ?? []
    expect(marks).toContain('removed')
    expect(marks).toContain('added')
  })

  it('draws two far-apart changes as two hunks, and two near ones as one', () => {
    const long = Array.from({ length: 40 }, (_, at) => `line ${String(at + 1)}`)
    const far = long.map((line, at) => (at === 2 || at === 30 ? `${line} moved` : line))
    expect(linesBetween(text(...long), text(...far)).hunks).toHaveLength(2)

    // Inside the context either side of each other, so one hunk holding both.
    const near = long.map((line, at) => (at === 10 || at === 12 ? `${line} moved` : line))
    const answer = linesBetween(text(...long), text(...near))
    expect(answer.hunks).toHaveLength(1)
    // And the line between them is drawn once, not twice.
    const middle = answer.hunks[0]?.lines.filter((line) => line.text === 'line 12') ?? []
    expect(middle).toHaveLength(1)
  })

  it('reads a file that did not exist as every line arriving', () => {
    const answer = linesBetween('', text(...TEN))

    expect(answer.added).toBe(10)
    expect(answer.removed).toBe(0)
    expect(answer.hunks[0]?.lines.every((line) => line.mark === 'added')).toBe(true)
  })

  it('reads a file that is gone as every line leaving', () => {
    const answer = linesBetween(text(...TEN), '')

    expect(answer.removed).toBe(10)
    expect(answer.added).toBe(0)
    expect(answer.hunks[0]?.lines.every((line) => line.mark === 'removed')).toBe(true)
  })

  it('refuses a file past the ceiling rather than hanging the window on it', () => {
    const huge = Array.from({ length: COMPARE_CEILING + 1 }, (_, at) => `line ${String(at)}`)
    const answer = linesBetween(text(...huge), text(...huge, 'one more'))

    expect(answer.refused).toBe(true)
    expect(answer.hunks).toEqual([])
    // Not the same, and not compared: a screen must be able to tell those apart.
    expect(answer.same).toBe(false)
  })

  it('counts a text by its lines, without the empty one a final break leaves', () => {
    expect(linesOf('a\nb\n')).toEqual(['a', 'b'])
    expect(linesOf('a\nb')).toEqual(['a', 'b'])
    expect(linesOf('')).toEqual([])
    expect(COMPARE_CONTEXT).toBeGreaterThan(0)
  })

  it('keeps every line of both files between the two sides', () => {
    // The whole of the left side is the removed and same lines; the right, the added and same.
    const after = ['a new first line', ...TEN.slice(1, 4), 'a line in the middle', ...TEN.slice(4)]
    const answer = linesBetween(text(...TEN), text(...after))
    const drawn = answer.hunks.flatMap((hunk) => hunk.lines)

    expect(drawn.filter((line) => line.mark !== 'added').map((line) => line.text)).toEqual(
      TEN.slice(0, Math.max(...drawn.map((line) => line.before))),
    )
    expect(drawn.filter((line) => line.mark !== 'removed').map((line) => line.text)).toEqual(
      after.slice(0, Math.max(...drawn.map((line) => line.after))),
    )
  })
})

describe('RG282: the original a comparison is against', () => {
  const acts = actsIn(EDIT_LINES.split('\n').filter((line) => line.trim() !== ''))
  const NEW_FILE = String.raw`D:\tmp\rk-capture\new.txt`
  const OLD_FILE = String.raw`D:\tmp\rk-capture\old.txt`

  it('hands back the file a real run answered with, before it touched it', () => {
    expect(originalIn(acts, OLD_FILE)).toBe('first line\nsecond line\n')
  })

  it('hands back nothing at all for a file the session made, every line being new', () => {
    // A `Write` that created the file answers a null original beside a type of `create`.
    expect(originalIn(acts, NEW_FILE)).toBe('')
    expect(linesBetween(originalIn(acts, NEW_FILE) ?? '', 'hello world\n').added).toBe(1)
  })

  it('says it does not know where no call on the path was answered', () => {
    expect(originalIn(acts, String.raw`D:\tmp\rk-capture\never.txt`)).toBeNull()
  })
})
