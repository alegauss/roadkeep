import { describe, expect, it } from 'vitest'

import {
  allowsEval,
  allowsInlineScript,
  allowsRemoteScript,
  DEVELOPMENT_POLICY,
  PACKAGED_POLICY,
  policyFor,
  policyText,
  POLICY_HEADER,
} from './policy'

describe('RG59: what a packaged build may load', () => {
  it('refuses a script from anywhere but itself', () => {
    // The whole point: a remote `<script>` that reached the page would run beside the
    // bridge, and the navigation guard never fires because nothing navigated.
    expect(allowsRemoteScript(PACKAGED_POLICY)).toBe(false)
  })

  it('refuses a script written into the document', () => {
    expect(allowsInlineScript(PACKAGED_POLICY)).toBe(false)
  })

  it('refuses a string compiled into code', () => {
    expect(allowsEval(PACKAGED_POLICY)).toBe(false)
  })

  it('falls back to itself for anything it does not name', () => {
    expect(PACKAGED_POLICY['default-src']).toEqual(["'self'"])
  })

  it('closes the doors nothing here uses', () => {
    for (const directive of [
      'object-src',
      'base-uri',
      'frame-src',
      'frame-ancestors',
      'form-action',
    ]) {
      expect(PACKAGED_POLICY[directive], `${directive} is open`).toEqual(["'none'"])
    }
  })

  it('lets a style attribute through, which React writes and CSP calls inline', () => {
    // Stated rather than left implicit: this is the one relaxation the packaged policy has,
    // and it is in the directive that cannot run code.
    expect(PACKAGED_POLICY['style-src']).toContain("'unsafe-inline'")
    expect(allowsInlineScript(PACKAGED_POLICY)).toBe(false)
  })

  it('lets an image or a font be a data URI and nothing else be', () => {
    expect(PACKAGED_POLICY['img-src']).toEqual(["'self'", 'data:'])
    expect(PACKAGED_POLICY['font-src']).toEqual(["'self'", 'data:'])
    expect(PACKAGED_POLICY['connect-src']).toEqual(["'self'"])
  })
})

describe('RG59: what a development run adds', () => {
  it('allows what Vite needs and says so by differing in exactly two places', () => {
    const relaxed = Object.keys(DEVELOPMENT_POLICY).filter(
      (directive) =>
        (DEVELOPMENT_POLICY[directive] ?? []).join(' ') !==
        (PACKAGED_POLICY[directive] ?? []).join(' '),
    )

    expect(relaxed.sort()).toEqual(['connect-src', 'script-src'])
  })

  it('still refuses a script from another host', () => {
    // The relaxations are inline and eval, which React Refresh needs. A remote script is
    // not something a dev server needs and is not allowed even here.
    expect(allowsRemoteScript(DEVELOPMENT_POLICY)).toBe(false)
    expect(allowsInlineScript(DEVELOPMENT_POLICY)).toBe(true)
    expect(allowsEval(DEVELOPMENT_POLICY)).toBe(true)
  })

  it('opens a websocket, which is how the page is told a module changed', () => {
    expect(DEVELOPMENT_POLICY['connect-src']).toContain('ws:')
  })
})

describe('RG59: which one is in force', () => {
  it('is the packaged one when no dev server was named', () => {
    expect(policyFor()).toBe(PACKAGED_POLICY)
    expect(policyFor('')).toBe(PACKAGED_POLICY)
  })

  it('is the development one when one was', () => {
    expect(policyFor('http://localhost:5173/')).toBe(DEVELOPMENT_POLICY)
  })

  it('never reaches the packaged build with a relaxation, whatever is set', () => {
    // The property, not the branch: an environment variable is what decides, and the
    // build a person installs is the one where it is unset.
    expect(allowsEval(policyFor())).toBe(false)
  })
})

describe('RG59: the header it becomes', () => {
  it('writes every directive it declares', () => {
    const text = policyText(PACKAGED_POLICY)

    for (const directive of Object.keys(PACKAGED_POLICY)) {
      expect(text).toContain(directive)
    }
  })

  it('reads as a policy and not as a list', () => {
    expect(policyText({ 'default-src': ["'self'"], 'object-src': ["'none'"] })).toBe(
      "default-src 'self'; object-src 'none'",
    )
  })

  it('names the header once, so the two halves cannot disagree', () => {
    expect(POLICY_HEADER).toBe('Content-Security-Policy')
  })
})
