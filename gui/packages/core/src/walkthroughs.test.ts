import { describe, expect, it } from 'vitest'

import { NO_WALKTHROUGH } from './walkthrough'
import {
  NOTHING_WALKED,
  WALKTHROUGHS_KEPT,
  WALKTHROUGHS_VERSION,
  walkthroughFor,
  walkthroughsFrom,
  walkthroughStands,
  withWalkthrough,
  type KeptWalkthrough,
} from './walkthroughs'

/**
 * RG292: what a machine keeps of a walkthrough, and when it still answers.
 *
 * Kept by the project, the entry and the language, stale by one hash rather than by a clock, and
 * bounded so a cache cannot become a record that grows.
 */

const SHA = '216066b89561b6e9c68f9bab67fe9ffe9ae014a9'

const KEPT: KeptWalkthrough = {
  root: 'D:/code/alpha',
  id: 'AL1',
  tag: 'en',
  walkthrough: {
    ...NO_WALKTHROUGH,
    before: ['a build of the app'],
    steps: [{ does: 'open the task', sees: 'the dialog draws' }],
  },
  version: '2.1.278',
  model: 'claude-opus-5',
  answered: '2026-09-21T10:00:00.000Z',
  commit: SHA,
}

describe('RG292: a walkthrough kept by what it answered', () => {
  it('finds one by project, entry and language, and keeps two languages apart', () => {
    const both = withWalkthrough(withWalkthrough(NOTHING_WALKED, KEPT), {
      ...KEPT,
      tag: 'pt-BR',
      answered: '2026-09-21T10:05:00.000Z',
    })

    expect(walkthroughFor(both, KEPT.root, 'AL1', 'en')?.tag).toBe('en')
    expect(walkthroughFor(both, KEPT.root, 'AL1', 'pt-BR')?.tag).toBe('pt-BR')
    // A window switched to a language nothing was written in has none, and asks anew.
    expect(walkthroughFor(both, KEPT.root, 'AL1', 'fr')).toBeNull()
    expect(walkthroughFor(both, 'D:/code/beta', 'AL1', 'en')).toBeNull()
  })

  it('replaces the one it answers for rather than keeping both', () => {
    const again = withWalkthrough(withWalkthrough(NOTHING_WALKED, KEPT), {
      ...KEPT,
      walkthrough: { ...NO_WALKTHROUGH, nothingToSee: 'a refactor after all' },
      answered: '2026-09-21T11:00:00.000Z',
    })

    expect(again.walkthroughs).toHaveLength(1)
    expect(walkthroughFor(again, KEPT.root, 'AL1', 'en')?.walkthrough.nothingToSee).toBe(
      'a refactor after all',
    )
  })

  it('drops the oldest past the bound, so a cache cannot grow into a record', () => {
    let kept = NOTHING_WALKED
    for (let at = 0; at < WALKTHROUGHS_KEPT + 5; at += 1) {
      kept = withWalkthrough(kept, {
        ...KEPT,
        id: `AL${String(at)}`,
        answered: `2026-09-21T${String(at % 24).padStart(2, '0')}:00:00.000Z`,
      })
    }

    expect(kept.walkthroughs).toHaveLength(WALKTHROUGHS_KEPT)
    expect(kept.walkthroughs.at(0)?.answered).toBe(
      kept.walkthroughs
        .map((one) => one.answered)
        .toSorted()
        .at(-1),
    )
  })
})

describe('RG292: stale is one hash', () => {
  it('stands while the entry still ships from the commit it was written from', () => {
    expect(walkthroughStands(KEPT, SHA)).toBe(true)
    // The whole test, and the reason it is cheaper than a gloss's: the ledger sentence can be
    // corrected without the work changing, and the work cannot change without a new commit.
    expect(walkthroughStands(KEPT, '70aed365ee1c79a9cb73923901f5516ad807ecfe')).toBe(false)
  })

  it('never stands where either side has no hash to compare', () => {
    // A history that cannot place the commit cannot say the answer is still about it, and
    // "probably still fine" is not something this decides on somebody's behalf.
    expect(walkthroughStands(KEPT, '')).toBe(false)
    expect(walkthroughStands({ ...KEPT, commit: '' }, SHA)).toBe(false)
    expect(walkthroughStands({ ...KEPT, commit: '' }, '')).toBe(false)
  })
})

describe('RG292: the file they are kept in', () => {
  it('reads back what it wrote', () => {
    const kept = withWalkthrough(NOTHING_WALKED, KEPT)

    expect(walkthroughsFrom(JSON.stringify(kept))).toEqual(kept)
  })

  it('reads nothing kept from a file that is not one, rather than refusing', () => {
    for (const junk of ['', 'not json', '[1,2]', '{"version":"one"}']) {
      expect(walkthroughsFrom(junk)).toBeNull()
    }
  })

  it('leaves a file from a later build alone, its fields possibly meaning something else', () => {
    const ahead = JSON.stringify({ version: WALKTHROUGHS_VERSION + 1, walkthroughs: [] })

    expect(walkthroughsFrom(ahead)).toBeNull()
  })

  it('reads an entry with no walkthrough in it as one that says nothing', () => {
    // A file half-written, or one from a build whose slots this one does not have: the entry is
    // read and draws nothing, which is the same answer as a run that said nothing.
    const { walkthrough: _dropped, ...bare } = KEPT
    const read = walkthroughsFrom(
      JSON.stringify({ version: WALKTHROUGHS_VERSION, walkthroughs: [bare] }),
    )

    expect(read?.walkthroughs[0]?.walkthrough).toEqual(NO_WALKTHROUGH)
    expect(read?.walkthroughs[0]?.commit).toBe(SHA)
  })
})
