import { BASE, PT_BR, translator } from '@rk/core'
import { vigDesignSystemTranslations } from '@viglet/viglet-design-system'
import { render, screen } from '@testing-library/react'
import i18next, { changeLanguage, t } from 'i18next'
import { act } from 'react'
import { afterEach, describe, expect, it } from 'vitest'

import { Portfolio } from './Portfolio'
import { spokenLocale, startSpeaking } from './speaking'
import { WordingProvider } from './wording'

/**
 * RG88: one locale, read by both translation systems.
 *
 * The screen mixes this app's components with the design system's, and the package
 * translates its own with i18next. What is held here is that the two cannot disagree: the
 * tag the shell resolved goes to i18next, and this app's catalogue reads it back from
 * there rather than keeping a second copy.
 *
 * The package's own strings are read off `vigDesignSystemTranslations` rather than typed
 * in, so a release that rewords one does not fail a test about locales.
 */
const inPtBr = translator(PT_BR)

/** A wording a test forces, hoisted so the provider is not handed a new object per render. */
const FORCED = { 'portfolio.footnote': 'forced' } as const

/** What the package says for one of its own keys, in one of its own languages. */
function packageSays(language: 'en' | 'pt', key: string): string {
  const bundle = vigDesignSystemTranslations[language] as Record<string, unknown>
  const nav = (bundle['bento'] as { nav?: Record<string, string> } | undefined)?.nav
  return nav?.[key] ?? ''
}

afterEach(async () => {
  // i18next is a singleton, so a tag left behind is the next file's starting state.
  if (i18next.isInitialized) await changeLanguage('en')
})

describe('RG88: which system decides the language', () => {
  it('speaks the tag the shell resolved, not the one a browser detector guessed', async () => {
    await startSpeaking('pt-BR')

    expect(spokenLocale()).toBe('pt-BR')
  })

  it('says nothing is speaking before anything started it', () => {
    // A plain render in a test has no entry point, and the catalogue has to be legible in
    // that state rather than reading `undefined` as a tag.
    expect(typeof spokenLocale()).toBe('string')
  })

  it('reaches the package with the tag, resolving the region to the language it ships', async () => {
    // The catalogue ships `pt-BR` and the package ships `pt`. One tag has to satisfy both,
    // and this is the assertion that says it does.
    await startSpeaking('pt-BR')

    expect(t('bento.nav.label')).toBe(packageSays('pt', 'label'))
    expect(packageSays('pt', 'label')).not.toBe(packageSays('en', 'label'))
  })
})

describe('RG88: the catalogue takes its tag from i18next', () => {
  it('draws this app`s own strings in the language i18next is speaking', async () => {
    await startSpeaking('pt-BR')

    render(
      <WordingProvider>
        <Portfolio />
      </WordingProvider>,
    )

    expect(screen.getByText(inPtBr('portfolio.footnote'))).toBeTruthy()
  })

  it('follows a later change, so one switch moves both systems', async () => {
    // The whole point. A tag read once at mount would leave the package's components
    // translated and this app's frozen at whatever it was handed.
    await startSpeaking('pt-BR')
    render(
      <WordingProvider>
        <Portfolio />
      </WordingProvider>,
    )
    expect(screen.getByText(inPtBr('portfolio.footnote'))).toBeTruthy()

    await act(async () => {
      await changeLanguage('en')
    })

    expect(screen.getByText(BASE['portfolio.footnote'])).toBeTruthy()
    expect(t('bento.nav.label')).toBe(packageSays('en', 'label'))
  })

  it('still lets a test force a wording, which is the pseudo-locale run`s door', async () => {
    await startSpeaking('pt-BR')

    render(
      <WordingProvider over={FORCED}>
        <Portfolio />
      </WordingProvider>,
    )

    expect(screen.getByText('forced')).toBeTruthy()
  })
})
