import { designFrom, whereDesignLives, type Design } from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { aLine, openWithDesign, read, REPO } from './live'

/**
 * The design read against this repository's own rationale file. It is the interesting
 * one: open lines with prose, a shipped line whose section the ship deleted, and a real
 * `[limits] section` the count has to be held against.
 */

async function designOfBrief(id: string): Promise<Design> {
  return designFrom(aLine(await read(REPO, 'brief', { id })))
}

async function designOfShow(id: string, noBody = false): Promise<Design> {
  return designFrom(await read(REPO, 'show', { id, noBody }))
}

/**
 * The lines roadkeep filled to its column: not a list item or the indented lines that carry
 * one on, and not a table row — the two shapes it inserts as written.
 */
function filledLines(lines: readonly string[]): string[] {
  const filled: string[] = []
  let listed = false
  for (const line of lines) {
    if (/^\s*([-*+]|\d+\.)\s/.test(line) || line.trimStart().startsWith('|')) {
      listed = true
      continue
    }
    if (listed && /^\s+\S/.test(line)) continue
    listed = false
    filled.push(line)
  }
  return filled
}

/**
 * An open line this repository has designed, and its design — found off the listing, never
 * written here: `openWithDesign` says why neither an id nor `pick` is the way to it.
 */
let id: string
let design: Design

beforeAll(async () => {
  id = await openWithDesign()
  design = await designOfBrief(id)
}, 120000)

describe('RG24: a real rationale, as the file keeps it', () => {
  it('opens a section with its prose, its heading and where it lives', () => {
    expect(design.state).toBe('shown')
    expect(design.title).not.toBe('')
    expect(design.prose ?? '').not.toBe('')
    expect(whereDesignLives(design)).toMatch(/\.md:\d+(-\d+)?$/)
  })

  it('leaves the prose byte for byte, so joining the lines is the body again', () => {
    expect(design.lines.length).toBeGreaterThan(1)
    expect(design.lines.join('\n')).toBe(design.prose)
  })

  it('never reflows a body the file already wrapped', () => {
    // `[limits] prose` is the column this project fills to. Every line the engine filled is
    // at or under it, and a screen that re-wrapped would be showing different prose from
    // the one the gate measured. Filled, and not every line (RG163): roadkeep inserts a list
    // or a table as written, so a list item past the column is the file's and not a reflow.
    const filled = filledLines(design.lines)

    expect(filled.every((line) => line.length <= 100)).toBe(true)
    expect(filled.some((line) => line.length > 40)).toBe(true)
  })

  it('prices the prose against the project own limit, which is never written in here', () => {
    expect(design.budget?.written).toBe(true)
    expect(design.budget?.unit).toBe('words')
    expect(design.budget?.limit).toBeGreaterThan(0)
    expect(design.budget?.taken).toBeGreaterThan(0)
  })
})

describe('RG24: the two states that are not prose', () => {
  it('withholds the body when the read did not ask for it, keeping the address', async () => {
    const withheld = await designOfShow(id, true)

    expect(withheld.state).toBe('withheld')
    expect(withheld.prose).toBeNull()
    expect(withheld.words).toBeGreaterThan(0)
    expect(whereDesignLives(withheld)).toMatch(/\.md:\d+(-\d+)?$/)
  })

  it('reads a shipped line as absent, with the engine sentence about the deletion', async () => {
    // RG21 shipped, and the ship deleted its design. A shipped id is the one kind that
    // stays true: nothing unships it. `budget` is null with the section — there is
    // nothing left to price.
    const gone = await designOfBrief('RG21')

    expect(gone.state).toBe('absent')
    expect(gone.absence).not.toBe('')
    expect(gone.budget).toBeNull()
  })
})
