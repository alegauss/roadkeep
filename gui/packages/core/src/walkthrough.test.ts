import { describe, expect, it } from 'vitest'

import type { OriginCommit, OriginPayload } from './payloads'
import {
  hasWalkthrough,
  NO_WALKTHROUGH,
  promptForWalkthrough,
  readWalkthrough,
  WALKTHROUGH_SCHEMA,
} from './walkthrough'

/**
 * RG291: the shape a walkthrough comes back in, and the prompt that asks for it.
 *
 * Nothing here runs anything — `walkthrough-live.test.ts` replays two real runs. What is held
 * here is the reading: a step with half a pair is not a step, a missing slot is empty, and the
 * prompt names the commit the run is to read rather than a sentence about it.
 */

const SHIPPED: OriginCommit = {
  sha: '216066b89561b6e9c68f9bab67fe9ffe9ae014a9',
  short: '216066b',
  date: '2026-09-21T15:37:08-03:00',
  author: 'Somebody',
  subject: 'feat(core): ask which entries await a person (RG289)',
  reasoning: 'feat(core): ask which entries await a person (RG289)\n\nThe whole message.',
}

const ORIGIN: OriginPayload = { id: 'RG289', proposedIn: null, shippedIn: SHIPPED }

const SAID = 'Both verbs are in the tables with the shapes a live fixture proved.'

describe('RG291: the prompt a walkthrough is asked with', () => {
  it('names the shipping commit, so the run reads the change and not the sentence', () => {
    const prompt = promptForWalkthrough(ORIGIN, SAID, 'en')

    expect(prompt).toContain(`git show ${SHIPPED.sha}`)
    // The payload goes in whole, as a gloss's brief does: nothing here paraphrases either half,
    // and the whole message rides in the JSON rather than in a sentence composed about it.
    expect(prompt).toContain(JSON.stringify(SHIPPED.reasoning).slice(1, -1))
    expect(prompt).toContain(SHIPPED.subject)
    expect(prompt).toContain(SAID)
    expect(prompt).toContain('en')
  })

  it('asks for nothing to see where no commit shipped it, rather than an empty sha', () => {
    // A line nobody has committed, and a checkout with no history, both arrive here: there is
    // no diff, so there is nothing to read, and `git show ` with a blank after it is the
    // instruction that sends a run looking at the working tree instead.
    const prompt = promptForWalkthrough({ ...ORIGIN, shippedIn: null }, SAID, 'en')

    expect(prompt).not.toContain('git show')
    expect(prompt).toContain('nothingToSee')
  })

  it('writes in the language it is given, which is the window own', () => {
    expect(promptForWalkthrough(ORIGIN, SAID, 'pt-BR')).toContain('pt-BR')
  })
})

describe('RG291: reading what a run answered', () => {
  it('reads the slots it filled, and leaves the rest empty', () => {
    const walkthrough = readWalkthrough({
      before: ['a build of the app', ''],
      steps: [{ does: 'open the task', sees: 'the dialog draws the notice' }],
      where: [{ path: 'packages/ui/src/explain.tsx', said: 'the notice is drawn here' }],
      nothingToSee: '',
    })

    // The empty string in `before` is dropped: a blank line is not a precondition.
    expect(walkthrough.before).toEqual(['a build of the app'])
    expect(walkthrough.steps).toEqual([
      { does: 'open the task', sees: 'the dialog draws the notice' },
    ])
    expect(walkthrough.where[0]?.path).toBe('packages/ui/src/explain.tsx')
    expect(walkthrough.nothingToSee).toBe('')
    expect(hasWalkthrough(walkthrough)).toBe(true)
  })

  it('drops a step missing either half, since one nobody can check is not a step', () => {
    const walkthrough = readWalkthrough({
      steps: [
        { does: 'open the task' },
        { sees: 'something happens' },
        { does: 'press Explain', sees: 'the dialog opens' },
        'not a step at all',
      ],
    })

    expect(walkthrough.steps).toEqual([{ does: 'press Explain', sees: 'the dialog opens' }])
  })

  it('reads a run that found nothing to try, with no steps beside it', () => {
    const walkthrough = readWalkthrough({
      before: [],
      steps: [],
      nothingToSee: 'Two rows in a verb table: nothing is drawn and nobody can open it.',
    })

    expect(walkthrough.steps).toEqual([])
    expect(walkthrough.nothingToSee).not.toBe('')
    // It says something, which is what a screen draws: the verdict it proposes is the answer.
    expect(hasWalkthrough(walkthrough)).toBe(true)
  })

  it('reads nothing at all from an answer that is not one, rather than failing', () => {
    for (const junk of [null, undefined, 'a sentence', 42, []]) {
      expect(readWalkthrough(junk)).toEqual(NO_WALKTHROUGH)
      expect(hasWalkthrough(readWalkthrough(junk))).toBe(false)
    }
  })
})

describe('RG291: the schema that crosses to the other program', () => {
  it('requires the three slots an answer is useless without', () => {
    // `where` is not required: a run that read the diff and named no file still answered the
    // question. The other three are the answer.
    expect(WALKTHROUGH_SCHEMA.required).toEqual(['before', 'steps', 'nothingToSee'])
    expect(WALKTHROUGH_SCHEMA.additionalProperties).toBe(false)
  })

  it('holds a step to both halves, so the shape refuses what the reader would drop', () => {
    expect(WALKTHROUGH_SCHEMA.properties.steps.items.required).toEqual(['does', 'sees'])
  })
})
