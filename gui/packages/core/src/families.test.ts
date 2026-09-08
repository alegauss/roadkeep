import { describe, expect, it } from 'vitest'

import {
  groupProjects,
  isFamily,
  orderMembers,
  type ProjectMember,
  type ProjectSite,
} from './families'

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
      [site(TURING_MAIN, TURING_MAIN, TURING_GIT), site(TURING_LATEST, TURING_MAIN, TURING_GIT)],
      keyOf,
    )

    expect(families).toHaveLength(1)
    expect(families[0]?.members).toHaveLength(1)
  })

  it('keeps the folder as the path and the link as an alias', () => {
    // A family should read by version. `latest` is a name that moves; `2026.3` is what it
    // currently means, and it is the one somebody is going to recognise next month.
    const families = groupProjects(
      [site(TURING_LATEST, TURING_MAIN, TURING_GIT), site(TURING_MAIN, TURING_MAIN, TURING_GIT)],
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
    expect(families.map((family) => family.members[0]?.path)).toEqual([
      '/git/z',
      '/git/a',
      '/git/m',
    ])
  })

  it('answers nothing for nothing', () => {
    expect(groupProjects([], keyOf)).toEqual([])
  })
})

describe('RG72: which version of a family reads first', () => {
  const member = (path: string, aliases: readonly string[] = []): ProjectMember => ({
    path,
    aliases,
  })

  it('puts the member the stable name points at first', () => {
    // `latest` resolves onto one of them, and collapsing links already worked out which:
    // it is the member carrying the alias. The fact was in hand and was being dropped.
    const ordered = orderMembers([member(TURING_OLD), member(TURING_MAIN, [TURING_LATEST])])

    expect(ordered.map((one) => one.path)).toEqual([TURING_MAIN, TURING_OLD])
  })

  it('keeps that member first however the scan happened to reach them', () => {
    const found = [member(TURING_MAIN, [TURING_LATEST]), member(TURING_OLD)]

    // The symptom: the same machine drew this newest-first or newest-last depending on a
    // directory listing. Both orders in, one order out.
    expect(orderMembers(found).map((one) => one.path)).toEqual(
      orderMembers(found.toReversed()).map((one) => one.path),
    )
  })

  it('reads a run of digits as a number, so 10 is above 2 and not below it', () => {
    // The trap every tool falls into once, and it falls in on the release nobody checks:
    // plain string order puts `2026.10` before `2026.2`.
    const ordered = orderMembers([
      member('/git/viglet/turing/2026.2'),
      member('/git/viglet/turing/2026.10'),
      member('/git/viglet/turing/2026.9'),
    ])

    expect(ordered.map((one) => one.path)).toEqual([
      '/git/viglet/turing/2026.10',
      '/git/viglet/turing/2026.9',
      '/git/viglet/turing/2026.2',
    ])
  })

  it('orders the rest newest first, under the current one', () => {
    const ordered = orderMembers([
      member('/git/viglet/turing/2026.1'),
      member('/git/viglet/turing/2026.3'),
      member('/git/viglet/turing/2026.2', ['/git/viglet/turing/latest']),
    ])

    expect(ordered.map((one) => one.path)).toEqual([
      // The current one, whatever its number.
      '/git/viglet/turing/2026.2',
      '/git/viglet/turing/2026.3',
      '/git/viglet/turing/2026.1',
    ])
  })

  it('still answers an order for folders that are not versions', () => {
    // Stable rather than meaningful, which is the whole claim: what it must never be is
    // whichever the filesystem said first.
    const ordered = orderMembers([member('/repo/feature-x'), member('/repo/main')])

    expect(ordered.map((one) => one.path)).toEqual(['/repo/main', '/repo/feature-x'])
  })

  it('orders the members a grouping produces, not just a list handed to it', () => {
    const families = groupProjects(
      [
        site(TURING_OLD, TURING_OLD, TURING_GIT),
        site(TURING_MAIN, TURING_MAIN, TURING_GIT),
        site(TURING_LATEST, TURING_MAIN, TURING_GIT),
      ],
      keyOf,
    )

    expect(families[0]?.members.map((one) => one.path)).toEqual([TURING_MAIN, TURING_OLD])
  })
})
