import { describe, expect, it } from 'vitest'

import { identityFrom, saidOfBuild, UNSTAMPED } from './build'

describe('RG46: what a build says about itself', () => {
  it('answers all three questions from what it was stamped with', () => {
    const identity = identityFrom({
      version: '0.3.1',
      commit: '8d2800b',
      signed: 'signed',
      packaged: true,
    })

    expect(saidOfBuild(identity)).toBe('roadkeep-gui 0.3.1 (8d2800b, packaged, signed)')
  })

  it('says an unstamped field rather than leaving a screen to invent one', () => {
    // `npm start` from a working tree is a real way to run this, and it has no commit.
    const identity = identityFrom({ version: '0.0.0' })

    expect(identity.commit).toBe(UNSTAMPED)
    expect(identity.signed).toBe(UNSTAMPED)
    expect(identity.from).toBe('source')
    expect(saidOfBuild(identity)).toBe('roadkeep-gui 0.0.0 (unstamped, source, unstamped)')
  })

  it('reads an empty stamp as unstamped, not as a blank field', () => {
    const identity = identityFrom({ version: '', commit: '', signed: '' })

    expect(identity.version).toBe(UNSTAMPED)
    expect(identity.commit).toBe(UNSTAMPED)
  })

  it('says unsigned truthfully, because that is what the build is', () => {
    // The certificate is RG49's and it is a thing somebody buys. Reporting `unsigned` is
    // honest; leaving the field out would be the app declining to answer.
    const identity = identityFrom({ version: '0.1.0', commit: 'abc1234', signed: 'unsigned' })

    expect(identity.signed).toBe('unsigned')
    expect(saidOfBuild(identity)).toContain('unsigned')
  })

  it('takes only the two words it knows for signing', () => {
    expect(identityFrom({ signed: 'probably' }).signed).toBe(UNSTAMPED)
  })

  it('is one line, short enough to paste into a defect report', () => {
    const said = saidOfBuild(identityFrom({ version: '1.0.0', commit: 'abc1234', packaged: true }))

    expect(said.split('\n')).toHaveLength(1)
    expect(said.length).toBeLessThan(80)
  })
})
