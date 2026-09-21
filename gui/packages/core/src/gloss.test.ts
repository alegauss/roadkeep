import { describe, expect, it } from 'vitest'

import CAPTURED from './captured/gloss-answer.json?raw'
import { GLOSS_SCHEMA, hasGloss, NO_GLOSS, promptForGloss, readGloss } from './gloss'
import type { BriefPayload } from './payloads'

/**
 * RG283: a task said in plain words.
 *
 * `captured/gloss-answer.json` is what Claude Code answered for the payload below, kept as it
 * came back. What it proves is that this reader takes the shape a real answer has — every slot
 * filled, the deps keyed by the id the brief carries and the non-goals by their leads — and the
 * rest of the file holds what it does with an answer that is not that.
 */

const BRIEF: BriefPayload = {
  id: 'RG282',
  status: '📋',
  shipped: false,
  block: 'F',
  rendered: '- 📋 **RG282** (deps: RG280) **an edited file opens as it is now** — … → §RG282',
  symptom: 'an edited file opens as it is now, with no view of it against what it was before',
  why: 'The per-call blocks answer what changed one call at a time and miss what a formatter did.',
  deps: ['RG280'],
  requires: [],
  ref: 'RG282',
  section: {
    anchor: 'RG282',
    title: 'The file against its original, line by line',
    body: 'The viewer shows the file as the disk has it, and above it each call’s two halves.',
    level: 3,
    file: 'docs/IMPROVEMENTS.md',
    first: 61,
    last: 86,
    words: 249,
    ownWords: 249,
  },
  sectionAbsence: '',
  readiness: 'ready',
  picked: 'lowest ready id',
  depsResolved: [{ dep: 'RG280', kind: 'task', status: 'shipped', detail: 'in the changelog' }],
  chains: [],
  unblocks: { count: 1, of: 7, direct: ['RG285'], transitive: ['RG285'], transitiveElided: 0 },
  nonGoals: ['No Markdown parsed in this app', 'No write to a governed file'],
  nonGoalsElided: 0,
  quotes: ['No Markdown parsed in this app'],
  doneWhen: ['What the session did to the backlog is visible without leaving the task'],
  doneWhenElided: 0,
  doneWhenOwn: [],
  doneWhenOwnElided: 0,
  doneWhenFolded: {},
  held: [],
  landed: [],
  budget: null,
  claimed: null,
}

const ANSWER: unknown = JSON.parse(CAPTURED)

describe('RG283: the frame a gloss is asked for in', () => {
  it('sends the payload verbatim, as the hand-over does', () => {
    const prompt = promptForGloss(BRIEF, 'en')

    expect(prompt).toContain(JSON.stringify(BRIEF, null, 2))
    expect(prompt).toContain('RG282')
    // Nothing of this app's about the task itself: the payload is the account of it.
    expect(prompt).toContain('Nothing in it was rewritten.')
  })

  it('names the reader, the language and the one rule', () => {
    const prompt = promptForGloss(BRIEF, 'pt-BR')

    expect(prompt).toContain('has never worked on this project')
    expect(prompt).toContain('Write every string in pt-BR.')
    expect(prompt).toContain('Say only what the payload says')
  })

  it('answers against a schema whose slots are the ones a gloss has', () => {
    expect(Object.keys(GLOSS_SCHEMA.properties).sort()).toEqual(Object.keys(NO_GLOSS).sort())
    expect(GLOSS_SCHEMA.additionalProperties).toBe(false)
  })
})

describe('RG283: reading what came back', () => {
  it('reads a captured answer whole, keyed by the ids and leads the brief carries', () => {
    const gloss = readGloss(ANSWER, BRIEF)

    expect(hasGloss(gloss)).toBe(true)
    expect(gloss.headline).not.toBe('')
    expect(gloss.today).not.toBe('')
    expect(gloss.after).not.toBe('')
    expect(gloss.steps.length).toBeGreaterThan(0)
    expect(gloss.done.length).toBeGreaterThan(0)
    expect(Object.keys(gloss.deps)).toEqual(['RG280'])
    expect(Object.keys(gloss.unblocks)).toEqual(['RG285'])
    expect(Object.keys(gloss.binds)).toEqual(BRIEF.nonGoals)
    // A term is a word and what it means here; one missing either half is not a term.
    expect(gloss.terms.every((one) => one.term !== '' && one.said !== '')).toBe(true)
  })

  it('drops an id or a lead the brief does not carry, so no fact on screen is the agent’s', () => {
    const invented = {
      ...(ANSWER as object),
      deps: { RG280: 'the one it waits on', RG999: 'a line nobody filed' },
      unblocks: { RG285: 'the screen that draws it', RG404: 'a line that is not there' },
      binds: { 'No Markdown parsed in this app': 'said as it is', 'No flying cars': 'invented' },
    }
    const gloss = readGloss(invented, BRIEF)

    expect(Object.keys(gloss.deps)).toEqual(['RG280'])
    expect(Object.keys(gloss.unblocks)).toEqual(['RG285'])
    expect(Object.keys(gloss.binds)).toEqual(['No Markdown parsed in this app'])
  })

  it('holds a slot nobody filled as empty rather than refusing the answer', () => {
    const short = { headline: 'One line about it', today: 'What is true now' }
    const gloss = readGloss(short, BRIEF)

    expect(gloss.headline).toBe('One line about it')
    expect(gloss.after).toBe('')
    expect(gloss.steps).toEqual([])
    expect(gloss.terms).toEqual([])
    expect(gloss.deps).toEqual({})
    expect(hasGloss(gloss)).toBe(true)
  })

  it('reads anything that is not an answer as no gloss at all', () => {
    for (const junk of [null, 'a sentence', 42, ['a', 'list'], undefined]) {
      const gloss = readGloss(junk, BRIEF)

      expect(gloss).toEqual(NO_GLOSS)
      expect(hasGloss(gloss)).toBe(false)
    }
  })

  it('keeps only the strings out of a list, and only the terms with both halves', () => {
    const mixed = {
      steps: ['read it', 42, '', { step: 'no' }, 'write it'],
      terms: [{ term: 'hunk', said: 'a run of lines' }, { term: 'hunk' }, { said: 'orphaned' }, 7],
    }
    const gloss = readGloss(mixed, BRIEF)

    expect(gloss.steps).toEqual(['read it', 'write it'])
    expect(gloss.terms).toEqual([{ term: 'hunk', said: 'a run of lines' }])
  })
})
