import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { reportOf, screenProse } from './screen-prose'

/**
 * RG191: the gate itself, run over this repository's own sources.
 *
 * It loads a whole program and asks a checker what every candidate name resolves to, which
 * is a server started and a `tsconfig` read — so it is live, and `npm run lint` pays the
 * same cost for the same answer.
 *
 * **Two directions, and the second is the one that matters.** That the renderer is clean is
 * the regression this exists to hold. That the rule *fires* is what says the first assertion
 * means anything: a walk that resolved nothing, or a tag lookup that never matched, would
 * report a clean renderer too.
 *
 * `core` is where it is pointed to prove that, and not a fixture, because `core` reads these
 * fields correctly — `reasonOf` is the catalogue lookup itself. The same three steps have to
 * resolve for the read to be found there, and nothing has to be kept in step with it.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

const CORE_PROJECT = 'packages/core/tsconfig.json'
const coreSource = (file: string): boolean =>
  file.includes('/packages/core/src/') && !file.endsWith('.test.ts')

describe('RG191: prose a screen must not draw', () => {
  it('finds none in the renderer, which is the regression it holds', async () => {
    const findings = await screenProse(REPO)

    expect(findings, reportOf(findings)).toEqual([])
  })

  it('finds the reads in core, so a clean renderer is an answer and not a silence', async () => {
    const findings = await screenProse(REPO, CORE_PROJECT, coreSource)

    expect(findings.length).toBeGreaterThan(0)
    for (const found of findings) {
      expect(found.file).toMatch(/^packages\/core\/src\//)
      expect(found.line).toBeGreaterThan(0)
      expect(found.column).toBeGreaterThan(0)
      expect(found.instead).not.toBe('')
    }
  })

  it('names the whole read, a field name alone not saying which one it is', async () => {
    const findings = await screenProse(REPO, CORE_PROJECT, coreSource)

    // `reasonOf` is the lookup every screen goes through, and the line it falls back on is
    // the one read this rule is about. Found by what it reads, not by where it is.
    const inWording = findings.filter((found) => found.file.endsWith('core/src/wording.ts'))

    expect(inWording.map((found) => found.read)).toContain('unreadable.message')
  })

  it('tells each tagged field apart by what it says to draw instead', async () => {
    const findings = await screenProse(REPO, CORE_PROJECT, coreSource)
    const instead = new Set(findings.map((found) => found.instead))

    // More than one, which is the claim: the replacement comes off the field that was read
    // and is not one sentence this gate prints for everything it finds.
    expect(instead.size).toBeGreaterThan(1)
  })

  it('refuses to answer for a project holding nothing, rather than reading as clean', async () => {
    // The failure mode a gate must never have: a renamed directory answering green.
    await expect(screenProse(REPO, CORE_PROJECT, () => false)).rejects.toThrow(
      /holds no sources to read/u,
    )
  })
})
