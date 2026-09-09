import { designFrom, whereDesignLives, wordsAgainstLimit, type Design } from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { read, REPO } from './live'

/**
 * The design read against this repository's own rationale file. It is the interesting
 * one: open lines with prose, a shipped line whose section the ship deleted, and a real
 * `[limits] section` the count has to be held against.
 */

/**
 * The design of whatever is open, and the id it belongs to.
 *
 * Called with no id, `brief` picks — which is the only spelling that keeps working. An id
 * written into an assertion is a marker pinned to the day it was written: it is open when
 * the test is committed and shipped by the commit that finishes it, and the failure then
 * belongs to nothing anybody changed.
 */
async function designOfBrief(id?: string): Promise<Design> {
  return designFrom(await read(REPO, 'brief', id === undefined ? {} : { id }))
}

/** Which line that was, so the `show` reads below ask about the same one. */
async function openId(): Promise<string> {
  return (await read(REPO, 'brief', {})).id
}

async function designOfShow(id: string, noBody = false): Promise<Design> {
  return designFrom(await read(REPO, 'show', { id, noBody }))
}

/** Whatever this repository has open, and its design. Both chosen by the engine. */
let id: string
let design: Design

beforeAll(async () => {
  id = await openId()
  design = await designOfBrief()
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
    // `[limits] prose` is the column this project fills to. Every line the engine sent
    // is at or under it, and a screen that re-wrapped would be showing different prose
    // from the one the gate measured.
    expect(design.lines.every((line) => line.length <= 100)).toBe(true)
    expect(design.lines.some((line) => line.length > 40)).toBe(true)
  })

  it('prices the prose against the project own limit, which is never written in here', () => {
    expect(design.budget?.written).toBe(true)
    expect(design.budget?.unit).toBe('words')
    expect(design.budget?.limit).toBeGreaterThan(0)
    expect(wordsAgainstLimit(design)).toContain(`of ${String(design.budget?.limit ?? 0)} words`)
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
    expect(wordsAgainstLimit(gone)).toBe('')
  })
})
