import { describe, expect, it } from 'vitest'

import { compareVersions, readLatestRelease, saidOfUpdate, verdictOf } from './updates'

const PAGE = 'https://github.com/alegauss/roadkeep-gui/releases/tag/v0.2.0'

describe('RG50: which build is newer', () => {
  it.each([
    ['0.1.0', '0.2.0', -1],
    ['0.2.0', '0.1.0', 1],
    ['v1.0.0', '1.0.0', 0],
    ['0.10.0', '0.9.9', 1],
  ])('orders %s against %s', (a, b, sign) => {
    expect(Math.sign(compareVersions(a, b) ?? Number.NaN)).toBe(sign)
  })

  it('refuses to guess between two things that are not versions', () => {
    // `0.10.0` sorts below `0.9.9` as a string, which is exactly the answer a guess gives.
    expect(compareVersions('unstamped', '0.1.0')).toBeNull()
    expect(compareVersions('0.1.0', 'nightly')).toBeNull()
  })
})

describe('RG50: what the newest release means for the build that asked', () => {
  it('names both versions and the page, where a newer one is published', () => {
    expect(verdictOf('0.1.0', { tag: 'v0.2.0', url: PAGE })).toEqual({
      kind: 'newer',
      current: '0.1.0',
      latest: '0.2.0',
      url: PAGE,
    })
  })

  it('is current for the same build, and for a developer build ahead of every release', () => {
    expect(verdictOf('0.2.0', { tag: 'v0.2.0', url: PAGE }).kind).toBe('current')
    expect(verdictOf('0.3.0', { tag: 'v0.2.0', url: PAGE }).kind).toBe('current')
  })

  it('says which side is not a version, rather than which is newer', () => {
    const unstamped = verdictOf('unstamped', { tag: 'v0.2.0', url: PAGE })

    expect(unstamped.kind).toBe('failed')
    if (unstamped.kind !== 'failed') throw new Error('unreachable')
    expect(unstamped.reason).toContain('unstamped')
  })

  it('offers a page only where there is something newer to go and get', () => {
    expect(saidOfUpdate(verdictOf('0.1.0', { tag: 'v0.2.0', url: PAGE })).opens).toBe(PAGE)
    expect(saidOfUpdate({ kind: 'current', current: '0.2.0', latest: '0.2.0' }).opens).toBeNull()
    expect(saidOfUpdate({ kind: 'none', current: '0.1.0' }).opens).toBeNull()
    expect(saidOfUpdate({ kind: 'failed', current: '0.1.0', reason: 'offline' }).key).toBe(
      'update.failed',
    )
  })
})

describe('RG50: the answer GitHub gives', () => {
  it('reads the tag and the page out of a release, and nothing else', () => {
    const read = readLatestRelease(
      { tag_name: 'v0.2.0', html_url: PAGE, draft: false, assets: [], body: 'notes' },
      '',
    )

    expect(read.ok).toBe(true)
    if (!read.ok) throw new Error('unreachable')
    expect(read.value).toEqual({ tag: 'v0.2.0', url: PAGE })
  })
})
