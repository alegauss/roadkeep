import { describe, expect, it } from 'vitest'

import { blanksIn, doorsIn, filledArgv, isBlank } from './doors'

/**
 * RG165: the doors an answer carried, and the words that go in one.
 *
 * The shapes are the engine's, captured from real answers: a refusal writes `<name>` where a
 * caller has to put something and a gate finding writes `…`, and both arrive as `doors` — at
 * the top of an `explain`, under `remedy` on a finding, beside a refusal.
 */

/** Captured from a real `lint --json` finding. */
const FINDING = {
  clean: false,
  findings: [
    {
      code: 'ref.unresolved',
      file: 'docs/ROADMAP.md',
      remedy: {
        kind: 'compose',
        doors: [
          {
            argv: ['section', 'add', 'RG9', '--title', '…', '--body', '…'],
            what: 'the line points at a section no prose file declares',
            complete: false,
            writes: true,
          },
        ],
      },
    },
  ],
}

/** Captured from a real refusal, which offers a door that runs as it stands. */
const REFUSED = {
  refused: [{ code: 'criterion.absent', field: '', bound: '', message: 'nothing says how much' }],
  said: 'roadkeep: refused',
  doors: [
    { argv: ['criterion', 'add', '--task', 'RG153', '--lead', '<lead>'], complete: false },
    { argv: ['engines'], what: 'four copies of this tool can be in play', complete: true },
  ],
}

describe('RG165: where the engine wrote a blank', () => {
  it('knows the two spellings a blank has, and nothing else', () => {
    expect(isBlank('…')).toBe(true)
    expect(isBlank('<lead>')).toBe(true)
    // An argument the engine chose, which a caller must not be able to replace.
    expect(isBlank('--task')).toBe(false)
    expect(isBlank('RG153')).toBe(false)
    expect(isBlank('<>')).toBe(false)
    expect(isBlank('')).toBe(false)
  })

  it('finds them in the order a caller fills them', () => {
    expect(blanksIn(['section', 'add', 'RG9', '--title', '…', '--body', '…'])).toEqual([4, 6])
    expect(blanksIn(['engines'])).toEqual([])
  })
})

describe('RG165: filling a door', () => {
  const DOOR = ['section', 'add', 'RG9', '--title', '…', '--body', '…']

  it('puts each word where the engine left a blank, and nowhere else', () => {
    expect(filledArgv(DOOR, ['A design', 'The prose.'])).toEqual([
      'section',
      'add',
      'RG9',
      '--title',
      'A design',
      '--body',
      'The prose.',
    ])
  })

  it('refuses the wrong number of words rather than running a placeholder', () => {
    // `<lead>` as a lead is what the engine would file, and a door run short is worse than
    // one not run at all.
    expect(filledArgv(DOOR, ['only one'])).toBeNull()
    expect(filledArgv(DOOR, ['one', 'two', 'three'])).toBeNull()
    expect(filledArgv(DOOR, [])).toBeNull()
  })

  it('refuses an empty word, which would leave an argument nobody offered', () => {
    expect(filledArgv(DOOR, ['A design', ''])).toBeNull()
  })

  it('takes a door that needs nothing, and refuses words for it', () => {
    expect(filledArgv(['engines'], [])).toEqual(['engines'])
    expect(filledArgv(['engines'], ['--json'])).toBeNull()
  })

  it('cannot be used to add a flag, since only the blanks are replaced', () => {
    // The whole of the refusal §RG85 made: a caller supplies prose and never a command line.
    const filled = filledArgv(DOOR, ['--publish', '; rm -rf /'])

    expect(filled).toEqual([
      'section',
      'add',
      'RG9',
      '--title',
      '--publish',
      '--body',
      '; rm -rf /',
    ])
    // Both landed in the slots the engine left, and the verb and its flags are untouched.
    expect(filled?.slice(0, 4)).toEqual(['section', 'add', 'RG9', '--title'])
  })
})

describe('RG165: every door in one answer', () => {
  it('finds the ones under a finding remedy', () => {
    const found = doorsIn(FINDING)

    expect(found).toHaveLength(1)
    expect(found[0]?.argv[0]).toBe('section')
    expect(found[0]?.complete).toBe(false)
  })

  it('finds the ones a refusal carries, in the order the document has them', () => {
    const found = doorsIn(REFUSED)

    expect(found.map((door) => door.argv[0])).toEqual(['criterion', 'engines'])
    expect(found[1]?.complete).toBe(true)
  })

  it('answers nothing for an answer that carries none, which is nearly every answer', () => {
    expect(doorsIn({ file: 'docs/ROADMAP.md', total: 3, tasks: [] })).toEqual([])
    expect(doorsIn(null)).toEqual([])
    expect(doorsIn('a string')).toEqual([])
    expect(doorsIn([])).toEqual([])
  })

  it('skips a door whose shape it cannot read, rather than the whole answer', () => {
    const found = doorsIn({ doors: [{ what: 'no argv here' }, { argv: ['engines'] }] })

    expect(found).toHaveLength(1)
    expect(found[0]?.argv).toEqual(['engines'])
  })
})
