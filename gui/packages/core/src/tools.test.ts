import { describe, expect, it } from 'vitest'

import { buildArgv, buildCall } from './client'
import { argumentName, argumentsFor, callFor, toolFor } from './tools'
import { VERB_WORDS, VERBS, type VerbName } from './verbs'

/**
 * RG101: the same call, spelled for the engine's other surface.
 *
 * What is held is that the two spellings come off one table. A verb named one way on a
 * command line and another way as a tool would be a transport that reads a different verb
 * from the one the caller asked for, and nothing above the transport could see it.
 */

describe('RG101: which tool a verb is', () => {
  it('joins the words the command line separates', () => {
    expect(toolFor('sectionAdd', { sectionAdd: ['section', 'add'] })).toBe('section_add')
  })

  it('takes a hyphen inside a word to an underscore too', () => {
    expect(toolFor('nonGoalList', VERB_WORDS)).toBe('non_goal_list')
    expect(toolFor('criterionList', VERB_WORDS)).toBe('criterion_list')
  })

  it('leaves a one-word verb as it is', () => {
    expect(toolFor('list', VERB_WORDS)).toBe('list')
    expect(toolFor('brief', VERB_WORDS)).toBe('brief')
  })

  it('names a tool for every verb the read table has', () => {
    // The table is what a caller reaches, so a verb with no tool would be a read that
    // works over one transport and not the other for a reason nobody wrote down.
    for (const verb of Object.keys(VERBS) as VerbName[]) {
      expect(toolFor(verb, VERB_WORDS)).toMatch(/^[a-z][\da-z_]*$/)
    }
  })
})

describe('RG101: what a tool call carries', () => {
  it('spells a field the way a schema publishes it', () => {
    expect(argumentName('noBody')).toBe('no_body')
    expect(argumentName('supersededDesign')).toBe('superseded_design')
    expect(argumentName('id')).toBe('id')
  })

  it('leaves out what nobody set, rather than sending it as nothing', () => {
    // Almost every field is optional, and a key present with no value is a different thing
    // from an absent one to a validator.
    expect(argumentsFor({ id: 'RG1', noBody: undefined })).toEqual({ id: 'RG1' })
  })

  it('keeps a value that is false or empty, which somebody did set', () => {
    expect(argumentsFor({ noBody: false, block: '' })).toEqual({ no_body: false, block: '' })
  })

  it('answers nothing for an input that is not an object', () => {
    expect(argumentsFor(undefined)).toEqual({})
    expect(argumentsFor(null)).toEqual({})
  })

  it('composes the tool and its arguments together', () => {
    expect(callFor('show', { id: 'RG1', noBody: true }, VERB_WORDS)).toEqual({
      tool: 'show',
      arguments: { id: 'RG1', no_body: true },
    })
  })
})

describe('RG101: the two spellings are of one call', () => {
  it('sends the id as an argument where the argv sends it as a word', () => {
    expect(buildArgv('/w', 'show', { id: 'RG1' })).toEqual(['-C', '/w', 'show', 'RG1', '--json'])
    expect(buildCall('show', { id: 'RG1' })).toEqual({ tool: 'show', arguments: { id: 'RG1' } })
  })

  it('spells a two-word verb as words on one side and one name on the other', () => {
    expect(buildArgv('/w', 'nonGoalList', {})).toEqual(['-C', '/w', 'non-goal', 'list', '--json'])
    expect(buildCall('nonGoalList', {}).tool).toBe('non_goal_list')
  })

  // That every one of these tools is a tool the engine actually publishes is
  // `mcp-live.test.ts`: it asks the server, which is the only thing that can say.
})
