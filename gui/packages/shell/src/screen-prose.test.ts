import { describe, expect, it } from 'vitest'

import { isDrawn, NOT_FOR_SCREEN, oneLine, replacementFrom, reportOf, wordAt } from './screen-prose'

/**
 * RG191: the half of the gate that reads no types.
 *
 * What a tag means, what a report says and which files are a screen — all decidable from
 * text, and all asserted here in milliseconds. The other half needs a checker and a program,
 * which starts something, so it is `screen-prose-live.test.ts` and costs what that costs.
 */

describe('RG191: what the tag says to draw instead', () => {
  it('answers nothing for a field carrying no tag at all', () => {
    expect(replacementFrom([])).toBeNull()
    expect(replacementFrom([{ name: 'param', text: 'a the first number' }])).toBeNull()
  })

  it('answers the tag text, which is what the failure tells the reader to use', () => {
    const tags = [{ name: NOT_FOR_SCREEN, text: '`code`, looked up with `say`' }]

    expect(replacementFrom(tags)).toBe('`code`, looked up with `say`')
  })

  it('still answers where the tag names nothing, rather than reading as untagged', () => {
    // A field saying *not this* without saying what is a docstring worth fixing, and
    // swallowing it would turn the gate off for that field without anybody deciding to.
    expect(replacementFrom([{ name: NOT_FOR_SCREEN }])).toContain(NOT_FOR_SCREEN)
    expect(replacementFrom([{ name: NOT_FOR_SCREEN, text: '   ' }])).toContain(NOT_FOR_SCREEN)
  })

  it('reads a tag the author wrapped as the one line a report prints', () => {
    const tags = [{ name: NOT_FOR_SCREEN, text: '`code`, looked up\nin the catalogue\nwith `say`' }]

    expect(replacementFrom(tags)).toBe('`code`, looked up in the catalogue with `say`')
  })
})

describe('RG191: which files are a screen', () => {
  it('reads the renderer, where a person sees the output', () => {
    expect(isDrawn('D:/repo/packages/ui/src/Task.tsx')).toBe(true)
    expect(isDrawn('/home/x/repo/packages/ui/src/useGate.ts')).toBe(true)
  })

  it('leaves the other two packages alone, neither of them drawing anything', () => {
    // `core` reads these fields on purpose — `reasonOf` is the lookup itself — and the
    // shell writes them to a log. Only a screen has a language to say them in.
    expect(isDrawn('/repo/packages/core/src/wording.ts')).toBe(false)
    expect(isDrawn('/repo/packages/shell/src/carrier.ts')).toBe(false)
  })

  it('leaves a test alone, which asserts prose rather than showing it to anybody', () => {
    expect(isDrawn('/repo/packages/ui/src/task.test.tsx')).toBe(false)
    expect(isDrawn('/repo/packages/ui/src/reaching.test.ts')).toBe(false)
  })
})

describe('RG191: the report', () => {
  const found = {
    file: 'packages/ui/src/useGate.ts',
    line: 114,
    column: 41,
    read: 'answered.message',
    instead: '`code`, looked up with `say`',
  }

  it('says nothing at all where nothing draws prose', () => {
    expect(reportOf([])).toBe('')
  })

  it('names the place, what is read and what to read instead', () => {
    const report = reportOf([found])

    expect(report).toContain('packages/ui/src/useGate.ts:114:41')
    expect(report).toContain('answered.message')
    // The whole point of carrying the tag's text: a gate that says only *no* costs the
    // reader the search the gate has already done.
    expect(report).toContain('`code`, looked up with `say`')
    expect(report).toContain('RG191')
  })

  it('counts, so a reader knows whether the list is the whole of it', () => {
    expect(reportOf([found])).toContain('1 place draws')
    expect(reportOf([found, { ...found, line: 220 }])).toContain('2 places draw')
  })
})

describe('RG191: reading a position off the source', () => {
  it('starts at the word and not at the whitespace a node begins with', () => {
    // A node begins where the one before it ended, so `pos` is the gap between them: `b`
    // here starts at 6, and the position the AST carries for it is 3.
    expect(wordAt('a +   b', 3)).toBe(6)
  })

  it('leaves a position already on a word where it is', () => {
    expect(wordAt('unreadable.message', 0)).toBe(0)
  })

  it('stops at the end rather than running past it', () => {
    expect(wordAt('x   ', 1)).toBe(4)
  })

  it('folds every kind of space, a docstring wrapping with newlines', () => {
    expect(oneLine('  a\n b\t c ')).toBe('a b c')
  })
})
