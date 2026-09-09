import { describe, expect, it } from 'vitest'

import { LOCALE_TAGS, LOCALES, wordingFor } from './locales'
import { PT_BR, PT_BR_LOCALE } from './pt-br'
import { BASE, BASE_LOCALE, localeFor, keys, stale, untranslated } from './wording'

describe('RG86: what this build ships', () => {
  it('lists the base and one translation', () => {
    expect(LOCALE_TAGS).toEqual([BASE_LOCALE, PT_BR_LOCALE])
  })

  it('answers the base for its own tag, so English lives in one file', () => {
    expect(wordingFor(BASE_LOCALE)).toEqual({})
  })

  it('answers the base for a tag nobody wrote, rather than throwing', () => {
    expect(wordingFor('ja')).toEqual({})
  })

  it('hands back the stored object, which is what the renderer memoises on', () => {
    expect(wordingFor(PT_BR_LOCALE)).toBe(PT_BR)
    expect(wordingFor('ja')).toBe(wordingFor('zz'))
  })

  it('is the list localeFor chooses among', () => {
    expect(localeFor(PT_BR_LOCALE, LOCALE_TAGS)).toBe(PT_BR_LOCALE)
    expect(localeFor('pt-PT', LOCALE_TAGS)).toBe(PT_BR_LOCALE)
    expect(localeFor('ja', LOCALE_TAGS)).toBe(BASE_LOCALE)
  })
})

describe('RG86: every shipped locale, against the base', () => {
  // The two reports RG51 built and nothing ran. `stale` is the one that catches a rename:
  // a key the base dropped keeps translating nothing, and no screen ever shows it.
  it.each(LOCALE_TAGS)('carries no key the base has dropped: %s', (tag) => {
    expect(stale(wordingFor(tag))).toEqual([])
  })

  it('leaves nothing untranslated in the one translation it ships', () => {
    // The type stays `Partial`, because a translation in progress is worth shipping and
    // falls back per key. What is held complete is the locale this build actually offers,
    // so an English string added without a Portuguese one is a red run and not a screen
    // with a sentence in the wrong language halfway down it.
    expect(untranslated(PT_BR)).toEqual([])
  })

  it('translates every key to something other than the English it replaces', () => {
    // `app.name` excepted: it is the product's name and a locale that changed it would be
    // naming a different program.
    const same = keys().filter((key) => key !== 'app.name' && PT_BR[key] === BASE[key])

    expect(same).toEqual([])
  })
})

describe('RG86: the map itself', () => {
  it('holds one entry per tag, so the list cannot drift from the lookup', () => {
    expect(Object.keys(LOCALES)).toEqual([...LOCALE_TAGS])
  })
})
