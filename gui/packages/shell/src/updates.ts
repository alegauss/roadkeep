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

/** Long enough for a slow network, short enough that a menu click does not seem to hang. */
const CHECK_CEILING = 10000

export type Fetcher = (url: string, init: RequestInit) => Promise<Response>

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
    return {
      kind: 'failed',
      current,
      reason: cause instanceof Error ? cause.message : String(cause),
    }
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
  } catch {
    return { kind: 'failed', current, reason: 'GitHub answered something that is not JSON' }
  }
  const read = readLatestRelease(body, '')
  if (!read.ok) {
    return { kind: 'failed', current, reason: `the answer had no ${read.failure.path}` }
  }
  return verdictOf(current, read.value)
}

/** Whether a URL is one of this project's release pages — the only thing the dialog opens. */
export function isReleasePage(url: string): boolean {
  return url.startsWith(RELEASE_PAGES)
}
