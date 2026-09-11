import { BASE_LOCALE, bundleGaps, bundlePaths, keysOf } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { AREA_WORDING, AREAS, HOME_ROUTE, surfacesIn } from './areas'

/**
 * RG125: the half of the wording nothing compared.
 *
 * This app's strings reach the screen two ways. The catalogue is one, and `locales.test.ts`
 * walks every key of the base to hold the one shipped translation complete. `AREA_WORDING`
 * is the other — the labels the design system's own components resolve through i18next —
 * and it is one hand-written object per language that nothing checked against another.
 *
 * RG88 created it empty, so the gap cost nothing; RG116 put the first string in it. A second
 * added to `en` alone would draw English inside a Portuguese window, and RG51's run is not
 * the guard for it: that renders under the base locale, which is the language a missing
 * Portuguese key falls back to.
 *
 * **Every language, not `pt` by name.** The comparison is over whatever languages the object
 * carries, so a third one is an object and not an edit here.
 */
const LANGUAGES = keysOf(AREA_WORDING).filter((language) => language !== BASE_LOCALE)

describe('RG125: every language against the base', () => {
  it('carries a base to compare against, and something in it', () => {
    // The control. An empty base has no untranslated paths in any language, so the checks
    // below would pass on a bundle nobody had written yet.
    expect(bundlePaths(AREA_WORDING[BASE_LOCALE]).length).toBeGreaterThan(0)
    expect(LANGUAGES.length).toBeGreaterThan(0)
  })

  it.each(LANGUAGES)('leaves nothing untranslated: %s', (language) => {
    const gaps = bundleGaps(AREA_WORDING[BASE_LOCALE], AREA_WORDING[language])

    expect(
      gaps.untranslated,
      `these paths are in \`en\` and not in \`${language}\`, so a window speaking it draws` +
        ' the English string — or, where the package ships a default for the key, whatever' +
        ' that says instead.',
    ).toEqual([])
  })

  it.each(LANGUAGES)('carries no path the base has dropped: %s', (language) => {
    const gaps = bundleGaps(AREA_WORDING[BASE_LOCALE], AREA_WORDING[language])

    // The rename catch, and the same one `stale` makes for the catalogue: a key the base
    // stopped naming keeps translating nothing, and no screen ever shows it.
    expect(gaps.stale).toEqual([])
  })

  it.each(LANGUAGES)('says every path in words of its own: %s', (language) => {
    const gaps = bundleGaps(AREA_WORDING[BASE_LOCALE], AREA_WORDING[language])

    // The case the catalogue settles with `app.name`: a name is the same word in either
    // language, and everything else identical is a line copied across and not translated.
    // Nothing here is a name yet — an endonym would be, and the language menu's own labels
    // come from `LOCALE_NAMES` rather than from this object — so the list is empty and the
    // day it is not, whoever adds the name adds the exception beside this.
    expect(
      gaps.identical,
      `these paths say the same words in \`en\` and \`${language}\`. A name is allowed to;` +
        ' a sentence copied across is the thing this catches.',
    ).toEqual([])
  })
})

describe('RG125: the map itself', () => {
  it('offers the portfolio and nothing else, since no other screen routes yet', () => {
    // Stated rather than assumed: the palette and the rail render this array, and a button
    // leading nowhere is worse than a rail that grew one the day its screen opened (RG145).
    expect(surfacesIn(AREAS).map((item) => [item.id, item.bentoRoute])).toEqual([
      ['portfolio', HOME_ROUTE],
    ])
  })
})
