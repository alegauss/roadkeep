import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  ACCEPTED,
  advisoriesIn,
  atLeast,
  GATED_AT,
  idIn,
  outlived,
  unexcused,
  type Accepted,
} from './advisories'

/**
 * RG95: the rule over an advisory report, read against a real one.
 *
 * `captured/npm-audit.json` is `npm audit --json` from this tree, kept verbatim. A
 * hand-written report is this app's idea of what one looks like, and the shape of that
 * answer is npm's to change.
 *
 * What is asserted is the rule and never which advisories this project happens to carry
 * today: a test naming `xlsx` would have to be edited the day it is fixed, which is the day
 * the gate is supposed to speak for itself.
 */
const REPORT: unknown = JSON.parse(
  readFileSync(path.join(import.meta.dirname, 'captured', 'npm-audit.json'), 'utf8'),
)

/** An exception for whatever the captured report happens to name first. */
function acceptingOne(): Accepted {
  const first = advisoriesIn(REPORT)[0]
  if (first === undefined) throw new Error('the captured report names no advisory to accept')
  return { id: first.id, of: first.of, why: 'a test', established: '2026-09-09' }
}

describe('RG95: reading a report', () => {
  it('finds the advisories a real one carries', () => {
    const found = advisoriesIn(REPORT)

    expect(found.length).toBeGreaterThan(0)
    for (const one of found) {
      expect(one.id).toMatch(/^GHSA-/)
      expect(one.url).toContain(one.id)
      expect(atLeast(one.severity, GATED_AT)).toBe(true)
    }
  })

  it('names each advisory once, however many packages it reaches', () => {
    // One package answers for several advisories and one advisory reaches several packages.
    // A list with duplicates would report the same thing twice and need answering twice.
    const ids = advisoriesIn(REPORT).map((one) => one.id)

    expect(ids).toEqual([...new Set(ids)])
  })

  it('reads no advisory out of a package named as a path to one', () => {
    // `via` carries strings as well as objects: a string is another package's name, and the
    // advisory lives on that package's own entry. Treating one as an advisory would report a
    // finding with no id, no severity and no link.
    for (const one of advisoriesIn(REPORT)) expect(one.severity).not.toBe('')
  })

  it('says nothing about a report it cannot read, rather than guessing', () => {
    expect(advisoriesIn(null)).toEqual([])
    expect(advisoriesIn({})).toEqual([])
    expect(advisoriesIn({ vulnerabilities: 'lots' })).toEqual([])
  })

  it('leaves out anything below the floor', () => {
    expect(advisoriesIn(REPORT, 'critical')).toEqual([])
    expect(advisoriesIn(REPORT, 'info').length).toBeGreaterThanOrEqual(
      advisoriesIn(REPORT, 'high').length,
    )
  })

  it('takes the id out of the advisory URL, which is the stable one', () => {
    // npm's numeric `source` is its own registry key; the GHSA id is what a person
    // searching for the advisory will find.
    expect(idIn('https://github.com/advisories/GHSA-4r6h-8v6p-xvw6')).toBe('GHSA-4r6h-8v6p-xvw6')
    expect(idIn('https://example.com/nothing')).toBe('')
  })
})

describe('RG95: what the gate refuses', () => {
  it('refuses an advisory nobody wrote a reason for', () => {
    expect(unexcused(advisoriesIn(REPORT), []).length).toBeGreaterThan(0)
  })

  it('lets through one that is accepted', () => {
    const accepted = acceptingOne()

    expect(unexcused(advisoriesIn(REPORT), [accepted]).map((one) => one.id)).not.toContain(
      accepted.id,
    )
  })

  it('refuses an exception the report no longer names', () => {
    // The half a list like this normally lacks. Entries accumulate, nobody removes them,
    // and the list becomes a record of what somebody once worried about.
    const gone: Accepted = {
      id: 'GHSA-0000-0000-0000',
      of: 'nothing',
      why: 'fixed upstream long ago',
      established: '2026-01-01',
    }

    expect(outlived(advisoriesIn(REPORT), [gone])).toEqual([gone])
  })

  it('is clean against this tree as it stands, which is what makes a red run mean something', () => {
    // Not a claim about which advisories exist — a claim that every one of them has been
    // read and answered. A third one arriving is what breaks the build.
    expect(unexcused(advisoriesIn(REPORT))).toEqual([])
  })
})

describe('RG95: what an accepted advisory has to say', () => {
  it.each(ACCEPTED)('$id carries a reason and a date', (one) => {
    // An id alone is a suppression. What makes this a list somebody wrote deliberately is
    // the other two fields, so they are held rather than trusted.
    expect(one.id).toMatch(/^GHSA-/)
    expect(one.of).not.toBe('')
    expect(one.why.length).toBeGreaterThan(40)
    expect(one.established).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('accepts each advisory once', () => {
    const ids = ACCEPTED.map((one) => one.id)

    expect(ids).toEqual([...new Set(ids)])
  })
})
