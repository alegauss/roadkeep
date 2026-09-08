import {
  BASE,
  identityFrom,
  isPseudo,
  PACKAGES,
  pseudo,
  PSEUDO_CLOSE,
  PSEUDO_OPEN,
  type RendererBridge,
  type Wording,
} from '@rk/core'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { App } from './App'
import { WordingProvider } from './wording'

/**
 * RG51: the test the design rests on.
 *
 * The screen is rendered under a locale nobody speaks, in which every catalogue value is
 * wrapped in brackets. Anything visible without them is a string somebody typed into a
 * component — which this sees on the run after they type it, rather than on the day a
 * second locale is added and every screen has to be reopened.
 */
const BUILT = identityFrom({ version: '0.0.0', commit: 'abc1234', signed: 'unsigned' })

function withBridge(bridge: RendererBridge): void {
  Object.defineProperty(window, 'roadkeep', { value: bridge, configurable: true })
}

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

function drawIn(over: Wording | undefined) {
  return render(
    <WordingProvider over={over}>
      <App />
    </WordingProvider>,
  )
}

/**
 * Every piece of text the rendered screen actually shows, deduplicated.
 *
 * Read off the leaf elements rather than off `textContent` at the root, which would join
 * a wrapped string to an unwrapped one and hide exactly what this is looking for.
 */
function visibleText(root: HTMLElement): string[] {
  const seen = new Set<string>()
  for (const node of root.querySelectorAll('*')) {
    if (node.children.length > 0) continue
    const text = node.textContent?.trim() ?? ''
    if (text !== '') seen.add(text)
  }
  return [...seen]
}

/** The only text on this screen that is a name and not a sentence. */
const IDENTIFIERS = new Set<string>(PACKAGES)

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
