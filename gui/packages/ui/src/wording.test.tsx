import {
  BASE,
  BASE_LOCALE,
  DEFAULT_SETTINGS,
  identityFrom,
  isPseudo,
  PACKAGES,
  pseudo,
  PSEUDO_CLOSE,
  PSEUDO_OPEN,
  PT_BR,
  type RendererBridge,
  translator,
  type Wording,
  wordingFor,
} from '@rk/core'
import { screen } from '@testing-library/react'
import i18next from 'i18next'
import { afterEach, beforeAll, describe, expect, it } from 'vitest'

import { AREA_WORDING } from './areas'
import { drawWindow } from './harness'
import { startSpeaking } from './speaking'

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
 */
const BUILT = identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' })

function withBridge(parts: Partial<RendererBridge>): void {
  const bridge: RendererBridge = {
    identify: () => Promise.resolve({ transport: 'ipc', build: BUILT }),
    settings: () => Promise.resolve({ settings: DEFAULT_SETTINGS, reset: [], locale: BASE_LOCALE }),
    saveTheme: () => Promise.resolve(),
    saveLocale: () => Promise.resolve(),
    ...parts,
  }
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
}

afterEach(() => {
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

/** The only text on this screen that is a name and not a sentence. */
const IDENTIFIERS = new Set<string>(PACKAGES)

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
  await startSpeaking(BASE_LOCALE)
  i18next.addResourceBundle(BASE_LOCALE, 'translation', pseudoDeep(AREA_WORDING.en), true, true)
})

/**
 * A key on the keyboard is not a sentence.
 *
 * `Ctrl K`, `⌘K` and `?` are drawn in `kbd` and are the platform's own names for its keys —
 * translating them would be telling somebody to press a key their keyboard does not have.
 * The element is the claim: anything outside a `kbd` is prose and is held to the rule.
 */
const KEYCAP = 'KBD'

describe('RG51: nothing on the screen is typed into a component', () => {
  it('wraps every sentence, leaving only the package names bare', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'ipc', build: BUILT }) })
    const { container } = drawIn(pseudo())
    // Wait for the bridge to answer, so the badge is a settled string and not `asking`.
    await screen.findByText(`${PSEUDO_OPEN}${BASE['transport.ipc']}${PSEUDO_CLOSE}`)

    const bare = visibleText(container).filter((text) => !isPseudo(text) && !IDENTIFIERS.has(text))

    expect(bare).toEqual([])
  })

  it('finds the literal a component would have kept', () => {
    // The guard on the guard: with nothing wrapped, the check above has to fail — otherwise
    // a green run would prove only that the test does not look.
    const { container } = drawIn(undefined)

    const bare = visibleText(container).filter((text) => !isPseudo(text) && !IDENTIFIERS.has(text))

    expect(bare.length).toBeGreaterThan(0)
  })

  it('says the same screen in English, which is the base and not a translation', () => {
    drawIn(undefined)

    expect(screen.getByRole('heading', { name: BASE['app.name'] })).toBeTruthy()
    expect(screen.getByText(BASE['app.tagline'])).toBeTruthy()
  })
})

describe('RG51: a translation reaches the screen', () => {
  it('draws what the locale says, per key, leaving the rest in English', async () => {
    withBridge({ identify: () => Promise.resolve({ transport: 'http', build: BUILT }) })
    drawIn({ 'app.tagline': 'A janela abre e os três pacotes estão ligados.' })

    expect(screen.getByText('A janela abre e os três pacotes estão ligados.')).toBeTruthy()
    // Untranslated, so English — and never the key.
    expect(await screen.findByText(BASE['transport.http'])).toBeTruthy()
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

    expect(screen.getByText(inPtBr('app.tagline'))).toBeTruthy()
    expect(await screen.findByText(inPtBr('transport.ipc'))).toBeTruthy()
  })

  it('says the base for a tag nobody wrote, which is what an unshipped locale is', () => {
    drawIn(wordingFor('ja'))

    expect(screen.getByText(BASE['app.tagline'])).toBeTruthy()
  })
})
