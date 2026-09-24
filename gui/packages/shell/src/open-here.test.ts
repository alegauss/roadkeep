import { describe, expect, it } from 'vitest'

import { unheldAmong } from './open-here'

/**
 * RG137: the reason a project's engine could not be held, found among what its open built.
 *
 * Resolution builds a transport per candidate, and only the chosen one is read through — so
 * the reason is looked for on all of them rather than on one this file would have to
 * remember. What `open-here-live.test.ts` holds end to end, this holds by the rule.
 */
describe('RG137: the reason, among the transports an open built', () => {
  it('finds it on whichever transport kept it', () => {
    const made = [
      { unheld: new Map<string, string>() },
      { unheld: new Map([['/proj', 'exited with 3']]) },
    ]

    expect(unheldAmong(made, '/proj')).toBe('exited with 3')
  })

  it('answers null for a root nothing refused, and once the open is closed', () => {
    // Closing empties the list the open built, so a closed project has nothing to say.
    expect(unheldAmong([{ unheld: new Map([['/other', 'exited with 3']]) }], '/proj')).toBeNull()
    expect(unheldAmong([], '/proj')).toBeNull()
  })
})
