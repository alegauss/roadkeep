import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  classListsIn,
  classPairs,
  declaredIn,
  isResponsive,
  losingPairs,
  packageSheets,
  pairsIn,
  positionOf,
  propertiesOf,
  reportOf,
  splitClass,
} from './class-pairs'

/**
 * RG230: the class pair that cannot win, found.
 *
 * The rule is the one measured in Chromium against this app's stylesheet: a responsive class
 * loses at every width when a base class beside it sets the same property and the design
 * system ships that base class but not the responsive one. The fourteen pairs measured are
 * `MEASURED` below, each with what the browser did, so the rule is held to the page and not
 * to what somebody expected.
 */

const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** What the package's stylesheets ship, read the way the gate reads them. */
const SHIPPED = new Set(
  packageSheets(REPO).flatMap((sheet) => [...declaredIn(readFileSync(sheet, 'utf8'))]),
)

/** Each pair measured in Chromium (RG229, RG230), and whether its responsive half applied. */
const MEASURED: readonly (readonly [string, boolean])[] = [
  ['hidden sm:inline', true],
  ['hidden sm:block', false],
  ['hidden sm:grid', false],
  ['hidden sm:flex', true],
  ['grid max-sm:hidden', false],
  ['flex max-sm:hidden', false],
  ['block max-sm:hidden', false],
  ['inline max-sm:hidden', false],
  ['grid-cols-1 sm:grid-cols-2', true],
  ['grid-cols-1 sm:grid-cols-[1fr_1fr]', false],
  ['grid-cols-2 max-sm:grid-cols-1', false],
  ['gap-2 sm:gap-4', false],
  ['flex-col sm:flex-row', true],
  ['items-start sm:items-center', false],
]

describe('RG230: what a class is', () => {
  it('splits variants from the utility on colons outside brackets', () => {
    expect(splitClass('max-sm:grid-cols-1')).toEqual({
      variants: ['max-sm'],
      utility: 'grid-cols-1',
    })
    expect(splitClass('sm:grid-cols-[a:b]')).toEqual({
      variants: ['sm'],
      utility: 'grid-cols-[a:b]',
    })
    expect(splitClass('grid')).toEqual({ variants: [], utility: 'grid' })
  })

  it('calls a class responsive only when every variant is a width', () => {
    expect(isResponsive(splitClass('sm:flex'))).toBe(true)
    expect(isResponsive(splitClass('max-lg:hidden'))).toBe(true)
    expect(isResponsive(splitClass('min-[30rem]:grid'))).toBe(true)
    // A hover or a ground is a different condition, and not the one this judges.
    expect(isResponsive(splitClass('sm:hover:flex'))).toBe(false)
    expect(isResponsive(splitClass('dark:flex'))).toBe(false)
    expect(isResponsive(splitClass('flex'))).toBe(false)
  })

  it('maps a utility to what it sets, and a gap to both of its halves', () => {
    expect(propertiesOf('hidden')).toEqual(['display'])
    expect(propertiesOf('grid-cols-[6rem_1fr]')).toEqual(['grid-template-columns'])
    expect(propertiesOf('gap-4')).toEqual(['column-gap', 'row-gap'])
    expect(propertiesOf('gap-y-2')).toEqual(['row-gap'])
    expect(propertiesOf('justify-items-start')).toEqual(['justify-items'])
    expect(propertiesOf('justify-between')).toEqual(['justify-content'])
    expect(propertiesOf('truncate')).toEqual([])
  })

  it('reads an escaped selector as the class it names', () => {
    expect([
      ...declaredIn('.hidden{display:none}@media (width>=40rem){.sm\\:flex{display:flex}}'),
    ]).toEqual(['hidden', 'sm:flex'])
  })
})

describe('RG230: which pair loses, held to what Chromium did', () => {
  it('reads the package stylesheets, which is what a clean answer rests on', () => {
    // The guard on the guard: nothing shipped would mean nothing ever loses.
    expect(SHIPPED.has('hidden')).toBe(true)
    expect(SHIPPED.has('grid-cols-1')).toBe(true)
    expect(SHIPPED.has('sm:inline')).toBe(true)
    expect(SHIPPED.has('sm:grid')).toBe(false)
  })

  it.each(MEASURED)('answers what the browser did for %s', (pair, applied) => {
    expect(losingPairs(pair.split(' '), SHIPPED).length === 0).toBe(applied)
  })

  it('passes the forms that win: the wide value unshipped with max-sm over it, or a wrapper', () => {
    expect(losingPairs(['grid', 'grid-cols-[6rem_1fr]', 'max-sm:grid-cols-1'], SHIPPED)).toEqual([])
    expect(losingPairs(['max-sm:hidden'], SHIPPED)).toEqual([])
    expect(losingPairs(['gap-x-4', 'gap-y-2', 'max-sm:grid-cols-1'], SHIPPED)).toEqual([])
  })

  it('names both halves of a pair that loses', () => {
    expect(
      losingPairs(['grid', 'grid-cols-1', 'gap-2', 'sm:grid-cols-[1fr_1fr]', 'sm:gap-4'], SHIPPED),
    ).toEqual([
      { base: 'grid-cols-1', responsive: 'sm:grid-cols-[1fr_1fr]' },
      { base: 'gap-2', responsive: 'sm:gap-4' },
    ])
  })
})

describe('RG230: the renderer, read', () => {
  it('finds class lists in any string, a constant or a template', () => {
    const source = [
      "const cell = 'grid-cols-1 sm:grid-cols-[1fr_1fr]'",
      '<div className="flex max-sm:hidden" />',
      'const wide = `grid ${extra} max-sm:hidden`',
      "const plain = 'grid gap-2'",
    ].join('\n')

    expect(classListsIn(source).map((list) => list.classes)).toEqual([
      ['grid-cols-1', 'sm:grid-cols-[1fr_1fr]'],
      ['flex', 'max-sm:hidden'],
      ['grid', 'max-sm:hidden'],
    ])
  })

  it('places a finding where an editor opens it', () => {
    expect(positionOf('one\ntwo three', 8)).toEqual({ line: 2, column: 5 })
  })

  it('fails RG223 as it was written, and names the fix', () => {
    // The done-when: the class string that stacked a project's rows at 1280.
    const source =
      '<li className="grid grid-cols-1 gap-2 border-t px-5 py-3 sm:grid-cols-[6rem_minmax(0,1fr)_11rem] sm:gap-4">'
    const findings = pairsIn('packages/ui/src/Project.tsx', source, SHIPPED)

    expect(findings.map((one) => `${one.base} > ${one.responsive}`)).toEqual([
      'grid-cols-1 > sm:grid-cols-[6rem_minmax(0,1fr)_11rem]',
      'gap-2 > sm:gap-4',
    ])
    const report = reportOf(findings)
    expect(report).toContain('packages/ui/src/Project.tsx:1:15')
    expect(report).toContain('max-sm:')
    expect(report).toContain('wrapper')
  })

  it('finds nothing in the renderer as it is', () => {
    expect(classPairs(REPO)).toEqual([])
  })
})
