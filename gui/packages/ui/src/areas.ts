import {
  HOME_ROUTE,
  PT_BR,
  PT_BR_LOCALE,
  SESSIONS_ROUTE,
  SETTINGS_ROUTE,
  translator,
  type Bundle,
  type Translate,
} from '@rk/core'
import { IconLayoutGrid, IconSettings, IconTerminal2 } from '@tabler/icons-react'
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

/*
 * The route patterns are `core`'s since RG209, because the screenshot run in `shell` visits
 * the same list the router serves and may not import this package. They are re-exported here
 * so a screen keeps importing its routes from the map it is on.
 *
 * Which of them have an entry in `AREAS` is still this file's rule: the portfolio, the
 * sessions and the settings are about no project, so the rail and the palette reach them. A
 * project, its filing and its gate, a line and one session are each about something a reader
 * chose, and a rail button to one would lead nowhere until it was chosen — a row above it is
 * how a reader arrives.
 */
export {
  FILE_ROUTE,
  GATE_ROUTE,
  GATE_SESSION_ROUTE,
  HOME_ROUTE,
  PROJECT_ROUTE,
  SESSION_ROUTE,
  SESSIONS_ROUTE,
  SETTINGS_ROUTE,
  TASK_ROUTE,
} from '@rk/core'

/** The route for one project. Encoded whole, since a root carries slashes and a drive colon. */
export function projectPath(root: string): string {
  return `/project/${encodeURIComponent(root)}`
}

export function filePath(root: string): string {
  return `${projectPath(root)}/file`
}

export function gatePath(root: string): string {
  return `${projectPath(root)}/gate`
}

/** The route for one line. The id is encoded too: its shape is the project's, not this app's. */
export function taskPath(root: string, id: string): string {
  return `${projectPath(root)}/task/${encodeURIComponent(id)}`
}

export function sessionPath(root: string, id: string, key: string): string {
  return `${taskPath(root, id)}/session/${encodeURIComponent(key)}`
}

/** The route for a session handed a gate finding, which has no line to sit under (RG263). */
export function gateSessionPath(root: string, key: string): string {
  return `${gatePath(root)}/session/${encodeURIComponent(key)}`
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
    // No `areaRoute`, so the rail draws no tile for this one (RG221). `BentoNavRail` lists
    // Home and then a tile per section that declares a route, and this section's surface is
    // the portfolio at `/` — which is where the Home tile already leads. A second button to
    // the same screen is the one thing worse than a rail that reaches nothing.
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
  {
    // The route and the icon the rail reads, beside the ones its single item carries for
    // the palette and a hub (RG221): the rail draws sections and never leaves.
    section: {
      id: 'work',
      labelKey: 'areas.work',
      icon: IconTerminal2,
      areaRoute: SESSIONS_ROUTE,
    },
    items: [
      {
        id: 'sessions',
        titleKey: 'areas.sessions',
        descriptionKey: 'areas.sessionsAbout',
        icon: IconTerminal2,
        section: 'work',
        tone: 'amber',
        bentoRoute: SESSIONS_ROUTE,
        fallbackRoute: SESSIONS_ROUTE,
      },
    ],
  },
  {
    section: {
      id: 'app',
      labelKey: 'areas.app',
      icon: IconSettings,
      areaRoute: SETTINGS_ROUTE,
    },
    items: [
      {
        id: 'settings',
        titleKey: 'areas.settings',
        descriptionKey: 'areas.settingsAbout',
        icon: IconSettings,
        section: 'app',
        tone: 'amber',
        bentoRoute: SETTINGS_ROUTE,
        fallbackRoute: SETTINGS_ROUTE,
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

/** The four `theme` keys the package's `ModeToggle` reads, in one locale's catalogue words. */
function groundMenu(say: Translate): Bundle {
  return {
    toggle: say('ground.action'),
    light: say('settings.ground.light'),
    dark: say('settings.ground.dark'),
    system: say('settings.ground.system'),
  }
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
 * `theme` is the other way round (RG238): the header's ground menu is the package's
 * `ModeToggle`, and the package does ship a `theme` namespace, in words that are not this
 * app's — *Toggle theme* on a control this app calls the ground, and *System* beside a
 * settings screen that says *Follow the desktop*. The merge is deep and the product's leaf
 * wins, so these four replace exactly the four the menu reads. They are read out of the
 * catalogue rather than typed again, so the menu and the settings screen cannot drift apart.
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
    theme: groundMenu(translator()),
    // `areas` and not `nav`: the package ships a `nav` namespace, and a shallow merge would
    // replace its keys with these.
    areas: {
      backlogs: 'Backlogs',
      portfolio: 'Portfolio',
      portfolioAbout: 'Every governed project on this machine, one row each',
      work: 'Work',
      sessions: 'Sessions',
      sessionsAbout: 'Every Claude Code session this window started, one row each',
      app: 'This app',
      settings: 'Settings',
      settingsAbout: 'The ground, the language, and the rest of what you choose here',
    },
  },
  pt: {
    language: { toggle: 'Mudar o idioma' },
    theme: groundMenu(translator(PT_BR, PT_BR_LOCALE)),
    areas: {
      backlogs: 'Pendências',
      portfolio: 'Portfólio',
      portfolioAbout: 'Cada projeto governado nesta máquina, uma linha para cada',
      work: 'Trabalho',
      sessions: 'Sessões',
      sessionsAbout: 'Cada sessão do Claude Code iniciada por esta janela, uma linha para cada',
      app: 'Este aplicativo',
      settings: 'Configurações',
      settingsAbout: 'O fundo, o idioma e o resto do que você escolhe aqui',
    },
  },
}
