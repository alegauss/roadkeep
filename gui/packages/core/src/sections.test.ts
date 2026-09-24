import { describe, expect, it } from 'vitest'

import { readSectionWritten, type SectionWritten } from './payloads'
import { saidOfWrite, wasCreated, whereWritten, writtenFrom } from './sections'
import { composeWrite } from './writing'

/** Captured from a real `section add --json`. */
const ADDED = {
  anchor: 'FX1',
  title: 'Why question 1 needs answering',
  level: 3,
  file: 'docs/IMPROVEMENTS.md',
  first: 5,
  last: 8,
  words: 21,
  own_words: 21,
  wrote: ['docs/IMPROVEMENTS.md'],
}

/** Captured from a real `section amend --json`, which adds what it changed. */
const AMENDED = { ...ADDED, words: 20, own_words: 20, changed: ['body'], read_body: false }

function written(raw: Record<string, unknown>): SectionWritten {
  const parsed = readSectionWritten(raw, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG32: writing the design where the pointer points', () => {
  it('composes a section add with the anchor and the heading', () => {
    const composed = composeWrite('/w', 'sectionAdd', {
      anchor: 'RG32',
      title: 'Writing the design where the pointer points',
      body: 'Prose.',
    })

    // Two words, spread from `WRITE_WORDS` and never split out of the key.
    expect(composed.argv).toEqual([
      '-C',
      '/w',
      'section',
      'add',
      'RG32',
      '--title',
      'Writing the design where the pointer points',
      '--body',
      'Prose.',
      '--json',
    ])
  })

  it('names the decisions role, which is the only door to that file', () => {
    const composed = composeWrite('/w', 'sectionAdd', {
      anchor: 'RG32',
      title: 'A constraint',
      body: 'Prose.',
      role: 'decisions',
    })

    expect(composed.argv).toContain('--role')
    expect(composed.argv).toContain('decisions')
  })

  it('reads the prose from a file, so a short field refused costs only itself', () => {
    const composed = composeWrite('/w', 'sectionAdd', {
      anchor: 'RG32',
      title: 'A heading',
      bodyFile: '/tmp/body.md',
    })

    expect(composed.argv).toContain('--body-file')
    expect(composed.argv).not.toContain('--body')
  })
})

describe('RG32: a fragment, and both halves of it', () => {
  it('sends the replacement pair together', () => {
    const composed = composeWrite('/w', 'sectionAmend', {
      anchor: 'RG32',
      fragment: { replace: 'long enough to be prose', replacement: 'written to be read' },
    })

    expect(composed.argv).toEqual([
      '-C',
      '/w',
      'section',
      'amend',
      'RG32',
      '--replace',
      'long enough to be prose',
      '--with',
      'written to be read',
      '--json',
    ])
  })

  it('sends an empty replacement, which is how a fragment is deleted', () => {
    // `optional` would drop this, and dropping it turns a deletion into a malformed call.
    const composed = composeWrite('/w', 'sectionAmend', {
      anchor: 'RG32',
      fragment: { replace: ' and a clause nobody needed', replacement: '' },
    })

    expect(composed.argv).toContain('--with')
    expect(composed.argv[composed.argv.indexOf('--with') + 1]).toBe('')
  })

  it('sends neither half when there is no fragment', () => {
    const composed = composeWrite('/w', 'sectionAmend', { anchor: 'RG32', body: 'All new.' })

    expect(composed.argv).not.toContain('--replace')
    expect(composed.argv).not.toContain('--with')
  })

  it('amends only the heading, leaving the prose bytes alone', () => {
    const composed = composeWrite('/w', 'sectionAmend', { anchor: 'RG32', title: 'A better name' })

    expect(composed.argv).toContain('--title')
    expect(composed.argv).not.toContain('--body')
  })
})

describe('RG32: the answer is the file account, not the draft', () => {
  it('reads where the section landed and what it now counts', () => {
    const one = writtenFrom(written(ADDED))

    expect(one.anchor).toBe('FX1')
    expect(one.words).toBe(21)
    expect(whereWritten(one)).toBe('docs/IMPROVEMENTS.md:5-8')
    expect(wasCreated(one)).toBe(true)
    expect(saidOfWrite(one)).toBe('§FX1 written  docs/IMPROVEMENTS.md:5-8  21 words')
  })

  it('tells a correction from a creation by what the answer says changed', () => {
    const one = writtenFrom(written(AMENDED))

    expect(wasCreated(one)).toBe(false)
    expect(one.changed).toEqual(['body'])
    expect(saidOfWrite(one)).toBe('§FX1 amended (body)  docs/IMPROVEMENTS.md:5-8  20 words')
  })

  it('names both parts an amend touched', () => {
    const one = writtenFrom(written({ ...AMENDED, changed: ['title', 'body'] }))

    expect(saidOfWrite(one)).toContain('amended (title, body)')
  })

  it('names a single-line section without a range nobody can read', () => {
    expect(whereWritten(writtenFrom(written({ ...ADDED, first: 12, last: 12 })))).toBe(
      'docs/IMPROVEMENTS.md:12',
    )
  })

  it('takes the count off the file rather than the prose that was sent', () => {
    // The number that decides whether a design needs splitting has to be the gate's.
    const one = writtenFrom(written({ ...ADDED, words: 249, own_words: 249 }))

    expect(one.words).toBe(249)
    expect(saidOfWrite(one)).toContain('249 words')
  })
})
