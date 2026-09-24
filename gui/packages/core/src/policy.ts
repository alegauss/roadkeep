/**
 * What the renderer is allowed to load, which is the half the posture does not settle.
 *
 * Context isolation, the sandbox and the navigation guard between them decide what the page
 * may *do*. None of them decides what it may *fetch*. A page that ends up with a remote
 * `<script>` — an injected tag, a dependency that grew a CDN call, a payload rendered as
 * HTML — runs that script with the bridge sitting on `window`, and the navigation guard
 * never fires because nothing navigated.
 *
 * **Two policies, and the packaged one is the one that matters.** Vite injects an inline
 * preamble for React Refresh and talks to itself over a websocket, so a policy strict enough
 * to be worth shipping stops `npm run dev`. The development one exists so that nobody turns
 * the mechanism off to get work done — which is how a policy comes to be written and never
 * applied.
 *
 * The policy is data here and a header in `shell`, for the reason everything else in this
 * package is: what a directive says is a rule, and attaching it to a response needs a
 * session this half does not have.
 */

/** A directive and what it permits. An empty list is `'none'` spelled by the caller. */
export type Policy = Readonly<Record<string, readonly string[]>>

/** Nothing at all, which is a value and not an absence. */
const NONE = ["'none'"] as const
const SELF = ["'self'"] as const

/**
 * What a packaged build loads: itself, and data URIs for the two things that need them.
 *
 * `style-src` carries `'unsafe-inline'` and it is not an oversight. A `style` attribute is
 * inline style to CSP, and React writes them — the marker's face, and the `color-scheme`
 * next-themes stamps on the document element. The alternative is a nonce threaded through
 * a renderer that has no server to mint one, which buys nothing here: the script directive
 * is what stops code running, and that one is `'self'` alone.
 */
export const PACKAGED_POLICY: Policy = {
  'default-src': SELF,
  'script-src': SELF,
  'style-src': ["'self'", "'unsafe-inline'"],
  'img-src': ["'self'", 'data:'],
  'font-src': ["'self'", 'data:'],
  // The renderer's only way out is the bridge, which is IPC and not a request.
  'connect-src': SELF,
  'object-src': NONE,
  'base-uri': NONE,
  'frame-src': NONE,
  'frame-ancestors': NONE,
  'form-action': NONE,
}

/**
 * What a development run loads, which is the same plus what Vite needs.
 *
 * Every relaxation here is named and none of them reaches the packaged build: the inline
 * and eval allowances are React Refresh's, and the websocket is how the dev server tells
 * the page a module changed.
 */
export const DEVELOPMENT_POLICY: Policy = {
  ...PACKAGED_POLICY,
  'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
  'connect-src': ["'self'", 'ws:', 'wss:'],
}

/** Which policy is in force, decided by whether a dev server was named. */
export function policyFor(devServerUrl?: string): Policy {
  return devServerUrl === undefined || devServerUrl === '' ? PACKAGED_POLICY : DEVELOPMENT_POLICY
}

/** The header value, directives in the order they are written. */
export function policyText(policy: Policy): string {
  return Object.entries(policy)
    .map(([directive, sources]) => `${directive} ${sources.join(' ')}`)
    .join('; ')
}

/** The header this goes in. Named once so the two halves cannot disagree about it. */
export const POLICY_HEADER = 'Content-Security-Policy'

/**
 * Whether a policy would let a script be fetched from somewhere else.
 *
 * Asked of the policy rather than of a string, so a test states the property and not the
 * spelling: a directive list that grew a host is what this is looking for, whatever the
 * host is called.
 */
export function allowsRemoteScript(policy: Policy): boolean {
  const sources = policy['script-src'] ?? policy['default-src'] ?? []
  return sources.some((source) => !source.startsWith("'"))
}

/** Whether a policy would let a `<script>` in the document body run. */
export function allowsInlineScript(policy: Policy): boolean {
  const sources = policy['script-src'] ?? policy['default-src'] ?? []
  return sources.includes("'unsafe-inline'")
}

/** Whether a policy would let a string be compiled into code. */
export function allowsEval(policy: Policy): boolean {
  const sources = policy['script-src'] ?? policy['default-src'] ?? []
  return sources.includes("'unsafe-eval'")
}
