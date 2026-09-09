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
    if (unreadable.includes(directory)) return Promise.resolve(null)
    if (!directories.has(directory)) return Promise.resolve(null)

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

    return Promise.resolve({
      isProject,
      children: [...children].map(([name, path]) => ({ name, path })),
    } satisfies Listing)
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

  it('does not find a decoy inside an ignored directory', async () => {
    // The symptom, exactly: a `roadkeep.toml` shipped inside a dependency is not a project
    // on this machine, and walking in to find out costs a hundred thousand folders.
    const { look } = tree([
      '/code/app/roadkeep.toml',
      '/code/app/node_modules/some-pkg/roadkeep.toml',
      '/code/app/.git/modules/x/roadkeep.toml',
    ])

    const result = await scan([at('/code', 4)], look, keyOf)

    expect(result.found.map((entry) => entry.path)).toEqual(['/code/app'])
  })

  it('takes a different ignore list when a machine needs one', async () => {
    // Configuration, not constants. `vendor` is a dependency folder in one language and a
    // perfectly ordinary directory in another.
    const { look } = tree(['/code/vendor/app/roadkeep.toml'])
    const policy = { ...DEFAULT_POLICY, ignore: [] }

    expect((await scan([at('/code', 3)], look, keyOf, { policy })).found).toHaveLength(1)
    expect((await scan([at('/code', 3)], look, keyOf)).found).toHaveLength(0)
  })

  it('looks for the marker the policy names and no other file', async () => {
    const policy = { ...DEFAULT_POLICY, marker: 'something-else.toml' }
    const holding = tree(['/code/app/something-else.toml'], [], policy.marker)
    const notHolding = tree(['/code/app/roadkeep.toml'], [], policy.marker)

    expect((await scan([at('/code', 3)], holding.look, keyOf, { policy })).found).toHaveLength(1)
    expect((await scan([at('/code', 3)], notHolding.look, keyOf, { policy })).found).toHaveLength(0)
  })
})

describe('RG11: how far it goes', () => {
  it('stops at the declared depth', async () => {
    const { look } = tree(['/code/org/repo/deep/roadkeep.toml'])

    expect((await scan([at('/code', 2)], look, keyOf)).found).toHaveLength(0)
    expect((await scan([at('/code', 3)], look, keyOf)).found).toHaveLength(1)
  })

  it('finds a project at the root itself, with a depth of zero', async () => {
    const { look } = tree(['/code/roadkeep.toml'])

    expect((await scan([at('/code', 0)], look, keyOf)).found.map((f) => f.path)).toEqual(['/code'])
  })

  it('does not descend into a project it has found', async () => {
    // A governed repository does not contain another. Descending is how every package in
    // a monorepo becomes a candidate.
    const { look, looked } = tree([
      '/code/app/roadkeep.toml',
      '/code/app/packages/inner/roadkeep.toml',
    ])

    const result = await scan([at('/code', 5)], look, keyOf)

    expect(result.found.map((entry) => entry.path)).toEqual(['/code/app'])
    expect(looked()).not.toContain('/code/app/packages')
  })

  it('looks at only as many directories as the bounds allow', async () => {
    const paths = ['/code/app/roadkeep.toml']
    for (let index = 0; index < 500; index += 1) {
      paths.push(`/code/app/node_modules/pkg${String(index)}/index.js`)
    }
    const { look, looked } = tree(paths)

    const result = await scan([at('/code', 4)], look, keyOf)

    // Two directories read to find one project, out of five hundred and two.
    expect(result.looked).toBe(2)
    expect(looked()).toEqual(['/code', '/code/app'])
  })
})

describe('RG11: what it reports', () => {
  it('says which root each project came from and how far down', async () => {
    const { look } = tree(['/code/org/repo/roadkeep.toml'])

    expect((await scan([at('/code', 3)], look, keyOf)).found[0]).toEqual({
      path: '/code/org/repo',
      root: '/code',
      depth: 2,
    })
  })

  it('finds the shallow ones first', async () => {
    const { look } = tree(['/code/deep/down/here/roadkeep.toml', '/code/near/roadkeep.toml'])

    expect((await scan([at('/code', 4)], look, keyOf)).found.map((f) => f.path)).toEqual([
      '/code/near',
      '/code/deep/down/here',
    ])
  })

  it('reports a directory it could not read instead of abandoning the scan', async () => {
    const { look } = tree(['/code/open/roadkeep.toml', '/code/locked/x'], ['/code/locked'])

    const result = await scan([at('/code', 3)], look, keyOf)

    expect(result.found.map((f) => f.path)).toEqual(['/code/open'])
    expect(result.unreadable).toEqual(['/code/locked'])
  })

  it('reports a project once when two roots both reach it', async () => {
    const { look } = tree(['/code/org/repo/roadkeep.toml'])

    const result = await scan([at('/code', 3), at('/code/org', 2)], look, keyOf)

    expect(result.found).toHaveLength(1)
  })

  it('finds nothing under a root that is not there, without failing', async () => {
    const { look } = tree(['/code/app/roadkeep.toml'])

    const result = await scan([at('/not-here', 2)], look, keyOf)

    expect(result.found).toEqual([])
    expect(result.unreadable).toEqual(['/not-here'])
  })
})

describe('RG71: a walk that does not hold the process still', () => {
  /**
   * A tree whose directories answer after a number of turns rather than at once.
   *
   * Turns rather than milliseconds because this package has no timer — no Node and no DOM
   * (RG1). What is being asserted does not need one: a read that has started and not
   * answered is a read in flight, and yielding is what lets the next one start.
   */
  function slow(paths: readonly string[], turns: Readonly<Record<string, number>> = {}) {
    const { look: inner } = tree(paths)
    let running = 0
    let most = 0

    const look: Look = async (directory) => {
      running += 1
      most = Math.max(most, running)
      for (let turn = 0; turn < (turns[directory] ?? 1); turn += 1) await Promise.resolve()
      running -= 1
      return inner(directory)
    }

    return { look, most: () => most }
  }

  const LEVEL = [
    '/code/a/roadkeep.toml',
    '/code/b/roadkeep.toml',
    '/code/c/roadkeep.toml',
    '/code/d/roadkeep.toml',
  ]

  it('reads the directories of one level together', async () => {
    const { look, most } = slow(LEVEL)

    await scan([at('/code', 2)], look, keyOf)

    // Four siblings, four reads in flight. One at a time is what the synchronous walk did,
    // and it is what makes one slow share the whole scan's problem.
    expect(most()).toBe(4)
  })

  it('never opens more directories at once than the width allows', async () => {
    const { look, most } = slow(LEVEL)

    await scan([at('/code', 2)], look, keyOf, { width: 2 })

    expect(most()).toBe(2)
  })

  it('finds them in the order the level lists them, not the order they answered', async () => {
    // `d` answers first and `a` last. A walk that appended as answers arrived would report
    // them backwards, and a scan of one machine twice would be two different lists.
    const { look } = slow(LEVEL, { '/code/a': 8, '/code/b': 6, '/code/c': 4, '/code/d': 2 })

    const result = await scan([at('/code', 2)], look, keyOf)

    expect(result.found.map((entry) => entry.path)).toEqual([
      '/code/a',
      '/code/b',
      '/code/c',
      '/code/d',
    ])
  })

  it('still counts every directory it looked at', async () => {
    // The number the bounds exist to hold down, and the first thing that would quietly
    // stop being true once the counting moved off the path each read takes.
    const { look } = slow(LEVEL)

    const result = await scan([at('/code', 2)], look, keyOf)

    expect(result.looked).toBe(5)
  })
})
