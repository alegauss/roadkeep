import { readLatestRelease, verdictOf, type UpdateCheck } from '@rk/core'

/**
 * Asking GitHub for the newest published release, which is the one network call this app
 * makes on its own behalf (RG50) — and only ever from a click on the menu.
 *
 * In `shell` because it is a request, and in the main process rather than the window so the
 * renderer's content policy names no host for it: the window never learns this call exists.
 */

/** The repository the releases come from. The same one `ci.yml` drafts them into. */
export const RELEASES_OF = 'alegauss/roadkeep-gui'

const LATEST = `https://api.github.com/repos/${RELEASES_OF}/releases/latest`

/** Every page the dialog may open starts here, and nothing else is opened from it. */
export const RELEASE_PAGES = `https://github.com/${RELEASES_OF}/releases/`

/** The host and the path those pages live at, which is what a URL is checked against. */
const RELEASE_HOST = 'github.com'
const RELEASE_PATH = `/${RELEASES_OF}/releases/`

/** Long enough for a slow network, short enough that a menu click does not seem to hang. */
const CHECK_CEILING = 10000

export type Fetcher = (url: string, init: RequestInit) => Promise<Response>

/**
 * Why a request did not answer, in as many of its own words as it has (RG156).
 *
 * `fetch` throws `TypeError: fetch failed` for everything the network did — no such host, a
 * refused connection, a certificate nobody trusts — and keeps what actually happened on
 * `cause`. A dialog saying *fetch failed* tells somebody offline nothing they did not know, so
 * the cause is read and named beside it. A timeout arrives as its own error and already says
 * so, and a cause that is not an `Error` is not invented.
 */
export function reasonOf(thrown: unknown): string {
  if (!(thrown instanceof Error)) return String(thrown)
  const cause = thrown.cause
  return cause instanceof Error && cause.message !== ''
    ? `${thrown.message}: ${cause.message}`
    : thrown.message
}

/**
 * The newest published release against the version this build carries.
 *
 * Every way of not getting an answer is a `failed` with its reason rather than a throw: the
 * dialog that shows this has something true to say in every case, and a check that could
 * crash the main process is a menu item nobody should be offered.
 */
export async function checkForUpdate(
  current: string,
  fetcher: Fetcher = fetch,
  timeoutMs: number = CHECK_CEILING,
): Promise<UpdateCheck> {
  let response: Response
  try {
    response = await fetcher(LATEST, {
      headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'roadkeep-gui' },
      signal: AbortSignal.timeout(timeoutMs),
    })
  } catch (cause) {
    return { kind: 'failed', current, reason: reasonOf(cause) }
  }

  // No published release at all: GitHub answers 404 for `latest` while every release is a
  // draft, which is the state a repository is in until somebody publishes the first one.
  if (response.status === 404) return { kind: 'none', current }
  if (!response.ok) {
    return { kind: 'failed', current, reason: `GitHub answered ${String(response.status)}` }
  }

  let body: unknown
  try {
    body = await response.json()
  } catch (cause) {
    // Reading a body is still the network: a timeout or a dropped connection lands here, and
    // reporting either as *not JSON* names the wrong thing (RG156). Only the parser's own
    // `SyntaxError` says the answer was not JSON.
    const reason =
      cause instanceof SyntaxError ? 'GitHub answered something that is not JSON' : reasonOf(cause)
    return { kind: 'failed', current, reason }
  }
  const read = readLatestRelease(body, '')
  if (!read.ok) {
    return { kind: 'failed', current, reason: `the answer had no ${read.failure.path}` }
  }
  return verdictOf(current, read.value)
}

/**
 * Whether a URL is one of this project's release pages — the only thing the dialog opens.
 *
 * **A path and not a prefix** (RG155). The URL comes off a network answer, so it is somebody
 * else's word, and a string that starts with the right characters is not a location:
 * `…/releases/../../other/repo` starts with it and is another repository's page once the
 * browser normalises the dot segments — after the check said yes. So the URL is parsed and the
 * parts are compared: the scheme, the host, that nobody is named in it, and the pathname the
 * parser normalised.
 *
 * `URL` is what normalises, which is the point: it does the same thing to the dot segments and
 * the percent-encoding that the browser opening the link will do, so what is checked is what
 * gets opened. A string this cannot parse at all is not a page.
 */
export function isReleasePage(url: string): boolean {
  let parsed: URL
  try {
    parsed = new URL(url)
  } catch {
    return false
  }

  return (
    parsed.protocol === 'https:' &&
    // `host` and not `hostname`: a port is part of where this goes, and the pages have none.
    parsed.host === RELEASE_HOST &&
    // A URL may name a user and a password before the host, and `github.com` reads as the
    // password of a host nobody looked at.
    parsed.username === '' &&
    parsed.password === '' &&
    parsed.pathname.startsWith(RELEASE_PATH)
  )
}
