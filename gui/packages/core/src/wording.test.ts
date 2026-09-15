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
  type MessageKey,
  pseudo,
  reasonOf,
  refusalOf,
  saidPlainly,
  stale,
  timeIn,
  translator,
  UNREADABLE_TEXT,
  untranslated,
  WITHHELD_TEXT,
  type Wording,
  type Withholding,
} from './wording'
import { LOCALE_TAGS, wordingFor } from './locales'
import type { Unreadable } from './limits'

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
  const half: Wording = { 'portfolio.footnote': 'A janela abre.' }

  it('uses what it has', () => {
    expect(translator(half)('portfolio.footnote')).toBe('A janela abre.')
  })

  it('falls back per key, not per file', () => {
    // The point of the whole design: one translated string does not have to wait for the
    // rest, and one missing string does not show an identifier.
    expect(translator(half)('transport.absent')).toBe(BASE['transport.absent'])
  })

  it('says what is left to translate, in the base own order', () => {
    const left = untranslated(half)

    expect(left).not.toContain('portfolio.footnote')
    expect(left).toEqual(keys().filter((key) => key !== 'portfolio.footnote'))
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
    const say = translator({ ...pseudo(), 'portfolio.footnote': '⟦{count} read⟧' })

    expect(say('portfolio.footnote', { count: 2 })).toBe('⟦2 read⟧')
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

describe('RG168: why a project could not be read, in the window’s language', () => {
  /** An unreadable as the client builds one, with the code and the holes it carries. */
  const unreadable = (over: Partial<Unreadable> = {}): Unreadable => ({
    reason: 'unreadable-payload',
    message: 'the answer: expected a number, found null',
    code: 'shape',
    fields: { path: 'the answer', expected: 'a number', got: 'null' },
    elapsedMs: 0,
    argv: [],
    said: '',
    ...over,
  })

  it('says the catalogue sentence for the code, with the holes the fields fill', () => {
    const say = translator()

    expect(reasonOf(unreadable(), say)).toBe(
      fill(BASE['unreadable.shape'], { path: 'the answer', expected: 'a number', got: 'null' }),
    )
  })

  it('says it in the window’s language, which is the whole point of a code', () => {
    // The pseudo-locale stands for any second language: what matters is that the sentence
    // came out of the catalogue and not out of `message`.
    const say = translator(pseudo())

    expect(isPseudo(reasonOf(unreadable(), say))).toBe(true)
  })

  it('draws the engine’s own prose untranslated, which is what an empty code means', () => {
    const said = unreadable({ code: '', fields: {}, message: 'roadkeep: unknown key `x`' })

    expect(reasonOf(said, translator(pseudo()))).toBe('roadkeep: unknown key `x`')
  })

  it('has a sentence for every code, so a code added without one does not compile', () => {
    const say = translator()

    for (const key of Object.values(UNREADABLE_TEXT)) expect(say(key)).not.toBe('')
  })
})

describe('RG192: why a request did not run, in the window’s language', () => {
  /** A refusal as the carrier builds one, with the code and the hole it carries. */
  const withheld = (over: Partial<Withholding> = {}): Withholding => ({
    message: 'D:/x is not a project the scan of the person’s roots found',
    code: 'not-catalogued',
    fields: { root: 'D:/x' },
    ...over,
  })

  it('says the catalogue sentence for the code, with the holes the fields fill', () => {
    const say = translator()

    expect(refusalOf(withheld(), say)).toBe(fill(BASE['withheld.not-catalogued'], { root: 'D:/x' }))
  })

  it('says it in the window’s language, which is the whole point of a code', () => {
    const say = translator(pseudo())

    expect(isPseudo(refusalOf(withheld(), say))).toBe(true)
  })

  it('draws an untranslated sentence as written, which is what an empty code means', () => {
    // Two things arrive as the empty code and neither is looked up: a transport's own prose,
    // and this app's report of a command line it composed wrongly. This is the second.
    const said = withheld({ code: '', fields: {}, message: '`--nope` is not an option' })

    expect(refusalOf(said, translator(pseudo()))).toBe('`--nope` is not an option')
  })

  it('has a sentence for every code, so a code added without one does not compile', () => {
    const say = translator()

    for (const key of Object.values(WITHHELD_TEXT)) expect(say(key)).not.toBe('')
  })

  it('takes a sentence that is already what a person reads', () => {
    expect(refusalOf(saidPlainly('roadkeep: no'), translator(pseudo()))).toBe('roadkeep: no')
  })
})

describe('RG177: a time in the window’s language', () => {
  const STAMP = '2026-09-11T15:04:05.000Z'

  it('writes the same instant differently in two languages, which is the whole point', () => {
    // Not compared to a spelled-out string: what the runtime writes for a tag is the
    // runtime's, and a test that pinned it would be this file deciding a format.
    expect(timeIn(STAMP, 'pt-BR')).not.toBe(timeIn(STAMP, 'en-US'))
  })

  it('writes it in the tag it was given, and not in the desktop’s', () => {
    const said = timeIn(STAMP, 'pt-BR')

    expect(said).toBe(new Date(STAMP).toLocaleString('pt-BR'))
  })

  it('falls back to the desktop where no tag was named', () => {
    expect(timeIn(STAMP, '')).toBe(new Date(STAMP).toLocaleString())
  })

  it('answers a stamp it cannot read as it arrived, since a blank is worse', () => {
    expect(timeIn('whenever', 'pt-BR')).toBe('whenever')
    expect(timeIn('', 'pt-BR')).toBe('')
  })

  it('answers rather than throwing for a tag the runtime will not take', () => {
    // A tag this build does not ship is not worth failing a screen over: the time is the
    // point, and the desktop's own format will do.
    expect(timeIn(STAMP, 'not a tag')).toBe(new Date(STAMP).toLocaleString())
  })
})

/**
 * RG216: a count of one written as a plural.
 *
 * `portfolio.title` was `{count} projects on this machine` and nothing else, so a machine with
 * one project read *1 projetos* — and the English was as wrong. What replaced it is the
 * language's own rule: a key may carry a sibling named for a CLDR category, and the sentence
 * itself stays the `other` form.
 */

/** The forms a key may carry beside itself, which a walk must not read as a sentence of its own. */
const FORM = /\.(zero|one|two|few|many)$/

/**
 * The counted sentences that read right at one, and so carry no singular.
 *
 * Three shapes, and the list is short on purpose: a label drawn beside its own number, where
 * the count is the whole of what is said; `{count} of {total}`, where the noun agrees with the
 * total and never with the count; and a gerund, which inflects in neither language this build
 * ships — *1 ainda lendo* and *1 esperando* are as right as at fifty.
 */
const READS_AT_ONE: readonly MessageKey[] = [
  'portfolio.filter.all',
  'portfolio.filter.drifted',
  'portfolio.filter.disagrees',
  'portfolio.filter.unreadable',
  'task.unblocks',
  'counts.pending',
  'counts.waiting',
  'counts.requirement',
]

const counted = () => keys().filter((key) => !FORM.test(key) && BASE[key].includes('{count}'))

describe('RG216: every counted sentence has the forms its languages need', () => {
  it('reads counted sentences at all, so what follows is about something', () => {
    expect(counted().length).toBeGreaterThan(10)
  })

  it('gives each one a singular, or names it as one that already reads right', () => {
    // The guard the mechanism rests on: a counted key added without a singular fails here,
    // on the run after it is written, rather than on a screen showing *1 projetos*.
    const missing = counted().filter(
      (key) => !READS_AT_ONE.includes(key) && !(`${key}.one` in BASE),
    )

    expect(missing).toEqual([])
  })

  it('writes no form beside a sentence that counts nothing', () => {
    // The other direction. A `.one` whose own sentence lost its `{count}` is a form no rule
    // can ever choose, and it would sit in the catalogue translated and unread.
    const orphans = keys()
      .filter((key) => FORM.test(key))
      .filter((key) => {
        const plural = key.replace(FORM, '')
        return !(plural in BASE) || !BASE[plural as MessageKey].includes('{count}')
      })

    expect(orphans).toEqual([])
  })

  it('keeps every sentence in the list a counted one, so the list cannot outlive its reason', () => {
    expect(READS_AT_ONE.filter((key) => !BASE[key].includes('{count}'))).toEqual([])
  })
})

describe('RG216: which form a count chooses', () => {
  const say = translator()

  it('says the singular at one and the plural at every other number', () => {
    expect(say('portfolio.title', { count: 1 })).toBe('1 project on this machine')
    expect(say('portfolio.title', { count: 3 })).toBe('3 projects on this machine')
    expect(say('portfolio.title', { count: 0 })).toBe('0 projects on this machine')
  })

  it('reads a count that arrived as a string, which is what a narrowed listing carries', () => {
    // `Narrowed.fields` are strings by the time a screen has them, and a sentence that lost
    // its singular for crossing that seam is the defect this exists to remove.
    const narrowed = say('backlog.refused', { count: '1', file: 'docs/ROADMAP.md' })

    expect(narrowed).toContain('1 line in docs/ROADMAP.md carries')
    expect(say('backlog.refused', { count: '4', file: 'docs/ROADMAP.md' })).toContain('4 lines')
  })

  it('asks the locale and not the base, so a language with one form gets one sentence', () => {
    // Japanese has `other` and nothing else, which is what proves the rule comes from the tag
    // rather than from a count compared against one somewhere in here.
    expect(translator({}, 'ja')('portfolio.title', { count: 1 })).toBe('1 projects on this machine')
  })

  it('leaves a key with no form of its own as it was written', () => {
    expect(say('portfolio.filter.all', { count: 1 })).toBe('All 1')
  })

  it('leaves a sentence that counts nothing alone', () => {
    expect(say('portfolio.title.unknown')).toBe(BASE['portfolio.title.unknown'])
    expect(say('portfolio.title')).toBe(BASE['portfolio.title'])
  })

  it('falls back per form, the way the catalogue falls back per key', () => {
    // A translation that wrote the singular and not the plural reads in both: the form is
    // settled first, and what is missing is then one key falling through to English.
    const half: Wording = { 'portfolio.title.one': '{count} projeto nesta máquina' }
    const partly = translator(half, 'pt-BR')

    expect(partly('portfolio.title', { count: 1 })).toBe('1 projeto nesta máquina')
    expect(partly('portfolio.title', { count: 2 })).toBe('2 projects on this machine')
  })

  it('answers rather than throwing for a tag the runtime will not take', () => {
    expect(translator({}, 'not a tag')('portfolio.title', { count: 1 })).toBe(
      '1 project on this machine',
    )
  })
})

/**
 * RG216: the other shape, where several counts shared one sentence.
 *
 * `{read} read · {pending} still reading · {unreadable} unreadable` was one key with three
 * numbers in it, so at one project it read *1 lidos*: a plural rule chooses one form for a
 * sentence, and no form can agree with three numbers. Those rows are keys of their own now,
 * joined by `counted`, and every number a word agrees with is named `count`.
 *
 * What keeps that true is the walk below, over both catalogues: a hole followed by a word is
 * a number something may agree with, and each is `count`, text, or a figure nothing agrees
 * with. A name in none of those fails — so a hole added to a sentence is classified when it
 * is written, which is the only moment anybody knows what goes in it.
 */

/** A hole with a word after it, which is where agreement happens. */
const AGREES = /\{(\w+)\}\s+\p{Ll}/gu

/** Holes carrying text: a path, a name, an id, a version. No number, so nothing to agree with. */
const TEXT: readonly string[] = ['block', 'by', 'file', 'found', 'id', 'path', 'version']

/**
 * Numbers no word agrees with.
 *
 * Mostly the `{x} of {y}` shape, where the noun belongs to the total and the figure before it
 * is just a figure — `3 of 40 backlogs searched`, `12 of 250 words`. `characters` is one
 * judgement rather than a shape: its sentence already agrees with the count of lines it could
 * not list, and a read one character long is not a state this app has. `bytes` and `ceiling`
 * are the other (RG245): both are said only of a file past a mebibyte, so neither is ever one.
 */
const FIGURES: readonly string[] = [
  'bytes',
  'ceiling',
  'characters',
  'done',
  'left',
  'limit',
  'max',
  'of',
  'over',
  'prose',
  'room',
  'searched',
  'structure',
  'taken',
  'total',
]

/** What a sentence puts a word next to without saying which of the three it is. */
function unclassified(value: string): string[] {
  return [...value.matchAll(AGREES)]
    .map((found) => found[1] ?? '')
    .filter((name) => name !== 'count' && !TEXT.includes(name) && !FIGURES.includes(name))
}

describe('RG216: a sentence agrees with one number, and it is named count', () => {
  it('reads holes with a word after them at all, so what follows is about something', () => {
    const found = keys().flatMap((key) => [...BASE[key].matchAll(AGREES)])

    expect(found.length).toBeGreaterThan(20)
  })

  it.each([...LOCALE_TAGS])('classifies every one of them: %s', (tag) => {
    // Both catalogues, because a sentence that agrees in English may not in Portuguese —
    // `{count} more not listed` against `mais {count} não listados` — and the reverse is
    // what a translation of a row nobody split would look like.
    const said = wordingFor(tag)
    const loose = keys().flatMap((key) =>
      unclassified(said[key] ?? BASE[key]).map((name) => `${key}: {${name}}`),
    )

    expect(loose).toEqual([])
  })

  it('finds a row that shared one sentence between several counts', () => {
    // The guard on the guard: the sentence as it was written before this, which is what a
    // clean answer above has to be able to fail on.
    expect(unclassified('{read} read · {pending} still reading · {unreadable} unreadable')).toEqual(
      ['read', 'pending', 'unreadable'],
    )
    expect(unclassified('{count} lines in {file} carry a marker')).toEqual([])
  })

  it('leaves every classified name one a sentence still uses', () => {
    // Neither list outlives its reason: a name nothing spells any more is a line to delete.
    const spelled = new Set(
      keys().flatMap((key) => [...BASE[key].matchAll(AGREES)].map((f) => f[1])),
    )
    const gone = [...TEXT, ...FIGURES].filter((name) => !spelled.has(name))

    expect(gone).toEqual([])
  })
})
