import { PACKAGED_POLICY, policyText, POLICY_HEADER } from '@rk/core'
import { describe, expect, it } from 'vitest'

import { withPolicy, type Headers } from './content-policy'

/**
 * RG59: the rewrite, driven directly.
 *
 * What goes wrong with a header rewrite is the case where one is already there, and that is
 * a function of its input alone — so it is asked here rather than inferred from a run.
 *
 * What this does **not** prove is that a browser then refuses a remote script. That needs a
 * run that loads the bundle, which is RG60's harness, and the line is shipped as the half it
 * is rather than as the whole.
 */
describe('RG59: the header a response comes back with', () => {
  it('carries the policy', () => {
    const headers = withPolicy({}, PACKAGED_POLICY)

    expect(headers[POLICY_HEADER]).toEqual([policyText(PACKAGED_POLICY)])
  })

  it('keeps everything else the response said', () => {
    const given: Headers = { 'content-type': ['text/html'], 'cache-control': ['no-store'] }

    const headers = withPolicy(given, PACKAGED_POLICY)

    expect(headers['content-type']).toEqual(['text/html'])
    expect(headers['cache-control']).toEqual(['no-store'])
  })

  it('replaces a policy that was already there rather than adding a second', () => {
    // Two policies are both enforced and the effective one is their intersection, which is
    // how a page comes to refuse its own stylesheet for a reason nobody can find.
    const given: Headers = { 'Content-Security-Policy': ["default-src 'none'"] }

    const headers = withPolicy(given, PACKAGED_POLICY)

    expect(
      Object.keys(headers).filter((name) => name.toLowerCase().includes('content-security')),
    ).toEqual([POLICY_HEADER])
    expect(headers[POLICY_HEADER]).toEqual([policyText(PACKAGED_POLICY)])
  })

  it('replaces one spelled in another case, because a header name is not case-sensitive', () => {
    const given: Headers = { 'content-security-policy': ["default-src 'none'"] }

    const headers = withPolicy(given, PACKAGED_POLICY)

    expect(headers['content-security-policy']).toBeUndefined()
    expect(headers[POLICY_HEADER]).toEqual([policyText(PACKAGED_POLICY)])
  })

  it('answers a response that carried no headers at all', () => {
    expect(withPolicy(undefined, PACKAGED_POLICY)[POLICY_HEADER]).toEqual([
      policyText(PACKAGED_POLICY),
    ])
  })

  it('does not change the headers it was given', () => {
    const given: Headers = { 'content-type': ['text/html'] }

    withPolicy(given, PACKAGED_POLICY)

    expect(Object.keys(given)).toEqual(['content-type'])
  })
})
