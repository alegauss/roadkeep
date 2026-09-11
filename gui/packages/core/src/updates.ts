import { aString, record, type Reader } from './reading'
import type { Fill, MessageKey } from './wording'

/**
 * Whether a newer build has been published, answered only when somebody asks (RG50).
 *
 * Three rules from the line's design, and this file is where two of them are held. **It says
 * which version it is on and which it found**, because "an update is available" is a sentence
 * nobody can check. **It installs nothing**: the answer is a page to open, and opening it is
 * the person's. The third — that nothing phones anywhere on launch — is the menu's to keep,
 * since this is only ever called from a click.
 *
 * The request itself is the shell's, which has a network. What is here is what a web
 * service would keep: reading the answer, and comparing two versions.
 */

/** What GitHub answers for a repository's newest published release, trimmed to two fields. */
export interface LatestRelease {
  readonly tag: string
  /** The release's own page, which is what the dialog offers to open. */
  readonly url: string
}

export const readLatestRelease: Reader<LatestRelease> = record<LatestRelease>(
  { tag: aString, url: aString },
  { tag: 'tag_name', url: 'html_url' },
)

export type UpdateCheck =
  | {
      readonly kind: 'newer'
      readonly current: string
      readonly latest: string
      readonly url: string
    }
  | { readonly kind: 'current'; readonly current: string; readonly latest: string }
  /**
   * This build is newer than anything published (RG156).
   *
   * Its own answer and not `current`: between a tag and its release every build of the new
   * version is in this state, and telling one it is the newest published drops the version
   * that was found and says something that is not true.
   */
  | { readonly kind: 'ahead'; readonly current: string; readonly latest: string }
  /** Nothing is published yet: GitHub keeps drafts out of `releases/latest`. */
  | { readonly kind: 'none'; readonly current: string }
  /**
   * The check did not get an answer it could read.
   *
   * `reason` is the sentence in English, for a log. What a screen says is `code` looked up
   * in the catalogue, with `fields` filling its holes — and the empty code means the words
   * are the network's own, quoted rather than translated (RG172).
   */
  | {
      readonly kind: 'failed'
      readonly current: string
      readonly reason: string
      readonly code: FailedCheck
      readonly fields: Readonly<Record<string, string>>
    }

/** Which of this app's own sentences explains a check that got no answer (RG172). */
export type FailedCheck =
  /** GitHub answered, with a status that is not success. */
  | 'status'
  /** It answered something that is not JSON. */
  | 'not-json'
  /** It answered JSON without the field this reads. */
  | 'missing'
  /** One of the two versions is not one this can compare. */
  | 'version'
  /** The words are the network's own — a refused connection, a name that did not resolve. */
  | ''

/** The sentence for each way a check got no answer (RG172), in the shape its siblings use. */
export const FAILED_TEXT: Readonly<Record<Exclude<FailedCheck, ''>, MessageKey>> = {
  status: 'update.failed.status',
  'not-json': 'update.failed.not-json',
  missing: 'update.failed.missing',
  version: 'update.failed.version',
}

/** A version's three numbers, or null for anything that is not `X.Y.Z` (a leading `v` allowed). */
export function versionParts(version: string): readonly [number, number, number] | null {
  const match = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(version.trim())
  if (match === null) return null
  return [Number(match[1]), Number(match[2]), Number(match[3])]
}

/** Negative, zero or positive as `a` is older, the same or newer; null where either is not a version. */
export function compareVersions(a: string, b: string): number | null {
  const left = versionParts(a)
  const right = versionParts(b)
  if (left === null || right === null) return null
  for (let at = 0; at < 3; at += 1) {
    const difference = (left[at] ?? 0) - (right[at] ?? 0)
    if (difference !== 0) return difference
  }
  return 0
}

/**
 * What the newest published release means for the build that asked.
 *
 * Three answers and not two (RG156). A build newer than anything published is `ahead` — a
 * developer's, and every build between a tag and its release — because *nothing to fetch* and
 * *you are on the newest published* are different sentences, and only the first is true of it.
 * A version that is not a version, on either side, is a failure with its reason rather than a
 * guess about which is newer.
 */
export function verdictOf(current: string, latest: LatestRelease): UpdateCheck {
  const order = compareVersions(latest.tag, current)
  if (order === null) {
    const odd = versionParts(current) === null ? current || 'unstamped' : latest.tag
    return {
      kind: 'failed',
      current,
      reason: `${odd} is not a version this can compare`,
      code: 'version',
      fields: { version: odd },
    }
  }
  const found = latest.tag.replace(/^v/, '')
  if (order > 0) return { kind: 'newer', current, latest: found, url: latest.url }
  return order === 0
    ? { kind: 'current', current, latest: found }
    : { kind: 'ahead', current, latest: found }
}

/** The sentence a check produces, as a catalogue key and its holes, and the page it offers. */
export interface SaidOfUpdate {
  readonly key: MessageKey
  readonly fill: Fill
  /**
   * A second key, for the half of a failure this app wrote (RG172). Null where the reason is
   * already in `fill` — either because the check did not fail, or because the words are the
   * network's own and are quoted rather than translated.
   */
  readonly because: { readonly key: MessageKey; readonly fill: Fill } | null
  /** The release page to offer, or null where there is nothing newer to go and get. */
  readonly opens: string | null
}

export function saidOfUpdate(check: UpdateCheck): SaidOfUpdate {
  if (check.kind === 'newer') {
    return {
      key: 'update.newer',
      fill: { current: check.current, latest: check.latest },
      because: null,
      opens: check.url,
    }
  }
  if (check.kind === 'current') {
    return { key: 'update.current', fill: { current: check.current }, because: null, opens: null }
  }
  if (check.kind === 'ahead') {
    // Both versions, since what this says is that the two differ the other way round.
    return {
      key: 'update.ahead',
      fill: { current: check.current, latest: check.latest },
      because: null,
      opens: null,
    }
  }
  if (check.kind === 'none') {
    return { key: 'update.none', fill: { current: check.current }, because: null, opens: null }
  }
  return {
    key: 'update.failed',
    fill: { current: check.current, reason: check.reason },
    because: check.code === '' ? null : { key: FAILED_TEXT[check.code], fill: check.fields },
    opens: null,
  }
}
