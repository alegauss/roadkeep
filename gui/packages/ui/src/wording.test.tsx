import {
  BASE,
  BASE_LOCALE,
  DEFAULT_SETTINGS,
  EMPTY_CATALOGUE,
  identityFrom,
  isPseudo,
  pseudo,
  PSEUDO_CLOSE,
  PSEUDO_OPEN,
  PRODUCT,
  PT_BR,
  type RendererBridge,
  saidOfBuild,
  translator,
  type Wording,
  wordingFor,
} from '@rk/core'
import { vigDesignSystemTranslations } from '@viglet/viglet-design-system'
import { fireEvent, screen } from '@testing-library/react'
import i18next from 'i18next'
import { afterEach, beforeAll, describe, expect, it } from 'vitest'

import { AREA_WORDING } from './areas'
import { drawWindow } from './harness'
import { choicesAtLaunch } from './launch'
import { startSpeaking } from './speaking'
import { stubBridge } from './stub-bridge'

/**
 * RG51: the test the design rests on.
 *
 * The screen is rendered under a locale nobody speaks, in which every catalogue value is
 * wrapped in brackets. Anything visible without them is a string somebody typed into a
 * component — which this sees on the run after they type it, rather than on the day a
 * second locale is added and every screen has to be reopened.
 *
 * **Both halves of the wording, since RG116.** This app's strings reach the screen two ways:
 * the catalogue, and the i18next bundle the package's own components resolve. The second was
 * empty until the language menu arrived and needed a name, so the run now wraps that bundle
 * too — otherwise adding a string there would be adding one this guard cannot see.
 *
 * **And the whole document, with every surface open, since RG123.** Three of this window's
 * surfaces were invisible here and each for its own reason. The shortcuts sheet and the
 * command palette render into a portal, which is a sibling of the render's `container` and
 * not inside it — measured, and not what the design assumed of the third: `Toaster` renders
 * in place, so the toast was inside the container all along and the run simply never raised
 * one. So this reads `document.body`, opens the two dialogs, and launches against a settings
 * file that lost a field. The first look found two things: a literal in the package's dialog
 * markup, and the English detail RG123's other half moved into the catalogue.
 */
const BUILT = identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' })

function withBridge(parts: Partial<RendererBridge>): void {
  const bridge: RendererBridge = stubBridge({
    identify: () => Promise.resolve({ transport: 'ipc', build: BUILT }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: BASE_LOCALE }),
    saveTheme: () => Promise.resolve(),
    saveLocale: () => Promise.resolve(),
    // A machine with no project under its roots (RG145): the portfolio settles on a sentence
    // of its own, and no payload's prose reaches a screen this run reads.
    projects: () => Promise.resolve(EMPTY_CATALOGUE),
    ...parts,
  })
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
}

/**
 * A launch that lost a setting, which is what puts a toast on the screen.
 *
 * The notice is the reason this run has to reach a portal at all: the frame is a
 * `MessageKey` and the detail is what the reader of the settings file said about the field
 * it reset, so a run that could not see the toast could not see the half of a sentence that
 * was never in the catalogue.
 */
async function launchedWithALoss(): Promise<void> {
  withBridge({
    settings: () =>
      Promise.resolve({
        settings: DEFAULT_SETTINGS,
        reset: [{ lost: 'width', fields: { width: DEFAULT_SETTINGS.width } }],
        locale: BASE_LOCALE,
      }),
  })
  await choicesAtLaunch()
}

afterEach(async () => {
  // The notice list lives with the launch, so a clean launch is what empties it for the
  // next test — the same reason `notices.test.tsx` gives.
  withBridge({})
  await choicesAtLaunch()
  Reflect.deleteProperty(window, 'roadkeep')
})

/**
 * The whole window, chrome included. Since RG63 most of this app's own sentences are in the
 * shell — the wordmark, the palette's prompt, the ground — so a run against the page alone
 * would be a guard that stopped watching the strings most likely to be typed in by hand.
 */
function drawIn(over: Wording | undefined) {
  return drawWindow({ over })
}

/**
 * Every piece of text the rendered screen actually shows, deduplicated.
 *
 * Read off the leaf elements rather than off `textContent` at the root, which would join
 * a wrapped string to an unwrapped one and hide exactly what this is looking for.
 *
 * `script` and `style` are skipped: `next-themes` injects one to set the class before the
 * first paint, and it carries the chosen theme in its source rather than on screen.
 */
const UNREAD = new Set(['SCRIPT', 'STYLE'])

