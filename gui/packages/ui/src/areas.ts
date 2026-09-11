import type { Bundle } from '@rk/core'
import { IconLayoutGrid } from '@tabler/icons-react'
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
 * short: the portfolio routes since RG145, and the project surface, the task detail, the
 * write path and the agent session are blocks D to F — a rail button leading nowhere is worse
 * than a rail that grew a button the day the screen behind it opened. `docs/design/` draws
 * all five, and drawing is where the other four are until they route.
 *
 * **A label here is an i18next key**, not a `MessageKey`, because the package's own
 * components resolve it — which is the rule RG88 settled. The values are registered with
 * i18next in `speaking`, beside the tag that chooses among them.
 */

/** Where the rail's Home button leads, and where the portfolio is (RG145). */
export const HOME_ROUTE = '/'

/**
 * One project's backlog (RG148), the root in the path.
 *
 * No entry in `AREAS`: the surface is always about a project, so a rail button to it would
 * lead nowhere until one was chosen. A portfolio row is how a reader arrives.
 */
export const PROJECT_ROUTE = '/project/:root'

/** The route for one project. Encoded whole, since a root carries slashes and a drive colon. */
export function projectPath(root: string): string {
  return `/project/${encodeURIComponent(root)}`
}

/**
 * One line of one project (RG150), under the project it belongs to. No entry in `AREAS`
 * either, for the same reason: a project's row is how a reader arrives.
 */
export const TASK_ROUTE = '/project/:root/task/:id'

/** The route for one line. The id is encoded too: its shape is the project's, not this app's. */
export function taskPath(root: string, id: string): string {
  return `${projectPath(root)}/task/${encodeURIComponent(id)}`
}

/**
 * The sections and their surfaces, already filtered by whatever this reader may see —
 * which here is everything, there being no account and no privileges (a non-goal).
 *
 * **The portfolio is the first entry, the day its route answers** (RG145). Its section has no
 * hub of its own: the rail's Home button already leads to `/`, and a hub listing the one
 * surface under it would be a second button to the same screen. The palette offers it.
 */
export const AREAS: BentoNavGroup[] = [
  {
    section: { id: 'backlogs', labelKey: 'areas.backlogs' },
    items: [
      {
        id: 'portfolio',
        titleKey: 'areas.portfolio',
        descriptionKey: 'areas.portfolioAbout',
        icon: IconLayoutGrid,
        section: 'backlogs',
        tone: 'amber',
        bentoRoute: HOME_ROUTE,
        fallbackRoute: HOME_ROUTE,
      },
    ],
  },
]

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
  en: {
    language: { toggle: 'Change the language' },
    // `areas` and not `nav`: the package ships a `nav` namespace, and a shallow merge would
    // replace its keys with these.
    areas: {
      backlogs: 'Backlogs',
      portfolio: 'Portfolio',
      portfolioAbout: 'Every governed project on this machine, one row each',
    },
  },
  pt: {
    language: { toggle: 'Mudar o idioma' },
    areas: {
      backlogs: 'Pendências',
      portfolio: 'Portfólio',
      portfolioAbout: 'Cada projeto governado nesta máquina, uma linha para cada',
    },
  },
}
