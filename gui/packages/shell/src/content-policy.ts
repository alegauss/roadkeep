import { policyFor, policyText, POLICY_HEADER, type Policy } from '@rk/core'
import { session, type Session } from 'electron'

import { RENDERER_URL_VAR } from './window'

/**
 * Attaching the policy to every response the renderer receives.
 *
 * A response header and not a `<meta>` tag in `index.html`, for one reason: the two runs
 * need different policies and there is one `index.html`. A tag strict enough for the
 * packaged build would stop the dev server, and a tag loose enough for the dev server is
 * the policy that ships.
 *
 * **Every response, not the document's.** A policy on the page and not on what the page
 * pulls in is a policy with a hole in exactly the shape of the thing it is for.
 *
 * **It replaces rather than appends.** Two `Content-Security-Policy` headers are both
 * enforced and the effective policy is their intersection, which sounds safe and is how a
 * page ends up refusing its own stylesheet for a reason nobody can find. There is one
 * policy here and it is this one.
 */

/** Headers as Electron hands them over: a name to a list of values. */
export type Headers = Record<string, string | string[]>

/**
 * The headers a response should carry, given the ones it has.
 *
 * Pure and exported so a test can drive it: what goes wrong with a header rewrite is the
 * case where one is already there, and that is a function of the input alone.
 */
export function withPolicy(existing: Headers | undefined, policy: Policy): Headers {
  const kept: Headers = {}
  for (const [name, value] of Object.entries(existing ?? {})) {
    // Case-insensitively, because a header's name is and a server may spell it any way.
    if (name.toLowerCase() !== POLICY_HEADER.toLowerCase()) kept[name] = value
  }

  kept[POLICY_HEADER] = [policyText(policy)]
  return kept
}

/**
 * Put the policy on the session every renderer loads through.
 *
 * @param on the session to hold. The default one, in the app; a fresh one, in a test.
 * @param policy which policy, defaulting to the one this run's environment implies.
 */
export function attachPolicy(
  on: Session,
  policy: Policy = policyFor(process.env[RENDERER_URL_VAR]),
): void {
  on.webRequest.onHeadersReceived((details, callback) => {
    callback({ responseHeaders: withPolicy(details.responseHeaders, policy) })
  })
}

/** The app's own call: the default session, and the policy for how this run was started. */
export function attachDefaultPolicy(): void {
  attachPolicy(session.defaultSession)
}
