import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import {
  NOTHING_WALKED,
  NO_WALKTHROUGH,
  WALKTHROUGHS_VERSION,
  withWalkthrough,
  type KeptWalkthrough,
} from '@rk/core'
import { afterAll, describe, expect, it } from 'vitest'

import { removeTree } from './scratch'
import {
  loadWalkthroughs,
  saveWalkthroughs,
  WALKTHROUGHS_FILE,
  walkthroughsPath,
} from './walkthroughs-file'

/**
 * RG292: where a machine keeps the walkthroughs it was answered.
 *
 * `readings-file.test`'s shape and its reason: the round trip, and every way of not having one.
 * A launch with no file, a file somebody broke, and one written by a build that read it
 * differently all answer nothing kept — the window asks Claude Code again, which is what it did
 * before anything was kept — so none of them is an error anybody has to see.
 */

const scratches: string[] = []

function userData(): string {
  const at = mkdtempSync(path.join(tmpdir(), 'rk-walkthroughs-'))
  scratches.push(at)
  return at
}

afterAll(() => {
  for (const at of scratches) removeTree(at)
})

const KEPT: KeptWalkthrough = {
  root: '/code/alpha',
  id: 'AL1',
  tag: 'en',
  walkthrough: {
    ...NO_WALKTHROUGH,
    before: ['a build of the app'],
    steps: [{ does: 'open the entry', sees: 'the steps are drawn' }],
  },
  version: '2.1.278',
  model: 'claude-opus-5',
  answered: '2026-09-21T10:00:00.000Z',
  commit: '216066b89561b6e9c68f9bab67fe9ffe9ae014a9',
}

describe('RG292: the walkthroughs file', () => {
  it('reads back what it wrote', () => {
    const at = userData()
    const kept = withWalkthrough(NOTHING_WALKED, KEPT)

    expect(saveWalkthroughs(at, kept)).toBe(true)
    expect(loadWalkthroughs(at)).toEqual(kept)
  })

  it('is its own file beside the glosses, not a second store inside one', () => {
    // Two questions with different keys, different staleness and different bounds: one file
    // would make the bound on either of them a number about both.
    const at = userData()
    expect(walkthroughsPath(at)).toBe(path.join(at, WALKTHROUGHS_FILE))
    expect(WALKTHROUGHS_FILE).not.toBe('glosses.json')
  })

  it('answers nothing kept where no file has been written yet', () => {
    expect(loadWalkthroughs(userData())).toEqual(NOTHING_WALKED)
  })

  it('answers nothing kept from a file that is not one, rather than failing', () => {
    const at = userData()
    writeFileSync(walkthroughsPath(at), 'not json at all', 'utf8')

    expect(loadWalkthroughs(at)).toEqual(NOTHING_WALKED)
  })

  it('leaves a file from a later build alone, its fields possibly meaning something else', () => {
    const at = userData()
    writeFileSync(
      walkthroughsPath(at),
      JSON.stringify({ version: WALKTHROUGHS_VERSION + 1, walkthroughs: [KEPT] }),
      'utf8',
    )

    expect(loadWalkthroughs(at)).toEqual(NOTHING_WALKED)
  })

  it('writes by rename, so a quit mid-write leaves what was there', () => {
    // What the rename buys, read off the file it wrote: the temporary is gone and the target
    // holds a whole document rather than half of the next one.
    const at = userData()
    saveWalkthroughs(at, withWalkthrough(NOTHING_WALKED, KEPT))

    const written: unknown = JSON.parse(readFileSync(walkthroughsPath(at), 'utf8'))
    expect(written).toHaveProperty('version', WALKTHROUGHS_VERSION)
    expect(existsSync(`${walkthroughsPath(at)}.writing`)).toBe(false)
  })
})
