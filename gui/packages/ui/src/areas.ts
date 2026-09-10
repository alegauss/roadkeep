import type { Bundle } from '@rk/core'
import type { BentoNavGroup, BentoNavItem } from '@viglet/viglet-design-system/bento'

/**
 * This app's map of itself, which is the one thing the bento layer will not hold.
 *
 * The rail, the hubs and the command palette all render the same array, so a surface listed
 * once is reachable three ways and can never be offered by one and missed by another. The
 * package ships the render contract and no entries: an array in a package would offer
 * Turing's routes inside this window.
 *
 * **An entry appears when its route does.** That is the rule, and it is why this list is
 * nearly empty: the portfolio, the project surface, the task detail, the write path and the
 * agent session are blocks C to F, and a rail button leading nowhere is worse than a rail
 * that grew a button the day the screen behind it opened. `docs/design/` draws all five, and
 * drawing is where they are until they route.
 *
 * **A label here is an i18next key**, not a `MessageKey`, because the package's own
 * components resolve it — which is the rule RG88 settled. The values are registered with
 * i18next in `speaking`, beside the tag that chooses among them.
 */

/** Where the rail's Home button leads, and the one route this app serves so far. */
export const HOME_ROUTE = '/'

/**
 * The sections and their surfaces, already filtered by whatever this reader may see —
 * which here is everything, there being no account and no privileges (a non-goal).
 */
export const AREAS: BentoNavGroup[] = []

/**
 * Every surface, flattened, which is what the palette takes.
 *
 * Derived rather than written a second time: a palette given its own array is a palette
 * that can disagree with the rail about what exists.
 */
export function surfacesIn(groups: readonly BentoNavGroup[]): BentoNavItem[] {
  return groups.flatMap((group) => group.items)
}

/**
 * The nav labels, per language the design system's i18next knows.
 *
 * Keyed `en` and `pt` because those are the two `initVigI18n` merges into; the catalogue's
 * own `pt-BR` resolves to `pt` there, which is what makes one tag serve both systems.
 *
 * `language.toggle` is not a nav label and is here for the same reason (RG116): the language
 * menu is the package's `LanguageSwitcher`, it names itself with that key, and the package
 * ships no `language` namespace at all -- so without these two lines its only name is an
 * English default, in every language. The merge is shallow per top-level key and there is
 * nothing there to overwrite.
 *
 * **`en` is the base here, as it is in the catalogue** (RG125). Nothing compared these two
 * objects until then: a key added to `en` and missed in `pt` drew English inside a
 * Portuguese window, and the pseudo-locale run could not see it. `areas.test.ts` walks them
 * with `bundleGaps` now, which is the same pair of questions `locales.test.ts` asks of the
 * catalogue -- so adding a language means adding an object and nothing else.
 */
export const AREA_WORDING: Readonly<Record<'en' | 'pt', Bundle>> = {
  en: { language: { toggle: 'Change the language' } },
  pt: { language: { toggle: 'Mudar o idioma' } },
}
