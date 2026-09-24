import type { KeyOf } from './roots'

/**
 * One backlog reached by several paths, drawn once.
 *
 * Turing and Shio are kept as a git worktree per version under a stable junction, so
 * `2026.2`, `2026.3` and `latest` are three paths over one project family — and drawn flat
 * they are three rows with overlapping counts, one of them pointing at another.
 *
 * Two different things are being collapsed and they need telling apart.
 *
 * **A link is not a second project.** `latest` and `2026.3` are one folder with two names,
 * so they become one member with an alias. Which name is canonical is not a guess: the one
 * that *is* the folder wins, and the link is the alias, so a family reads by version rather
 * than by whichever path the scan happened to reach first.
 *
 * **A worktree is a second project in the same family.** `2026.2` and `2026.3` are two
 * folders with two backlogs that share a git common directory. They stay two members and
 * gain a family, because merging their counts would report a number that is true of
 * neither version.
 *
 * The grouping is read and never guessed — the common directory comes off git's own files,
 * which is also why nothing here runs git.
 *
 * **Inside a family the order is decided, not inherited.** Which version folder a walk
 * reaches first is a fact about a directory listing, so a family drawn in scan order reads
 * newest-first on one machine and newest-last on another. `orderMembers` says why the
 * order it uses is the one it uses.
 */

export interface ProjectSite {
  /** The path the scan found. */
  readonly path: string
  /** The same folder with every link resolved. Two paths sharing this are one folder. */
  readonly realPath: string
  /** Git's common directory for this worktree, or null where this is not a git checkout. */
  readonly commonDir: string | null
  /** Which branch it is on, a short sha where detached, empty where it is not a checkout. */
  readonly branch: string
}

export interface ProjectMember {
  /** The path to work with: the folder itself rather than a name pointing at it. */
  readonly path: string
  /** Other names for the same folder — a junction, a symlink. */
  readonly aliases: readonly string[]
  /**
   * Which branch this member is on (RG199). A family's members share a repository and a
   * declared name, so this is what tells two of them apart.
   */
  readonly branch: string
}

export interface ProjectFamily {
  /** What the members share. Null for a project that belongs to no family. */
  readonly commonDir: string | null
  readonly members: readonly ProjectMember[]
}

/**
 * The order the members of one family read in.
 *
 * **The current version first, and it is not a guess.** A worktree layout keeps a stable
 * name pointing at whichever version is being worked on — `latest` beside `2026.2` and
 * `2026.3` — and collapsing links already worked out which member that name resolves to:
 * it is the one that came out carrying an alias. So the fact is in hand and was being
 * thrown away.
 *
 * **The rest by path, compared with numbers read as numbers, newest first.** Plain string
 * order is the trap every tool falls into once: it puts `2026.10` before `2026.2`, and it
 * does so on the release where somebody stops checking. `Intl.Collator` with `numeric`
 * reads the run of digits as a number, which is what a person means by a version.
 *
 * Modification time was the other candidate and answers a different question — the folder
 * worked on most recently, not the newest version. It is also a `stat` per member, which
 * `core` cannot make and which would put a filesystem read behind drawing a list.
 *
 * The whole path is compared and never a folder name lifted out of it: cutting a path into
 * components is a rule about paths, and this package does not have one (§RG65). Members of
 * a family are siblings, so the shared prefix compares equal and the version decides.
 */
export function orderMembers(members: readonly ProjectMember[]): ProjectMember[] {
  const byVersion = new Intl.Collator('en', { numeric: true })
  return [...members].sort((left, right) => {
    const current = Number(right.aliases.length > 0) - Number(left.aliases.length > 0)
    return current === 0 ? byVersion.compare(right.path, left.path) : current
  })
}

/**
 * Collapse links, then group what is left by the git directory they share.
 *
 * The families are in the order the scan found them: the shallow-first walk is what a
 * person is watching a list build in, and re-sorting *those* would undo it. The members
 * inside one are not — see `orderMembers`.
 */
export function groupProjects(sites: readonly ProjectSite[], keyOf: KeyOf): ProjectFamily[] {
  const byFolder = new Map<string, { site: ProjectSite; paths: string[] }>()

  for (const site of sites) {
    const folder = keyOf(site.realPath)
    const held = byFolder.get(folder)
    if (held === undefined) {
      byFolder.set(folder, { site, paths: [site.path] })
      continue
    }
    held.paths.push(site.path)
    // The folder itself outranks any name pointing at it, whichever arrived first.
    if (keyOf(site.path) === folder) held.site = site
  }

  const families = new Map<string, { commonDir: string | null; members: ProjectMember[] }>()
  const order: string[] = []

  for (const [folder, held] of byFolder) {
    const member: ProjectMember = {
      path: held.site.path,
      aliases: held.paths.filter((path) => keyOf(path) !== keyOf(held.site.path)),
      branch: held.site.branch,
    }

    // A project outside git is its own family. Grouping every one of them under "no common
    // directory" would draw a family whose only shared property is not being a worktree.
    // The prefix is NUL, written as an escape: no path can hold one, and a literal byte
    // here is invisible in every editor and every diff (RG184).
    const key = held.site.commonDir === null ? `\u0000solo:${folder}` : keyOf(held.site.commonDir)
    const existing = families.get(key)
    if (existing === undefined) {
      families.set(key, { commonDir: held.site.commonDir, members: [member] })
      order.push(key)
    } else {
      existing.members.push(member)
    }
  }

  return order.map((key) => {
    const family = families.get(key)
    return {
      commonDir: family?.commonDir ?? null,
      members: orderMembers(family?.members ?? []),
    }
  })
}

/** A family with more than one member is one worth drawing as a family. */
export function isFamily(family: ProjectFamily): boolean {
  return family.members.length > 1
}
