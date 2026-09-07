import { describe, expect, it } from 'vitest'

import { groupProjects, isFamily, type ProjectSite } from './families'

const keyOf = (path: string) => path.replaceAll('\\', '/').toLowerCase()

/** The real arrangement: two versions as worktrees, and a junction onto the newer one. */
const TURING_MAIN = '/git/viglet/turing/2026.3'
const TURING_OLD = '/git/viglet/turing/2026.2'
const TURING_LATEST = '/git/viglet/turing/latest'
const TURING_GIT = '/git/viglet/turing/2026.3/.git'

const site = (path: string, realPath: string, commonDir: string | null): ProjectSite => ({
  path,
  realPath,
  commonDir,
})

describe('RG12: a link is not a second project', () => {
  it('collapses a junction and its target into one member', () => {
    const families = groupProjects(
      [
        site(TURING_MAIN, TURING_MAIN, TURING_GIT),
        site(TURING_LATEST, TURING_MAIN, TURING_GIT),
      ],
      keyOf,
    )

    expect(families).toHaveLength(1)
    expect(families[0]?.members).toHaveLength(1)
  })

  it('keeps the folder as the path and the link as an alias', () => {
    // A family should read by version. `latest` is a name that moves; `2026.3` is what it
    // currently means, and it is the one somebody is going to recognise next month.
    const families = groupProjects(
      [
        site(TURING_LATEST, TURING_MAIN, TURING_GIT),
        site(TURING_MAIN, TURING_MAIN, TURING_GIT),
      ],
      keyOf,
    )

    expect(families[0]?.members[0]?.path).toBe(TURING_MAIN)
    expect(families[0]?.members[0]?.aliases).toEqual([TURING_LATEST])
  })

  it('keeps the link as the path when the folder itself was never scanned', () => {
    // Naming only the junction as a root is a reasonable thing to do, and answering with
    // no project at all would be worse than answering with the name that was given.
    const families = groupProjects([site(TURING_LATEST, TURING_MAIN, TURING_GIT)], keyOf)

    expect(families[0]?.members[0]?.path).toBe(TURING_LATEST)
    expect(families[0]?.members[0]?.aliases).toEqual([])
  })

  it('sees one folder spelled two ways as one', () => {
    const families = groupProjects(
      [site('D:\\Git\\app', 'D:\\Git\\app', null), site('d:/git/app', 'D:\\Git\\app', null)],
      keyOf,
    )

    expect(families[0]?.members).toHaveLength(1)
  })
})

describe('RG12: a worktree is a second project in the same family', () => {
  it('keeps two versions apart and groups them', () => {
    const families = groupProjects(
      [site(TURING_MAIN, TURING_MAIN, TURING_GIT), site(TURING_OLD, TURING_OLD, TURING_GIT)],
      keyOf,
    )

    expect(families).toHaveLength(1)
    expect(isFamily(families[0]!)).toBe(true)
    // Two backlogs, two members. Merging their counts would report a number true of
    // neither version.
    expect(families[0]?.members.map((member) => member.path)).toEqual([TURING_MAIN, TURING_OLD])
  })

  it('handles the whole real arrangement at once', () => {
    const families = groupProjects(
      [
        site(TURING_OLD, TURING_OLD, TURING_GIT),
        site(TURING_MAIN, TURING_MAIN, TURING_GIT),
        site(TURING_LATEST, TURING_MAIN, TURING_GIT),
      ],
      keyOf,
    )

    // Three paths in, one family of two versions out, with the junction as an alias.
    expect(families).toHaveLength(1)
    expect(families[0]?.members).toHaveLength(2)
    expect(families[0]?.members.find((m) => m.path === TURING_MAIN)?.aliases).toEqual([
      TURING_LATEST,
    ])
  })

  it('does not group two repositories that merely sit side by side', () => {
    const families = groupProjects(
      [site('/git/a', '/git/a', '/git/a/.git'), site('/git/b', '/git/b', '/git/b/.git')],
      keyOf,
    )

    expect(families).toHaveLength(2)
    expect(families.every((family) => !isFamily(family))).toBe(true)
  })
})

describe('RG12: a project outside git', () => {
  it('is its own family rather than grouped with every other one', () => {
    // "No common directory" is not something two projects share. Grouping on it would
    // draw a family whose only property is not being a worktree.
    const families = groupProjects(
      [site('/plain/one', '/plain/one', null), site('/plain/two', '/plain/two', null)],
      keyOf,
    )

    expect(families).toHaveLength(2)
    expect(families.every((family) => family.commonDir === null)).toBe(true)
  })

  it('still collapses a link onto it', () => {
    const families = groupProjects(
      [site('/plain/one', '/plain/one', null), site('/plain/alias', '/plain/one', null)],
      keyOf,
    )

    expect(families).toHaveLength(1)
    expect(families[0]?.members[0]?.aliases).toEqual(['/plain/alias'])
  })
})

describe('RG12: the order a list is drawn in', () => {
  it('is the order the scan found things in', () => {
    const families = groupProjects(
      [
        site('/git/z', '/git/z', '/git/z/.git'),
        site('/git/a', '/git/a', '/git/a/.git'),
        site('/git/m', '/git/m', '/git/m/.git'),
      ],
      keyOf,
    )

    // The walk is shallow-first for a reason, and re-sorting here would undo it.
    expect(families.map((family) => family.members[0]?.path)).toEqual(['/git/z', '/git/a', '/git/m'])
  })

  it('answers nothing for nothing', () => {
    expect(groupProjects([], keyOf)).toEqual([])
  })
})
