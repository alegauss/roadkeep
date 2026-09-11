import { describe, expect, it } from 'vitest'

import { designFrom, whereDesignLives } from './design'
import { readBriefPayload, readShowPayload, type BriefPayload, type ShowPayload } from './payloads'

/** Captured from a real `brief --json`, trimmed to the keys the shape declares. */
const BODY =
  'The body arrives as one string, already wrapped to the column the project declared, and\n' +
  'it is shown as those bytes: a preformatted block, never reflowed and never parsed.\n' +
  '\n' +
  '- a list item the file wrote, and **bold** nothing here turns into markup\n'

const SECTION = {
  anchor: 'RG24',
  title: 'Prose shown as the file keeps it',
  level: 3,
  file: 'docs/IMPROVEMENTS.md',
  first: 240,
  last: 247,
  words: 235,
  own_words: 235,
  body: BODY,
}

const BUDGET = {
  section: {
    anchor: 'RG24',
    role: 'improvements',
    written: true,
    unit: 'words',
    limit: 250,
    allowed: 250,
    aim: 233,
    taken: 235,
    left: 15,
    over: 0,
  },
}

const RAW = {
  id: 'RG24',
  status: '🛠',
  block: 'D',
  symptom: 'the rationale section is not shown',
  why: 'The section is the half a reviewer needs before agreeing the line is right.',
  deps: ['RG23 ✅'],
  requires: [],
  ref: 'RG24',
  section: SECTION,
  section_absence: '',
  readiness: 'ready',
  picked: null,
  deps_resolved: [{ dep: 'RG23', kind: 'task', status: 'shipped', detail: 'in the changelog' }],
  unblocks: { count: 0, of: 49, transitive: [], transitive_elided: 0 },
  non_goals: ['No Markdown parsed in this app'],
  non_goals_elided: 0,
  done_when: ['The prose is shown as the file stores it'],
  done_when_elided: 0,
  held: [],
  landed: [],
  budget: BUDGET,
}

function brief(over: Record<string, unknown> = {}): BriefPayload {
  const parsed = readBriefPayload({ ...RAW, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

/** `show` carries the same section and prices nothing, which is the other caller. */
function show(over: Record<string, unknown> = {}): ShowPayload {
  const parsed = readShowPayload(
    {
      id: 'RG24',
      status: '🛠',
      block: 'D',
      shipped: false,
      file: 'docs/ROADMAP.md',
      line: 28,
      rendered: '- 🛠 **RG24** …',
      symptom: 'the rationale section is not shown',
      why: 'The section is the half a reviewer needs.',
      deps: ['RG23 ✅'],
      requires: [],
      ref: 'RG24',
      section: SECTION,
      section_absence: '',
      ...over,
    },
    '',
  )
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG24: the prose is shown as the file stores it', () => {
  it('passes the body through byte for byte', () => {
    // Not parsed, not reflowed, not trimmed. What the gate measured is what a reviewer
    // reads and what a commit will diff.
    expect(designFrom(brief()).prose).toBe(BODY)
  })

  it('breaks it where the file breaks it, and joining puts it back', () => {
    const design = designFrom(brief())

    expect(design.lines).toHaveLength(5)
    expect(design.lines[2]).toBe('')
    expect(design.lines.join('\n')).toBe(BODY)
  })

  it('reads a carriage return and its newline as the one break they are', () => {
    // A Windows checkout otherwise leaves a stray `\r` dangling off every line.
    const design = designFrom(brief({ section: { ...SECTION, body: 'one\r\ntwo\r\nthree' } }))

    expect(design.lines).toEqual(['one', 'two', 'three'])
  })

  it('keeps a trailing blank line, because the file has one', () => {
    const design = designFrom(brief({ section: { ...SECTION, body: 'a paragraph.\n' } }))

    expect(design.lines).toEqual(['a paragraph.', ''])
  })

  it('turns no markup into markup', () => {
    // `No Markdown parsed in this app`: a renderer that read `**` would be a second
    // reading of a format this app has no business knowing.
    const body = 'A `code span`, some **bold** and | a | table |'
    const design = designFrom(brief({ section: { ...SECTION, body } }))

    expect(design.prose).toBe(body)
    expect(design.lines).toEqual([body])
  })

  it('carries the heading and the address in the engine words', () => {
    const design = designFrom(brief())

    expect(design.title).toBe('Prose shown as the file keeps it')
    expect(design.anchor).toBe('RG24')
    expect(whereDesignLives(design)).toBe('docs/IMPROVEMENTS.md:240-247')
  })

  it('names a single-line section without a range nobody can read', () => {
    const design = designFrom(brief({ section: { ...SECTION, first: 12, last: 12 } }))

    expect(whereDesignLives(design)).toBe('docs/IMPROVEMENTS.md:12')
  })
})

describe('RG24: three states, not two', () => {
  it('shows the prose when the prose is there', () => {
    expect(designFrom(brief()).state).toBe('shown')
  })

  it('withholds rather than empties when the body was not asked for', () => {
    // `show --no-body` keeps the address and drops the text. Drawing that as an empty
    // design reports a defect that is not there.
    const design = designFrom(show({ section: { ...SECTION, body: null } }))

    expect(design.state).toBe('withheld')
    expect(design.prose).toBeNull()
    expect(design.lines).toEqual([])
    expect(whereDesignLives(design)).toBe('docs/IMPROVEMENTS.md:240-247')
  })

  it('keeps a section that exists and says nothing distinguishable from one withheld', () => {
    // An empty body is a defect and a withheld one is not, so the two must not collapse.
    const design = designFrom(brief({ section: { ...SECTION, body: '' } }))

    expect(design.state).toBe('shown')
    expect(design.prose).toBe('')
  })

  it('is absent for a pointer that resolves to nothing, in the engine sentence', () => {
    const design = designFrom(
      brief({
        section: null,
        section_absence: 'deleted on ship, which is where the rationale ends',
        budget: null,
      }),
    )

    expect(design.state).toBe('absent')
    expect(design.prose).toBeNull()
    expect(design.absence).toBe('deleted on ship, which is where the rationale ends')
    expect(whereDesignLives(design)).toBe('')
  })
})

describe('RG24: the count and the limit, beside the prose', () => {
  it('carries both off the budget the same read carried', () => {
    // 250 is `[limits] section` in this project's own config. A copy of it in here would
    // be the literal `No rule compiled into the client` refuses. The sentence that said it
    // in English went with RG172; what is left is the engine's numbers, which a screen fills
    // into a catalogue key.
    const design = designFrom(brief())

    expect(design.budget?.taken).toBe(235)
    expect(design.budget?.limit).toBe(250)
    expect(design.budget?.unit).toBe('words')
    expect(design.budget?.over).toBe(0)
  })

  it('carries how far past the limit the engine put it', () => {
    const design = designFrom(
      brief({ budget: { section: { ...BUDGET.section, taken: 268, left: 0, over: 18 } } }),
    )

    expect(design.budget?.over).toBe(18)
  })
})
