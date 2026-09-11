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
  /** Nothing is published yet: GitHub keeps drafts out of `releases/latest`. */
  | { readonly kind: 'none'; readonly current: string }
  /** The check did not get an answer it could read, said in the words that explain why. */
  | { readonly kind: 'failed'; readonly current: string; readonly reason: string }

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
 * A build newer than anything published — a developer's — reads as current: nothing to
 * fetch is the true answer for it. A version that is not a version, on either side, is a
 * failure with its reason rather than a guess about which is newer.
 */
export function verdictOf(current: string, latest: LatestRelease): UpdateCheck {
  const order = compareVersions(latest.tag, current)
  if (order === null) {
    const odd = versionParts(current) === null ? current || 'unstamped' : latest.tag
    return { kind: 'failed', current, reason: `${odd} is not a version this can compare` }
  }
  const found = latest.tag.replace(/^v/, '')
  return order > 0
    ? { kind: 'newer', current, latest: found, url: latest.url }
    : { kind: 'current', current, latest: found }
}

/** The sentence a check produces, as a catalogue key and its holes, and the page it offers. */
export interface SaidOfUpdate {
  readonly key: MessageKey
  readonly fill: Fill
  /** The release page to offer, or null where there is nothing newer to go and get. */
  readonly opens: string | null
}

export function saidOfUpdate(check: UpdateCheck): SaidOfUpdate {
  if (check.kind === 'newer') {
    return {
      key: 'update.newer',
      fill: { current: check.current, latest: check.latest },
      opens: check.url,
    }
  }
  if (check.kind === 'current') {
    return { key: 'update.current', fill: { current: check.current }, opens: null }
  }
  if (check.kind === 'none') {
    return { key: 'update.none', fill: { current: check.current }, opens: null }
  }
  return {
    key: 'update.failed',
    fill: { current: check.current, reason: check.reason },
    opens: null,
  }
}
