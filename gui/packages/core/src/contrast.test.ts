import { describe, expect, it } from 'vitest'

import {
  AA_LARGE,
  AA_TEXT,
  contrastOf,
  luminanceOf,
  parseOklch,
  ratioBetween,
  said,
  toLinearRgb,
} from './contrast'

const WHITE = 'oklch(100% 0 0)'
const BLACK = 'oklch(0% 0 0)'

describe('RG54: reading a colour', () => {
  it('reads the form the stylesheets spell', () => {
    expect(parseOklch('oklch(55.6% 0 0)')).toEqual({ l: 0.556, c: 0, h: 0 })

    const accent = parseOklch('oklch(57.7% .245 27.325)')
    expect(accent?.l).toBeCloseTo(0.577, 10)
    expect(accent?.c).toBe(0.245)
    expect(accent?.h).toBe(27.325)
  })

  it('reads a bare lightness as the 0-to-1 it is', () => {
    expect(parseOklch('oklch(0.556 0 0)')?.l).toBeCloseTo(0.556, 6)
  })

  it('ignores an alpha, which does not change what the maths needs', () => {
    expect(parseOklch('oklch(50% 0.1 20 / 0.5)')?.l).toBe(0.5)
  })

  it('answers nothing for anything that resolves somewhere else', () => {
    // The refusal the callers fail on: a pair this cannot read is a pair nobody checks.
    expect(parseOklch('color-mix(in oklab, var(--vg-accent-to), white)')).toBeNull()
    expect(parseOklch('var(--vg-accent-text-dark)')).toBeNull()
    expect(parseOklch('#fbbf24')).toBeNull()
    expect(parseOklch('')).toBeNull()
  })
})

describe('RG54: the conversion', () => {
  it('takes white to white and black to black', () => {
    const white = toLinearRgb({ l: 1, c: 0, h: 0 })
    expect(white.r).toBeCloseTo(1, 6)
    expect(white.g).toBeCloseTo(1, 6)
    expect(white.b).toBeCloseTo(1, 6)

    const black = toLinearRgb({ l: 0, c: 0, h: 0 })
    expect(luminanceOf(black)).toBeCloseTo(0, 6)
  })

  it('stays in gamut for a colour that is not', () => {
    // Clamped, because a display cannot show what is outside it and a negative channel
    // would make the luminance a number no screen ever produces.
    const wild = toLinearRgb({ l: 0.6, c: 0.5, h: 150 })

    for (const channel of [wild.r, wild.g, wild.b]) {
      expect(channel).toBeGreaterThanOrEqual(0)
      expect(channel).toBeLessThanOrEqual(1)
    }
  })

  it('puts a grey where a grey belongs', () => {
    // No chroma means the three channels agree, whatever the hue says.
    const grey = toLinearRgb({ l: 0.5, c: 0, h: 200 })

    expect(grey.r).toBeCloseTo(grey.g, 6)
    expect(grey.g).toBeCloseTo(grey.b, 6)
  })
})

describe('RG54: the ratio', () => {
  it('is 21 for black on white, which is the whole scale', () => {
    expect(contrastOf(BLACK, WHITE)).toBeCloseTo(21, 2)
  })

  it('is 1 for a colour on itself', () => {
    expect(contrastOf(WHITE, WHITE)).toBeCloseTo(1, 6)
  })

  it('does not care which way round it is asked', () => {
    const one = contrastOf('oklch(55.6% 0 0)', WHITE)
    const other = contrastOf(WHITE, 'oklch(55.6% 0 0)')

    expect(one).toBeCloseTo(other ?? 0, 10)
    expect(ratioBetween(0.2, 0.8)).toBe(ratioBetween(0.8, 0.2))
  })

  it('agrees with the published number for this palette own near-threshold grey', () => {
    // `--vg-muted-foreground` on `--vg-background` in light as the package shipped it before
    // VDS92 darkened it to 0.52 — then the pair closest to failing, and still the grey whose
    // published number this is. A test of only comfortable pairs would pass any maths at all.
    const ratio = contrastOf('oklch(55.6% 0 0)', WHITE)

    expect(ratio).toBeGreaterThan(AA_TEXT)
    expect(ratio).toBeLessThan(5)
  })

  it('refuses a pair it cannot read rather than scoring it', () => {
    expect(contrastOf('color-mix(in oklab, a, b)', WHITE)).toBeNull()
    expect(contrastOf(WHITE, 'var(--elsewhere)')).toBeNull()
  })

  it('holds the thresholds apart, because they are different questions', () => {
    expect(AA_TEXT).toBeGreaterThan(AA_LARGE)
  })
})

describe('RG54: what a failure says', () => {
  it('quotes a ratio without rounding it up to the threshold it missed', () => {
    // 4.499 must not read as 4.50 beside a limit of 4.5.
    expect(said(4.499)).toBe('4.49:1')
    expect(said(21)).toBe('21.00:1')
  })
})
