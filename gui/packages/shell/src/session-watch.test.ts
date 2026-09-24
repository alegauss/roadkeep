import { describe, expect, it } from 'vitest'

import { spelledMove } from './session-watch'

/**
 * RG247: how a watcher's answer is spelled before the policy folds it.
 *
 * The half `core` is held not to do (RG65, RG98): a recursive watch answers in the platform's
 * own separator, and one spelling is what a screen reads and what the fold groups on.
 */

describe('RG247: the path a watch answered, as a screen reads one', () => {
  it('turns the platform separator into the one a screen reads', () => {
    expect(spelledMove(String.raw`src\deep\a.ts`)).toBe('src/deep/a.ts')
  })

  it('drops the prefix a watcher may put in front, and keeps a leading dot', () => {
    expect(spelledMove('./src/a.ts')).toBe('src/a.ts')
    expect(spelledMove('.git/index')).toBe('.git/index')
  })

  it('leaves a path that is already spelled that way alone', () => {
    expect(spelledMove('src/a.ts')).toBe('src/a.ts')
    expect(spelledMove('')).toBe('')
  })
})
