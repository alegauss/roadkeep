/**
 * What the window is allowed to become. A renderer that can navigate is a renderer that
 * can be navigated: one redirect and the page holding the bridge is a page somebody else
 * wrote, running with whatever the preload exposed. So every navigation and every window
 * this app is asked to open is reviewed here first.
 *
 * The rules are pure string work on purpose — no Electron, no window — because that is
 * what lets them be tested against the URLs an attack would actually use rather than
 * against the ones a demo uses.
 */

export type NavigationDecision =
  /** The app navigating within itself. */
  | 'allow'
  /** Refuse, and hand it to the system browser, which is the only thing that should follow a link out. */
  | 'open-externally'
  /** Refuse, and go nowhere. */
  | 'refuse'

/** Schemes a person could reasonably have meant to open outside the app. */
const EXTERNAL_SCHEMES = new Set(['http:', 'https:', 'mailto:'])

function parse(candidate: string): URL | null {
  try {
    return new URL(candidate)
  } catch {
    return null
  }
}

/**
 * `file:` URLs share an empty host, so origin comparison would let any absolute path on
 * the machine pass as "the app". The bundle's own directory is the boundary instead.
 */
function insideBundle(target: URL, app: URL): boolean {
  const directory = app.pathname.slice(0, app.pathname.lastIndexOf('/') + 1)
  return directory !== '/' && target.pathname.startsWith(directory)
}

/**
 * Review a navigation the renderer asked for.
 *
 * @param target where it wants to go.
 * @param appUrl where the app itself was loaded from: the dev server in development, the
 *   built `index.html` as a `file:` URL in a packaged run.
 */
export function reviewNavigation(target: string, appUrl: string): NavigationDecision {
  const url = parse(target)
  const app = parse(appUrl)
  if (!url || !app) {
    return 'refuse'
  }

  if (app.protocol === 'file:') {
    return url.protocol === 'file:' && insideBundle(url, app) ? 'allow' : outward(url)
  }

  if (url.protocol === app.protocol && url.host === app.host) {
    return 'allow'
  }

  return outward(url)
}

/**
 * Review a request to open a new window — `window.open`, or a link with a target. The
 * answer is never to open one: this app has one window, and a second one Electron made is
 * a second one carrying the preload.
 */
export function reviewWindowOpen(target: string): Exclude<NavigationDecision, 'allow'> {
  const url = parse(target)
  return url ? outward(url) : 'refuse'
}

function outward(url: URL): Exclude<NavigationDecision, 'allow'> {
  return EXTERNAL_SCHEMES.has(url.protocol) ? 'open-externally' : 'refuse'
}
