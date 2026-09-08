import { describe, expect, it } from 'vitest'

import {
  BASE,
  BASE_LOCALE,
  EN,
  fill,
  isPseudo,
  keys,
  localeFor,
  pseudo,
  stale,
  translator,
  untranslated,
  type Wording,
} from './wording'

describe('RG51: the base is the type', () => {
  it('answers every key it declares', () => {
    const say = translator()

    for (const key of keys()) expect(say(key)).not.toBe('')
  })

  it('has no key whose value is the key, which is what an identifier on screen looks like', () => {
    for (const key of keys()) expect(BASE[key]).not.toBe(key)
  })

  it('is the same object the type is taken from', () => {
    expect(BASE).toBe(EN)
  })
})

describe('RG51: a translation that is not finished', () => {
  const half: Wording = { 'app.tagline': 'A janela abre.' }

  it('uses what it has', () => {
    expect(translator(half)('app.tagline')).toBe('A janela abre.')
  })

  it('falls back per key, not per file', () => {
    // The point of the whole design: one translated string does not have to wait for the
    // rest, and one missing string does not show an identifier.
    expect(translator(half)('transport.ipc')).toBe(BASE['transport.ipc'])
  })

  it('says what is left to translate, in the base own order', () => {
    const left = untranslated(half)

    expect(left).not.toContain('app.tagline')
    expect(left).toEqual(keys().filter((key) => key !== 'app.tagline'))
  })

  it('says nothing is left for a complete one', () => {
    expect(untranslated(pseudo())).toEqual([])
  })

  it('names a string that outlived its screen', () => {
    const old = { 'screen.deleted': 'gone' } as unknown as Wording

    expect(stale(old)).toEqual(['screen.deleted'])
    expect(stale(pseudo())).toEqual([])
  })
})

describe('RG51: holes are filled by name', () => {
  it('fills the ones it was given', () => {
    expect(fill('{count} of {total}', { count: 3, total: 9 })).toBe('3 of 9')
  })

  it('leaves a hole nobody filled visible, because a gap is what nobody reports', () => {
    expect(fill('{count} of {total}', { count: 3 })).toBe('3 of {total}')
  })

  it('does not care what order the holes are in, which is what a translation changes', () => {
    const values = { count: 3, total: 9 }

    expect(fill('{total} has {count}', values)).toBe('9 has 3')
    expect(fill('{count} of {total}', values)).toBe('3 of 9')
  })

  it('ignores a value nobody asked for', () => {
    expect(fill('nothing here', { count: 3 })).toBe('nothing here')
  })
})

describe('RG51: which locale answers', () => {
  const available = ['en', 'pt-BR']

  it('takes the exact tag when there is one', () => {
    expect(localeFor('pt-BR', available)).toBe('pt-BR')
  })

  it('matches case-insensitively, because a settings file is typed by hand', () => {
    expect(localeFor('PT-br', available)).toBe('pt-BR')
  })

  it('falls back from a region to its language', () => {
    expect(localeFor('pt-PT', available)).toBe('pt-BR')
    expect(localeFor('pt', available)).toBe('pt-BR')
  })

  it('falls back to the base for a language nobody wrote', () => {
    expect(localeFor('ja', available)).toBe(BASE_LOCALE)
  })

  it('reads an empty request as the desktop deciding, not as an error', () => {
    expect(localeFor('', available)).toBe(BASE_LOCALE)
    expect(localeFor('   ', available)).toBe(BASE_LOCALE)
  })
})

describe('RG51: the locale nobody speaks', () => {
  it('covers every key, so an unwrapped string on screen is a literal', () => {
    const say = translator(pseudo())

    for (const key of keys()) expect(isPseudo(say(key))).toBe(true)
  })

  it('keeps the holes, so a filled string is still filled', () => {
    const say = translator({ ...pseudo(), 'app.tagline': '⟦{count} read⟧' })

    expect(say('app.tagline', { count: 2 })).toBe('⟦2 read⟧')
  })

  it('is not mistaken for a real string', () => {
    expect(isPseudo(BASE['app.name'])).toBe(false)
  })
})
