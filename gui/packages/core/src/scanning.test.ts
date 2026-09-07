import { describe, expect, it } from 'vitest'

import type { ScanRoot } from './roots'
import { DEFAULT_POLICY, mayEnter, scan, type Listing, type Look } from './scanning'

/**
 * A tree written as paths. A path ending in the marker is a file; everything else is a
 * directory. Writing the fixture this way keeps the shape of the tree readable, which is
 * the thing each of these tests is actually about.
 */
function tree(
  paths: readonly string[],
  unreadable: readonly string[] = [],
  marker = DEFAULT_POLICY.marker,
) {
  const files = new Set(paths)
  const directories = new Set<string>()
  for (const entry of paths) {
    const parts = entry.split('/')
    for (let end = 1; end < parts.length; end += 1) {
      directories.add(parts.slice(0, end).join('/'))
    }
  }

  const looked: string[] = []
  const look: Look = (directory) => {
    looked.push(directory)
    if (unreadable.includes(directory)) return null
    if (!directories.has(directory)) return null

    const prefix = `${directory}/`
    const children = new Map<string, string>()
    let isProject = false
    for (const entry of [...files, ...directories]) {
      if (!entry.startsWith(prefix)) continue
      const rest = entry.slice(prefix.length)
      const name = rest.split('/')[0] ?? ''
      if (name === '') continue
      if (rest === marker) {
        isProject = true
        continue
      }
      if (directories.has(`${prefix}${name}`)) children.set(name, `${prefix}${name}`)
    }

    return {
      isProject,
      children: [...children].map(([name, path]) => ({ name, path })),
    } satisfies Listing
  }

  return { look, looked: () => looked }
}

const keyOf = (path: string) => path.toLowerCase()
const at = (path: string, depth: number): ScanRoot => ({ path, depth })

describe('RG11: what the walk refuses to enter', () => {
  it.each(['node_modules', '.git', 'dist', 'build', 'target', '__pycache__', '.venv'])(
    'never enters %s',
    (name) => {
      expect(mayEnter(name, DEFAULT_POLICY)).toBe(false)
    },
  )

  it('never enters any hidden directory', () => {
    expect(mayEnter('.cache', DEFAULT_POLICY)).toBe(false)
    expect(mayEnter('.anything-at-all', DEFAULT_POLICY)).toBe(false)
  })

  it('enters an ordinary folder', () => {
    expect(mayEnter('viglet', DEFAULT_POLICY)).toBe(true)
  })

  it('does not find a decoy inside an ignored directory', () => {
    // The symptom, exactly: a `roadkeep.toml` shipped inside a dependency is not a project
    // on this machine, and walking in to find out costs a hundred thousand folders.
    const { look } = tree([
      '/code/app/roadkeep.toml',
      '/code/app/node_modules/some-pkg/roadkeep.toml',
      '/code/app/.git/modules/x/roadkeep.toml',
    ])

    const result = scan([at('/code', 4)], look, keyOf)

    expect(result.found.map((entry) => entry.path)).toEqual(['/code/app'])
  })

  it('takes a different ignore list when a machine needs one', () => {
    // Configuration, not constants. `vendor` is a dependency folder in one language and a
    // perfectly ordinary directory in another.
    const { look } = tree(['/code/vendor/app/roadkeep.toml'])
    const policy = { ...DEFAULT_POLICY, ignore: [] }

    expect(scan([at('/code', 3)], look, keyOf, policy).found).toHaveLength(1)
    expect(scan([at('/code', 3)], look, keyOf).found).toHaveLength(0)
  })

  it('looks for the marker the policy names and no other file', () => {
    const policy = { ...DEFAULT_POLICY, marker: 'something-else.toml' }
    const holding = tree(['/code/app/something-else.toml'], [], policy.marker)
    const notHolding = tree(['/code/app/roadkeep.toml'], [], policy.marker)

    expect(scan([at('/code', 3)], holding.look, keyOf, policy).found).toHaveLength(1)
    expect(scan([at('/code', 3)], notHolding.look, keyOf, policy).found).toHaveLength(0)
  })
})

describe('RG11: how far it goes', () => {
  it('stops at the declared depth', () => {
    const { look } = tree(['/code/org/repo/deep/roadkeep.toml'])

    expect(scan([at('/code', 2)], look, keyOf).found).toHaveLength(0)
    expect(scan([at('/code', 3)], look, keyOf).found).toHaveLength(1)
  })

  it('finds a project at the root itself, with a depth of zero', () => {
    const { look } = tree(['/code/roadkeep.toml'])

    expect(scan([at('/code', 0)], look, keyOf).found.map((f) => f.path)).toEqual(['/code'])
  })

  it('does not descend into a project it has found', () => {
    // A governed repository does not contain another. Descending is how every package in
    // a monorepo becomes a candidate.
    const { look, looked } = tree([
      '/code/app/roadkeep.toml',
      '/code/app/packages/inner/roadkeep.toml',
    ])

    const result = scan([at('/code', 5)], look, keyOf)

    expect(result.found.map((entry) => entry.path)).toEqual(['/code/app'])
    expect(looked()).not.toContain('/code/app/packages')
  })

  it('looks at only as many directories as the bounds allow', () => {
    const paths = ['/code/app/roadkeep.toml']
    for (let index = 0; index < 500; index += 1) {
      paths.push(`/code/app/node_modules/pkg${String(index)}/index.js`)
    }
    const { look, looked } = tree(paths)

    const result = scan([at('/code', 4)], look, keyOf)

    // Two directories read to find one project, out of five hundred and two.
    expect(result.looked).toBe(2)
    expect(looked()).toEqual(['/code', '/code/app'])
  })
})

describe('RG11: what it reports', () => {
  it('says which root each project came from and how far down', () => {
    const { look } = tree(['/code/org/repo/roadkeep.toml'])

    expect(scan([at('/code', 3)], look, keyOf).found[0]).toEqual({
      path: '/code/org/repo',
      root: '/code',
      depth: 2,
    })
  })

  it('finds the shallow ones first', () => {
    const { look } = tree(['/code/deep/down/here/roadkeep.toml', '/code/near/roadkeep.toml'])

    expect(scan([at('/code', 4)], look, keyOf).found.map((f) => f.path)).toEqual([
      '/code/near',
      '/code/deep/down/here',
    ])
  })

  it('reports a directory it could not read instead of abandoning the scan', () => {
    const { look } = tree(['/code/open/roadkeep.toml', '/code/locked/x'], ['/code/locked'])

    const result = scan([at('/code', 3)], look, keyOf)

    expect(result.found.map((f) => f.path)).toEqual(['/code/open'])
    expect(result.unreadable).toEqual(['/code/locked'])
  })

  it('reports a project once when two roots both reach it', () => {
    const { look } = tree(['/code/org/repo/roadkeep.toml'])

    const result = scan([at('/code', 3), at('/code/org', 2)], look, keyOf)

    expect(result.found).toHaveLength(1)
  })

  it('finds nothing under a root that is not there, without failing', () => {
    const { look } = tree(['/code/app/roadkeep.toml'])

    const result = scan([at('/not-here', 2)], look, keyOf)

    expect(result.found).toEqual([])
    expect(result.unreadable).toEqual(['/not-here'])
  })
})
