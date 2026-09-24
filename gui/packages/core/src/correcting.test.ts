import { describe, expect, it } from 'vitest'

import { readCommandsPayload } from './capabilities'
import {
  amended,
  CORRECTIONS,
  correctionsOffered,
  renumbered,
  replacedBy,
  restated,
  wasTypo,
} from './correcting'
import {
  readAmendPayload,
  readRenumberPayload,
  readRestatePayload,
  type AmendPayload,
  type RenumberPayload,
  type RestatePayload,
} from './payloads'
import { composeWrite } from './writing'

/** Captured from a real `amend --json`. */
const AMEND = {
  id: 'FX1',
  file: 'docs/ROADMAP.md',
  line: 5,
  changed: ['why'],
  rendered: '- 📋 **FX1** (deps: —) **nothing answers question 1 yet** — A corrected sentence.',
  was: { why: 'The 1th read has no call path, so the screen has nothing to draw.' },
  refreshed: [],
  wrote: ['docs/ROADMAP.md'],
}

/** Captured from a real `restate --json`. */
const RESTATE = {
  id: 'FX1',
  file: 'docs/ROADMAP.md',
  line: 5,
  was: 'nothing answers question 1 yet',
  now: 'the claim this line made turned out to be false',
  changed: true,
  typo: false,
  premise: {
    design: 'FX1',
    role: 'improvements',
    next: ['amend FX1 --why -', 'section amend FX1 --body -'],
  },
  rendered: '- 📋 **FX1** (deps: —) **the claim this line made turned out to be false** — …',
  refreshed: [],
  wrote: ['docs/ROADMAP.md'],
}

/** Captured from a real `renumber --json`. */
const RENUMBER = {
  id: 'FX1',
  to: 'FX9',
  role: 'roadmap',
  file: 'docs/ROADMAP.md',
  line: 5,
  rendered: '- 📋 **FX9** (deps: —) **the claim this line made turned out to be false** — …',
  section: {
    anchor: 'FX9',
    title: 'Why question 1',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 5,
    last: 8,
    words: 15,
    own_words: 15,
  },
  subsections: [],
  criteria: false,
  moved: [],
  refreshed: [],
  files: ['docs/IMPROVEMENTS.md', 'docs/ROADMAP.md'],
  wrote: ['docs/ROADMAP.md', 'docs/IMPROVEMENTS.md'],
}

