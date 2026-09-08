/**
 * What a build says about itself.
 *
 * A packaged build has to answer three questions from inside itself: which version it is,
 * which commit it came from, and whether it was signed. Those go on an about surface and
 * into whatever a defect report carries — a bug from a packaged app is otherwise a
 * screenshot with no build attached.
 *
 * **The commit is stamped at build time and never asked for at run time.** `No git command
 * run by this app` binds here: a build step in `shell` writes what it knows into a file,
 * and this reads what it was given. That is why this half is in `core` — it has no
 * filesystem and needs none.
 *
 * **An unstamped field is a stated absence.** `npm start` from a working tree is a real way
 * to run this, and it has no commit and no signature. Saying `unstamped` is the honest
 * answer; leaving the field out would make a screen invent one.
 */

/** Where the packaging step leaves what it knows. Read at build, not at run. */
export const STAMP_VARS = {
  commit: 'ROADKEEP_GUI_COMMIT',
  version: 'ROADKEEP_GUI_VERSION',
  signed: 'ROADKEEP_GUI_SIGNED',
} as const

/** What this app says it is. Every field is a string, and every absence is said. */
export interface BuildIdentity {
  /** The version, from the package this was built from. */
  readonly version: string
  /** The commit, or `unstamped` where the build was not given one. */
  readonly commit: string
  /**
   * Whether the executable was signed.
   *
   * `unsigned` is truthful and not a placeholder: the certificate is RG49's and it is a
   * thing somebody buys, so until then this is what a build honestly is.
   */
  readonly signed: 'signed' | 'unsigned' | 'unstamped'
  /** Where this build came from: a package, or a working tree. */
  readonly from: 'packaged' | 'source'
}

/** The value used where a stamp was not supplied. Said, never blank. */
export const UNSTAMPED = 'unstamped'

/**
 * Read what the build was stamped with.
 *
 * Takes the values rather than reading a global, so the same function answers for the real
 * build and for a test — and so nothing here needs an environment at all.
 */
export function identityFrom(stamped: {
  readonly version?: string
  readonly commit?: string
  readonly signed?: string
  readonly packaged?: boolean
}): BuildIdentity {
  const signed = stamped.signed ?? ''
  return {
    version: stamped.version === undefined || stamped.version === '' ? UNSTAMPED : stamped.version,
    commit: stamped.commit === undefined || stamped.commit === '' ? UNSTAMPED : stamped.commit,
    signed: signed === 'signed' || signed === 'unsigned' ? signed : UNSTAMPED,
    from: stamped.packaged === true ? 'packaged' : 'source',
  }
}

/**
 * One line naming the build, for an about surface and for a defect report.
 *
 * Everything a person would have to be asked for otherwise. Short enough to paste into an
 * issue, which is the point of it existing at all.
 */
export function saidOfBuild(identity: BuildIdentity): string {
  return `roadkeep-gui ${identity.version} (${identity.commit}, ${identity.from}, ${identity.signed})`
}
