import { describe, expect, it } from 'vitest'

import { posturesLost, RENDERER_POSTURE, REQUIRED_POSTURE } from './posture'

describe('RG46: packaging is where the posture stops being configuration', () => {
  it('passes the posture this build actually constructs a window with', () => {
    // Not a copy that agrees today: `RENDERER_POSTURE` is spread into `webPreferences`,
    // so this is the value the window is built with.
    expect(posturesLost({ ...RENDERER_POSTURE })).toEqual([])
  })

  it('names every power a build gained, rather than failing on the first', () => {
    const lost = posturesLost({ ...RENDERER_POSTURE, sandbox: false, nodeIntegration: true })

    expect(lost).toHaveLength(2)
    expect(lost.join(' ')).toContain('sandbox must be true, is false')
    expect(lost.join(' ')).toContain('nodeIntegration must be false, is true')
  })

  it('notices a flag dropped altogether, not only one turned around', () => {
    // A later edit that deletes a line is the case writing the defaults out exists for.
    const { sandbox: _dropped, ...without } = { ...RENDERER_POSTURE }

    expect(posturesLost(without)).toEqual(['sandbox must be true, is undefined'])
  })

  it('requires every flag the window declares, so neither list can quietly shrink', () => {
    expect(Object.keys(REQUIRED_POSTURE).sort()).toEqual(Object.keys(RENDERER_POSTURE).sort())
  })
})
