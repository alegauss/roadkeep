import { describe, expect, it } from 'vitest'

import {
  CHOSEN_RULE,
  chosenFindings,
  findingsIn,
  judgeChosen,
  outlivedFindings,
  unexcusedFindings,
  type AcceptedFinding,
} from './accessibility'

/**
 * RG211: what a scan of a rendered surface found, and what fails the run.
 */

/** An axe result's shape, as `AxeBuilder.analyze` answers it, trimmed to what is read. */
const RESULT = {
  violations: [
    {
      id: 'color-contrast',
      impact: 'serious',
      help: 'Elements must meet minimum color contrast ratio thresholds',
      nodes: [{ target: ['.muted'] }, { target: ['#root', '.hint'] }],
    },
    {
      id: 'region',
      impact: 'moderate',
      help: 'All page content should be in landmarks',
      nodes: [{ target: ['main'] }],
    },
  ],
  incomplete: [{ id: 'color-contrast', impact: 'serious', nodes: [{ target: ['.unsure'] }] }],
}

describe('RG211: reading a scan', () => {
  it('names one finding per element a violation is on, and none for what axe could not decide', () => {
    const found = findingsIn(RESULT, 'settings', 'dark')

    expect(found.map((one) => [one.rule, one.target])).toEqual([
      ['color-contrast', '.muted'],
      ['color-contrast', '#root .hint'],
      ['region', 'main'],
    ])
    expect(found.every((one) => one.surface === 'settings' && one.ground === 'dark')).toBe(true)
  })

  it('reads nothing out of an answer that is not a result, rather than throwing', () => {
    expect(findingsIn(null, 'home', 'light')).toEqual([])
    expect(findingsIn({ violations: 'no' }, 'home', 'light')).toEqual([])
  })
})

describe('RG211: what fails the run', () => {
  const found = findingsIn(RESULT, 'settings', 'dark')
  const accepted: AcceptedFinding = {
    rule: 'color-contrast',
    target: '.muted',
    why: 'filed as a line of its own',
    established: '2026-09-12',
  }

  it('fails on a serious finding nobody excused, and not on a moderate one', () => {
    expect(unexcusedFindings(found, []).map((one) => one.target)).toEqual(['.muted', '#root .hint'])
  })

  it('lets through a finding whose rule and element were written down', () => {
    expect(unexcusedFindings(found, [accepted]).map((one) => one.target)).toEqual(['#root .hint'])
  })

  it('fails on an exception no scan names, which is a list that stopped being true', () => {
    expect(outlivedFindings(found, [accepted])).toEqual([])
    expect(outlivedFindings([], [accepted])).toEqual([accepted])
  })
})

describe('RG211: a chosen option, told apart from its sibling', () => {
  // RG207's toggle as the dark ground painted it: the accent on the panel.
  const DARK = { chosen: [51, 51, 51] as const, sibling: [33, 33, 33] as const }

  it('fails a chosen state told by a shade alone', () => {
    const verdict = judgeChosen({
      target: 'radio "Dark"',
      ...DARK,
      chosenMarks: 0,
      siblingMarks: 0,
    })

    expect(verdict.readable).toBe(false)
    expect(verdict.ratio).toBeCloseTo(1.27, 2)
    expect(chosenFindings([verdict], 'settings', 'dark')).toEqual([
      expect.objectContaining({ rule: CHOSEN_RULE, impact: 'serious', target: 'radio "Dark"' }),
    ])
  })

  it('passes the same shade once the chosen option carries a mark its sibling lacks', () => {
    // What RG207 did: a check drawn inside the chosen option.
    const verdict = judgeChosen({
      target: 'radio "Dark"',
      ...DARK,
      chosenMarks: 1,
      siblingMarks: 0,
    })

    expect(verdict.readable).toBe(true)
    expect(chosenFindings([verdict], 'settings', 'dark')).toEqual([])
  })

  it('passes a chosen state three to one apart in background, with no mark at all', () => {
    const verdict = judgeChosen({
      target: 'button "All"',
      chosen: [0, 0, 0],
      sibling: [128, 128, 128],
      chosenMarks: 0,
      siblingMarks: 0,
    })

    expect(verdict.readable).toBe(true)
  })
})
