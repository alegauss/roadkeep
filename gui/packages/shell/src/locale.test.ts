import { describe, expect, it } from 'vitest'

import { localeChoice } from './locale'

/**
 * RG86: the half of the choice that needs a desktop.
 *
 * `localeFor` is `core`'s and already tested there. What is asserted here is the one thing
 * this package adds: the empty tag `settings.ts` documents as *whatever the desktop says*,
 * which `core` cannot honour because it has no environment to read.
 */
describe('RG86: which locale the window speaks', () => {
  it('takes the tag somebody set', () => {
    expect(localeChoice('pt-BR', 'en-US')).toBe('pt-BR')
  })

  it('follows the desktop when nobody set one', () => {
    expect(localeChoice('', 'pt-BR')).toBe('pt-BR')
  })

  it('reads a blank tag as unset, because a settings file is typed by hand', () => {
    expect(localeChoice('   ', 'pt-BR')).toBe('pt-BR')
  })

  it("falls from the desktop's region to its language", () => {
    expect(localeChoice('', 'pt-PT')).toBe('pt-BR')
  })

  it('falls to the base where the desktop speaks something nobody wrote', () => {
    expect(localeChoice('', 'ja-JP')).toBe('en')
  })

  it('does not let the desktop overrule a tag somebody chose', () => {
    // The case the substitution has to stay out of: choosing English on a Portuguese
    // machine is a choice, not a mistake to correct.
    expect(localeChoice('en', 'pt-BR')).toBe('en')
  })
})
