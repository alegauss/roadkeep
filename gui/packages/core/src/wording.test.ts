import { describe, expect, it } from 'vitest'

import {
  BASE,
  BASE_LOCALE,
  type Bundle,
  bundleGaps,
  bundlePaths,
  bundleSays,
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

describe('RG125: the other half of the wording, compared', () => {
  /** A bundle shaped like the real one: nested, and one language per top-level object. */
  const base: Bundle = {
    language: { toggle: 'Change the language' },
    nav: { backlog: 'Backlog', task: 'Task' },
  }

  it('reads a nested bundle as the paths i18next resolves', () => {
    // Dotted, because that is what a component asks for: `t('nav.backlog')`. A test that
    // compared objects would say a language is missing something without saying what.
    expect(bundlePaths(base)).toEqual(['language.toggle', 'nav.backlog', 'nav.task'])
  })

  it('says nothing for a path that is not there, and nothing for a path that is a branch', () => {
    expect(bundleSays(base, 'nav.backlog')).toBe('Backlog')
    expect(bundleSays(base, 'nav.missing')).toBeUndefined()
    expect(bundleSays(base, 'nav.backlog.deeper')).toBeUndefined()
    // A branch is not a string, and reporting `nav` as translated would hide every leaf
    // under it.
    expect(bundleSays(base, 'nav')).toBeUndefined()
  })

  it('names the path a translation is missing, not the count', () => {
    const gaps = bundleGaps(base, {
      language: { toggle: 'Mudar o idioma' },
      nav: { backlog: 'Backlog' },
    })

    expect(gaps.untranslated).toEqual(['nav.task'])
    expect(gaps.stale).toEqual([])
  })

  it('names a path the base no longer has, which is a string that outlived its screen', () => {
    const gaps = bundleGaps(base, {
      language: { toggle: 'Mudar o idioma' },
      nav: { backlog: 'Backlog', task: 'Tarefa', archive: 'Arquivo' },
    })

    expect(gaps.stale).toEqual(['nav.archive'])
    expect(gaps.untranslated).toEqual([])
  })

  it('names a value identical in both, which is a name or a translation nobody wrote', () => {
    // Reported and not refused, for the reason `app.name` is the catalogue's exception:
    // a name is the same word in either language. Whether one of these is that is a
    // judgement, and this is the list somebody makes it against.
    const gaps = bundleGaps(base, {
      language: { toggle: 'Mudar o idioma' },
      nav: { backlog: 'Backlog', task: 'Tarefa' },
    })

    expect(gaps.identical).toEqual(['nav.backlog'])
  })

  it('holds a bundle against itself as wholly identical and wholly translated', () => {
    // The control: a copy of the base has nothing missing, nothing stale, and every path
    // identical — so a `pt` written by copying `en` reports every line of itself.
    const gaps = bundleGaps(base, base)

    expect(gaps.untranslated).toEqual([])
    expect(gaps.stale).toEqual([])
    expect(gaps.identical).toEqual(bundlePaths(base))
  })
})
