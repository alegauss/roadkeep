import { describe, expect, it } from 'vitest'

import {
  addRoot,
  checkRoot,
  coveredBy,
  DEFAULT_DEPTH,
  DEPTH_CEILING,
  NO_DEFAULT_ROOTS,
  removeRoot,
  walkable,
  withPresence,
  type ScanRoot,
} from './roots'

/** A stand-in for a platform that does not care about case, which is most of them here. */
const keyOf = (path: string) => path.replaceAll('\\', '/').toLowerCase()

const root = (path: string, depth = DEFAULT_DEPTH): ScanRoot => ({ path, depth })

describe('RG10: nothing is looked at until somebody says so', () => {
  it('starts with no roots at all', () => {
    // The list is the person's statement. An app that scanned a drive on first launch
    // would be reading somebody's whole disk to draw a list nobody asked for.
    expect(NO_DEFAULT_ROOTS).toEqual([])
  })

  it('invents nothing from a home directory', () => {
    expect(NO_DEFAULT_ROOTS.some((entry) => entry.path.includes('~'))).toBe(false)
    expect(NO_DEFAULT_ROOTS).toHaveLength(0)
  })
})

describe('RG10: what counts as a root', () => {
  it('takes a folder and a depth', () => {
    const checked = checkRoot('/home/a/code', 3)
    expect(checked).toEqual({ ok: true, value: { path: '/home/a/code', depth: 3 } })
  })

  it('defaults the depth rather than leaving it unset', () => {
    expect(checkRoot('/home/a/code')).toMatchObject({ ok: true, value: { depth: DEFAULT_DEPTH } })
  })

  it('refuses a blank folder, with a reason', () => {
    const checked = checkRoot('   ', 2)
    expect(checked.ok).toBe(false)
    if (checked.ok) return
    expect(checked.problem).toBe('empty')
    expect(checked.message).toContain('blank')
  })

  it('trims what somebody pasted', () => {
    expect(checkRoot('  /home/a/code  ')).toMatchObject({
      ok: true,
      value: { path: '/home/a/code' },
    })
  })

  it('allows a depth of zero, which is the folder itself', () => {
    expect(checkRoot('/home/a/one-repo', 0).ok).toBe(true)
  })

  it('refuses a depth past the ceiling, because that is a disk read and not a scan', () => {
    const checked = checkRoot('/home/a', DEPTH_CEILING + 1)
    expect(checked.ok).toBe(false)
    if (checked.ok) return
    expect(checked.problem).toBe('depth-out-of-range')
  })

  it.each([1.5, Number.NaN, Number.POSITIVE_INFINITY])('refuses a depth of %s', (depth) => {
    expect(checkRoot('/home/a', depth).ok).toBe(false)
  })
})

describe('RG10: keeping the list', () => {
  it('appends a new root at the end, keeping the order the person chose', () => {
    const roots = addRoot(addRoot([], root('/a'), keyOf), root('/b'), keyOf)
    expect(roots.map((entry) => entry.path)).toEqual(['/a', '/b'])
  })

  it('changes the depth of a root already named instead of adding it twice', () => {
    const roots = addRoot([root('/a', 2), root('/b', 2)], root('/a', 4), keyOf)

    expect(roots).toHaveLength(2)
    expect(roots[0]).toEqual({ path: '/a', depth: 4 })
    // And it stays where it was: the order is the person's.
    expect(roots[1]?.path).toBe('/b')
  })

  it('treats one folder spelled two ways as one root', () => {
    const roots = addRoot([root('D:\\Git')], root('d:/git', 3), keyOf)
    expect(roots).toHaveLength(1)
  })

  it('removes by the same rule it adds by', () => {
    expect(removeRoot([root('D:\\Git'), root('/b')], 'd:/git', keyOf).map((r) => r.path)).toEqual([
      '/b',
    ])
  })
})

describe('RG10: a root that is not there', () => {
  it('is kept and marked, never dropped', () => {
    // A disconnected drive is not a project somebody deleted, and forgetting it makes the
    // person retype a setting for a reason that was never theirs.
    const marked = withPresence(
      [root('/here'), root('/on-a-usb-stick')],
      (path) => path === '/here',
    )

    expect(marked).toHaveLength(2)
    expect(marked[1]).toMatchObject({ path: '/on-a-usb-stick', presence: 'missing' })
  })

  it('is left out of a walk without being left out of the list', () => {
    const marked = withPresence([root('/here'), root('/gone')], (path) => path === '/here')

    expect(walkable(marked).map((entry) => entry.path)).toEqual(['/here'])
    expect(marked).toHaveLength(2)
  })
})

describe('RG10: one root inside another', () => {
  const contains = (outer: ScanRoot, inner: string) =>
    inner.startsWith(`${outer.path}/`) &&
    inner.slice(outer.path.length + 1).split('/').length <= outer.depth

  it('is reported rather than refused', () => {
    // Sometimes it is exactly what somebody means: a shallow sweep of the code folder and
    // a deeper one of the monorepo inside it. This app cannot tell which, so it says so.
    const covering = coveredBy([root('/code', 3)], root('/code/mono/app'), contains)
    expect(covering?.path).toBe('/code')
  })

  it('says nothing when the depth does not reach', () => {
    expect(coveredBy([root('/code', 1)], root('/code/a/b/c'), contains)).toBeNull()
  })

  it('does not report a root as covering itself', () => {
    expect(coveredBy([root('/code', 3)], root('/code'), contains)).toBeNull()
  })
})