function visibleText(root: HTMLElement): string[] {
  const seen = new Set<string>()
  for (const node of root.querySelectorAll('*')) {
    if (node.children.length > 0 || node.tagName === KEYCAP || UNREAD.has(node.tagName)) continue
    const text = node.textContent.trim()
    if (text !== '') seen.add(text)
  }
  return [...seen]
}

/**
 * The attributes a person reads or hears (RG140).
 *
 * `visibleText` is what a sighted reader sees, and a screen reader says more: a button named
 * by `aria-label`, a field's `placeholder`, a `title`. None is a leaf's text, so the run that
 * found the package's `Close` walked past its `Back to top` in the same window.
 */
const SPOKEN = [
  'alt',
  'aria-description',
  'aria-label',
  'aria-roledescription',
  'aria-valuetext',
  'placeholder',
  'title',
] as const

function spokenNames(root: HTMLElement): string[] {
  const seen = new Set<string>()
  for (const node of root.querySelectorAll('*')) {
    for (const attribute of SPOKEN) {
      const value = node.getAttribute(attribute)?.trim()
      if (value) seen.add(value)
    }
  }
  return [...seen]
}

/**
 * The only text on this screen that is a name and not a sentence.
 *
 * The build line joined them at RG118. It is the same characters in every language on
 * purpose — a version, a commit, `packaged` or `source`, `signed` or not — because what it
 * is for is being pasted into a defect report, and a translated stamp is one that has to be
 * read back before it can be used. `build.test.ts` holds what it says.
 */
const IDENTIFIERS = new Set<string>([PRODUCT, saidOfBuild(BUILT)])

// And no exception for the package's own words, which there was until RG132. The close
// button was `<span class="sr-only">Close</span>` in its markup, found the moment this run
// first looked inside a dialog (RG123), and `aria-label="Back to top"` joined it when the
// run began reading names (RG140). Both were listed rather than filtered by shape, so the
// day they were translated the list would go stale and be deleted. The design system moved
// both into its bundle (VDS93, 2026.3.9): a bare word from the package is now a finding like
// any other.

/** What the package says for one of its own keys, read off its bundle rather than typed. */
function packageSays(group: string, key: string): string {
  const bundle = vigDesignSystemTranslations.en as Record<string, unknown>
  const bento = bundle['bento'] as Record<string, Record<string, string>> | undefined
  return bento?.[group]?.[key] ?? ''
}

/**
 * A sentence only the shortcuts sheet says, read at module scope — which is to say before
 * the wrapping below.
 *
 * `initVigI18n` hands i18next the very object `vigDesignSystemTranslations` exposes, and a
 * deep `addResourceBundle` merges into it: after the wrapping, reading the package's bundle
 * gives back the bracketed string. Measured as `⟦⟦Keyboard shortcuts⟧⟧`.
 *
 * The description and not the title, because `visibleText` reads leaves and the sheet's
 * heading is not one — the element holding it holds an element.
 */
const IN_THE_SHEET = packageSays('shortcuts', 'description')

/** The same brackets `pseudo` uses, over the nested shape an i18next bundle has. */
function pseudoDeep(bundle: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(bundle).map(([key, value]) => [
      key,
      typeof value === 'string'
        ? `${PSEUDO_OPEN}${value}${PSEUDO_CLOSE}`
        : pseudoDeep(value as Record<string, unknown>),
    ]),
  )
}

beforeAll(async () => {
  // The package's components read i18next and nothing else, so the wrapped bundle has to
  // be in the instance itself rather than handed to a provider.
  //
  // The package's own bundle is wrapped beside this app's (RG123), because the surfaces this
  // run now opens are the package's: the palette and the shortcuts sheet say a dozen things
  // out of `vigDesignSystemTranslations`, and unwrapped they would arrive here as a dozen
  // findings about strings this repository does not own. Wrapped, what is left bare is a
  // literal somebody typed into a component — which is the claim, whoever typed it.
  await startSpeaking(BASE_LOCALE)
  i18next.addResourceBundle(
    BASE_LOCALE,
    'translation',
    pseudoDeep({
      ...(vigDesignSystemTranslations.en as Record<string, unknown>),
      ...AREA_WORDING.en,
    }),
    true,
    true,
  )
})

/**
 * A key on the keyboard is not a sentence.
 *
 * `Ctrl K`, `⌘K` and `?` are drawn in `kbd` and are the platform's own names for its keys —
 * translating them would be telling somebody to press a key their keyboard does not have.
 * The element is the claim: anything outside a `kbd` is prose and is held to the rule.
 */
