import { describe, expect, it } from 'vitest'

import { NO_GLOSS } from './gloss'
import {
  glossedLine,
  glossesFrom,
  GLOSSES_KEPT,
  GLOSSES_VERSION,
  GLOSS_SHAPE,
  glossFor,
  glossShapeStands,
  glossStands,
  NOTHING_GLOSSED,
  withGloss,
  type KeptGloss,
} from './glosses'
import type { BriefPayload } from './payloads'

/**
 * RG287: what a machine keeps of a gloss, and when it still answers for the line.
 *
 * Kept by the project, the line and the language, stale by comparison rather than by a clock,
 * and bounded so a cache cannot become a record that grows.
 */

const LINE = {
  id: 'AL1',
  symptom: 'a line ready to start',
  why: 'It is.',
  deps: ['AL0'],
  section: { body: 'the design as it stands' },
  nonGoals: ['No Markdown parsed in this app'],
  doneWhen: ['the tests pass'],
  doneWhenOwn: [],
} as unknown as BriefPayload

const KEPT: KeptGloss = {
  root: 'D:/code/alpha',
  id: 'AL1',
  tag: 'en',
  gloss: { ...NO_GLOSS, headline: 'what it is' },
  version: '2.1.274',
  model: 'claude-opus-5',
  answered: '2026-09-21T10:00:00.000Z',
  shape: GLOSS_SHAPE,
  line: glossedLine(LINE),
}

describe('RG287: a gloss kept by what it answered', () => {
  it('finds one by project, line and language, and keeps two languages apart', () => {
    const both = withGloss(withGloss(NOTHING_GLOSSED, KEPT), {
      ...KEPT,
      tag: 'pt-BR',
      gloss: { ...NO_GLOSS, headline: 'o que é' },
      answered: '2026-09-21T10:05:00.000Z',
    })

    expect(glossFor(both, KEPT.root, 'AL1', 'en')?.gloss.headline).toBe('what it is')
    expect(glossFor(both, KEPT.root, 'AL1', 'pt-BR')?.gloss.headline).toBe('o que é')
    // A window switched to a language nothing was written in has none, and asks anew.
    expect(glossFor(both, KEPT.root, 'AL1', 'fr')).toBeNull()
    expect(glossFor(both, 'D:/code/beta', 'AL1', 'en')).toBeNull()
  })

  it('replaces the one it answers for rather than keeping both', () => {
    const again = withGloss(withGloss(NOTHING_GLOSSED, KEPT), {
      ...KEPT,
      gloss: { ...NO_GLOSS, headline: 'another reading' },
      answered: '2026-09-21T11:00:00.000Z',
    })

    expect(again.glosses).toHaveLength(1)
    expect(glossFor(again, KEPT.root, 'AL1', 'en')?.gloss.headline).toBe('another reading')
  })

  it('drops the oldest past the bound, so a cache cannot grow into a record', () => {
    let kept = NOTHING_GLOSSED
    for (let at = 0; at < GLOSSES_KEPT + 5; at += 1) {
      kept = withGloss(kept, {
        ...KEPT,
        id: `AL${String(at)}`,
        answered: `2026-09-21T${String(at % 24).padStart(2, '0')}:00:00.000Z`,
      })
    }

    expect(kept.glosses).toHaveLength(GLOSSES_KEPT)
    expect(kept.glosses.at(0)?.answered).toBe(
      kept.glosses
        .map((one) => one.answered)
        .toSorted()
        .at(-1),
    )
  })

  it('stands while the line reads as it did, and not once it has moved', () => {
    expect(glossStands(KEPT, LINE)).toBe(true)
    // What a reader would notice: the claim, the reason, the design, the deps, the binds.
    expect(glossStands(KEPT, { ...LINE, symptom: 'something else' })).toBe(false)
    expect(glossStands(KEPT, { ...LINE, why: 'another reason.' })).toBe(false)
    expect(
      glossStands(KEPT, { ...LINE, section: { body: 'rewritten' } } as unknown as BriefPayload),
    ).toBe(false)
    expect(glossStands(KEPT, { ...LINE, deps: ['AL0', 'AL7'] })).toBe(false)
    expect(glossStands(KEPT, { ...LINE, nonGoals: [] })).toBe(false)
    expect(glossStands(KEPT, { ...LINE, doneWhen: ['something else'] })).toBe(false)
  })

  it('stands through what says nothing about the task: a marker, a claim, a readiness', () => {
    const moved = {
      ...LINE,
      status: '🛠',
      readiness: 'blocked',
      held: [{ by: 'another session' }],
    } as unknown as BriefPayload

    expect(glossStands(KEPT, moved)).toBe(true)
  })
})

describe('RG290: the shape a kept gloss was written under', () => {
  it('stands under this build shape, and not under one the answer has since outgrown', () => {
    expect(glossShapeStands(KEPT)).toBe(true)
    expect(glossShapeStands({ ...KEPT, shape: GLOSS_SHAPE - 1 })).toBe(false)
    // Written by a later build, which holds every slot this one draws: asking again would buy
    // nothing, so it stands rather than reading as old.
    expect(glossShapeStands({ ...KEPT, shape: GLOSS_SHAPE + 1 })).toBe(true)
  })

  it('reads an entry with no shape as 0, which is every gloss kept before this', () => {
    // The whole of why the number is on the entry: an older file is read, not thrown away,
    // and what it does not say is the sentence the reader gets.
    const { shape: _dropped, ...before } = KEPT
    const older = glossesFrom(JSON.stringify({ version: GLOSSES_VERSION, glosses: [before] }))

    const entry = older?.glosses[0]
    expect(entry?.shape).toBe(0)
    expect(entry?.gloss.headline).toBe('what it is')
    expect(entry === undefined || glossShapeStands(entry)).toBe(false)
  })

  it('is the oldness the line comparison cannot see, and the two are separate', () => {
    // The symptom exactly: the line has not moved, so nothing is stale, and the gloss still
    // says nothing under the slot the answer grew.
    const outgrown = { ...KEPT, shape: 0 }

    expect(glossStands(outgrown, LINE)).toBe(true)
    expect(glossShapeStands(outgrown)).toBe(false)
  })
})

describe('RG287: the file they are kept in', () => {
  it('reads back what it wrote', () => {
    const kept = withGloss(NOTHING_GLOSSED, KEPT)

    expect(glossesFrom(JSON.stringify(kept))).toEqual(kept)
  })

  it('reads nothing kept from a file that is not one, rather than refusing', () => {
    for (const junk of ['', 'not json', '[1,2]', '{"version":"one"}']) {
      expect(glossesFrom(junk)).toBeNull()
    }
  })

  it('leaves a file from a later build alone, its fields possibly meaning something else', () => {
    const ahead = JSON.stringify({ version: GLOSSES_VERSION + 1, glosses: [] })

    expect(glossesFrom(ahead)).toBeNull()
  })
})