function amend(over: Record<string, unknown> = {}): AmendPayload {
  const parsed = readAmendPayload({ ...AMEND, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function restate(over: Record<string, unknown> = {}): RestatePayload {
  const parsed = readRestatePayload({ ...RESTATE, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function renumber(over: Record<string, unknown> = {}): RenumberPayload {
  const parsed = readRenumberPayload({ ...RENUMBER, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

function commands(
  entries: { command: string; help: string; description?: string; runs?: boolean }[],
) {
  const parsed = readCommandsPayload(
    {
      version: '0.2.396',
      source: {},
      commands: entries.map((entry) => ({
        command: entry.command,
        family: 'authoring',
        help: entry.help,
        description: entry.description ?? '',
        writes: true,
        runs: entry.runs ?? true,
        published: true,
        needs: '',
        arguments: [],
      })),
    },
    '',
  )
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG35: the reason each exists, read and not written', () => {
  it('offers the three with the sentence the engine publishes for each', () => {
    // The difference between them is the expensive thing to get wrong, and a sentence
    // composed here would be this app's account of another tool's verb.
    const offered = correctionsOffered(
      commands([
        { command: 'amend', help: "correct one open line's why, deps or pointer" },
        { command: 'restate', help: "correct one open line's symptom, keeping its id" },
        { command: 'renumber', help: 'move one open line to a free id, with its section' },
      ]),
    )

    expect(offered.map((one) => one.verb)).toEqual([...CORRECTIONS])
    expect(offered.every((one) => one.callable)).toBe(true)
    expect(offered[1]?.help).toContain('keeping its id')
  })

  it('withholds one this build does not publish, rather than offering a refusal', () => {
    const offered = correctionsOffered(commands([{ command: 'amend', help: 'correct a why' }]))

    expect(offered[0]?.callable).toBe(true)
    expect(offered[1]?.callable).toBe(false)
    expect(offered[1]?.help).toBe('')
  })

  it('withholds one this build publishes but cannot run', () => {
    const offered = correctionsOffered(
      commands([{ command: 'renumber', help: 'move a line', runs: false }]),
    )

    expect(offered[2]?.callable).toBe(false)
  })

  it('offers them least costly first, which is the order they should be read in', () => {
    expect(CORRECTIONS).toEqual(['amend', 'restate', 'renumber'])
  })
})

describe('RG35: was is two shapes, one verb apart', () => {
  it('reads an amend was as the fields it replaced', () => {
    expect(replacedBy(amend())).toEqual([
      ['why', 'The 1th read has no call path, so the screen has nothing to draw.'],
    ])
  })

  it('reads a restate was as the one symptom, a string', () => {
    expect(restate().was).toBe('nothing answers question 1 yet')
    expect(restate().now).toBe('the claim this line made turned out to be false')
  })

  it('names every field an amend touched, and what each held', () => {
    const two = amend({
      changed: ['why', 'deps'],
      was: { why: 'the old sentence.', deps: 'RG1' },
    })

    expect(replacedBy(two)).toEqual([
      ['why', 'the old sentence.'],
      ['deps', 'RG1'],
    ])
  })

  it('gives an empty string for a changed field the answer did not describe', () => {
    expect(replacedBy(amend({ changed: ['ref'], was: {} }))).toEqual([['ref', '']])
  })
})

describe('RG35: what one correction did', () => {
  it('keeps the id through an amend and a restate, and moves it on a renumber', () => {
    expect(amended(amend()).nowId).toBe('FX1')
    expect(restated(restate()).nowId).toBe('FX1')
    expect(renumbered(renumber()).nowId).toBe('FX9')
  })

  it('names the symptom as what a restate changed', () => {
    expect(restated(restate()).changed).toEqual(['symptom'])
    expect(restated(restate({ changed: false })).changed).toEqual([])
  })

  it('carries what a restate left for a person, without turning it into a form', () => {
    // The why and the design were written from the claim that was replaced, and whether
    // they still hold is a judgement this app does not make.
    expect(restated(restate()).next).toEqual(['amend FX1 --why -', 'section amend FX1 --body -'])
    expect(amended(amend()).next).toEqual([])
  })

  it('says whether it was a slip of the pen or a false premise', () => {
    // A typo leaves the why and the design standing; a false premise leaves both in
    // question, which is why the verb reports which it was.
    expect(wasTypo(restate())).toBe(false)
    expect(wasTypo(restate({ typo: true }))).toBe(true)
  })

  it('counts the lines a renumber rewrote as refreshed', () => {
    const one = renumbered(renumber({ moved: ['FX4', 'FX5'], refreshed: ['FX6'] }))

    expect(one.refreshed).toEqual(['FX4', 'FX5', 'FX6'])
    expect(one.wrote).toContain('docs/IMPROVEMENTS.md')
  })
})

describe('RG35: each is one command', () => {
  it('composes an amend that replaces the whole dep group', () => {
    expect(composeWrite('/w', 'amend', { id: 'RG35', deps: ['RG29', 'RG5'] }).argv).toEqual([
      '-C',
      '/w',
      'amend',
      'RG35',
      '--dep',
      'RG29',
      '--dep',
      'RG5',
      '--json',
    ])
  })

  it('composes an amend that changes one dep and leaves the rest', () => {
    const composed = composeWrite('/w', 'amend', { id: 'RG35', addDep: ['RG9'], dropDep: ['RG2'] })

    expect(composed.argv).toContain('--add-dep')
    expect(composed.argv).toContain('--drop-dep')
    expect(composed.argv).not.toContain('--dep')
  })

  it('composes a restate, which always carries the symptom it is for', () => {
    expect(
      composeWrite('/w', 'restate', { id: 'RG35', symptom: 'the claim was false', typo: true })
        .argv,
    ).toEqual([
      '-C',
      '/w',
      'restate',
      'RG35',
      '--symptom',
      'the claim was false',
      '--typo',
      '--json',
    ])
  })

  it('composes a renumber with a derived target where none is named', () => {
    expect(composeWrite('/w', 'renumber', { id: 'RG35' }).argv).toEqual([
      '-C',
      '/w',
      'renumber',
      'RG35',
      '--json',
    ])
  })
})