const KEYCAP = 'KBD'

/** What no catalogue accounts for, of what was found. The whole document, portals included. */
function bare(found: readonly string[]): string[] {
  return found.filter((text) => !isPseudo(text) && !IDENTIFIERS.has(text))
}

const bareText = () => bare(visibleText(document.body))
const bareNames = () => bare(spokenNames(document.body))

/**
 * Every surface this window can show, open at once.
 *
 * Together rather than one render each, because the question is about the window and not
 * about any one of them — and because three renders are three places to add a fourth
 * surface and not notice.
 */
async function everySurface(): Promise<void> {
  // The toast first: it is raised on mount, and waiting for its frame is also what says the
  // launch's notice arrived rather than that the run forgot to cause one.
  await screen.findByText(`${PSEUDO_OPEN}${BASE['settings.reset']}${PSEUDO_CLOSE}`)
  fireEvent.click(screen.getByTestId('shortcuts'))
  fireEvent.click(screen.getByTestId('palette-trigger'))
  await screen.findAllByRole('dialog')
}

describe('RG51: nothing on the screen is typed into a component', () => {
  it('wraps every sentence, leaving only the package names bare', async () => {
    await launchedWithALoss()
    drawIn(pseudo())
    // Wait for the bridge to answer, so the portfolio is a settled string and not `asking`.
    await screen.findByText(`${PSEUDO_OPEN}${BASE['portfolio.none']}${PSEUDO_CLOSE}`)
    await everySurface()

    expect(bareText()).toEqual([])
    expect(bareNames()).toEqual([])
  })

  it('finds the literal a component would have kept', () => {
    // The guard on the guard: with nothing wrapped, the check above has to fail — otherwise
    // a green run would prove only that the test does not look.
    drawIn(undefined)

    expect(bareText().length).toBeGreaterThan(0)
  })

  it('finds a name a component would have kept, read off its attributes alone', () => {
    // The same guard for the names (RG140). The shell's two named controls take their names
    // from the catalogue, so unwrapped they are English — and a run that never read an
    // attribute would pass here as it passed over the package's back-to-top button.
    drawIn(undefined)

    expect(bareNames().length).toBeGreaterThan(0)
  })

  it('looks inside a portal, which is where two of these surfaces render', async () => {
    // The gap RG123 closed, held as its own claim rather than left to the check above: the
    // sheet and the palette render into `document.body`, so a run reading the render's own
    // container saw nothing of either — and a literal in one of them read as an empty list.
    // The one this found on its first look was the package's `Close`, translated since RG132.
    await launchedWithALoss()
    const { container } = drawIn(pseudo())
    await everySurface()
    const inTheSheet = `${PSEUDO_OPEN}${IN_THE_SHEET}${PSEUDO_CLOSE}`

    expect(visibleText(container)).not.toContain(inTheSheet)
    expect(visibleText(document.body)).toContain(inTheSheet)
  })

  it('says the same screen in English, which is the base and not a translation', () => {
    drawIn(undefined)

    expect(screen.getByRole('heading', { name: BASE['portfolio.title.unknown'] })).toBeTruthy()
    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
  })
})

describe('RG51: a translation reaches the screen', () => {
  it('draws what the locale says, per key, leaving the rest in English', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'http', build: BUILT }) })
    drawIn({ 'portfolio.footnote': 'Cada número nesta tela foi impresso por um verbo.' })

    expect(screen.getByText('Cada número nesta tela foi impresso por um verbo.')).toBeTruthy()
    // Untranslated, so English — and never the key.
    expect(await screen.findByText(BASE['portfolio.none'])).toBeTruthy()
  })
})

describe('RG86: the locale this build ships', () => {
  // Through `translator` rather than off `PT_BR` directly: the type is `Partial`, and a
  // test reading a key straight out of it would compare against `undefined` the day one
  // goes missing instead of failing on the sentence that is not there.
  const inPtBr = translator(PT_BR)

  it('draws the screen in Portuguese, from the tag alone', async () => {
    withBridge({})
    drawIn(wordingFor('pt-BR'))

    expect(screen.getByText(inPtBr('portfolio.footnote'))).toBeTruthy()
    expect(await screen.findByText(inPtBr('portfolio.none'))).toBeTruthy()
  })

  it('says the base for a tag nobody wrote, which is what an unshipped locale is', () => {
    drawIn(wordingFor('ja'))

    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
  })
})
