/**
 * Contrast, computed.
 *
 * A palette that dims a label is an accessibility defect that looks like a style, and the
 * only thing that catches one before somebody squints at it is arithmetic. So this file is
 * the arithmetic: OKLCH in, a WCAG ratio out, no DOM anywhere near it.
 *
 * **It lives in `core` because a browser cannot help.** jsdom does not compute `oklch()`,
 * so `getComputedStyle` hands back the string it was given, and a test that asked the
 * browser what colour a label ended up would be asserting on its own input. The values in
 * the stylesheet are literals; converting them is this app's own work.
 *
 * The conversion is Ottosson's OKLab matrix, which lands on **linear** sRGB — which is
 * exactly what WCAG's relative luminance wants, so nothing is gamma-encoded on the way
 * only to be decoded again.
 */

export interface Oklch {
  /** Lightness, 0 to 1. A percentage in the stylesheet. */
  readonly l: number
  readonly c: number
  /** Hue in degrees. */
  readonly h: number
}

/** Linear sRGB, each 0 to 1 and clamped: a display cannot show what is out of gamut. */
export interface LinearRgb {
  readonly r: number
  readonly g: number
  readonly b: number
}

/**
 * The WCAG 2 thresholds this app holds itself to.
 *
 * AA and not AAA: AAA at 7:1 rules out most of the greys a neutral palette is built from,
 * and a threshold nothing can meet is one that gets suppressed rather than met.
 */
export const AA_TEXT = 4.5
/** Large text — 18.66px bold or 24px — and anything that is not text at all. */
export const AA_LARGE = 3
export const AA_NON_TEXT = 3

const OKLCH = /^oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)(?:deg)?\s*(?:\/.*)?\)$/i

/**
 * Read one `oklch(...)` literal, or answer nothing.
 *
 * Nothing is the answer for `color-mix`, a `var()` chain or anything else that resolves
 * somewhere else. A caller that skipped those would have a check whose coverage shrinks
 * every time the stylesheet grows, so the callers here fail on a null instead.
 */
export function parseOklch(value: string): Oklch | null {
  const found = OKLCH.exec(value.trim())
  if (!found) return null

  const [, lightness, chroma, hue] = found
  const l = Number(lightness)
  const c = Number(chroma)
  const h = Number(hue)
  if (!Number.isFinite(l) || !Number.isFinite(c) || !Number.isFinite(h)) return null

  // A percentage is what the stylesheets spell; the bare form is 0 to 1.
  return { l: value.includes('%') ? l / 100 : l, c, h }
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value))
}

/** OKLCH to linear sRGB, clamped into gamut. */
export function toLinearRgb(colour: Oklch): LinearRgb {
  const radians = (colour.h * Math.PI) / 180
  const a = colour.c * Math.cos(radians)
  const b = colour.c * Math.sin(radians)

  const long = (colour.l + 0.3963377774 * a + 0.2158037573 * b) ** 3
  const medium = (colour.l - 0.1055613458 * a - 0.0638541728 * b) ** 3
  const short = (colour.l - 0.0894841775 * a - 1.291485548 * b) ** 3

  return {
    r: clamp(4.0767416621 * long - 3.3077115913 * medium + 0.2309699292 * short),
    g: clamp(-1.2684380046 * long + 2.6097574011 * medium - 0.3413193965 * short),
    b: clamp(-0.0041960863 * long - 0.7034186147 * medium + 1.707614701 * short),
  }
}

/** WCAG relative luminance, over linear sRGB. */
export function luminanceOf(rgb: LinearRgb): number {
  return 0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b
}

/** The ratio between two luminances, 1 to 21. Order does not matter. */
export function ratioBetween(one: number, other: number): number {
  const lighter = Math.max(one, other)
  const darker = Math.min(one, other)
  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * The contrast between two `oklch(...)` literals, or nothing where either is not one.
 *
 * Null is a refusal to guess and is what a caller must fail on: a pair this cannot read is
 * a pair nobody is checking.
 */
export function contrastOf(front: string, behind: string): number | null {
  const a = parseOklch(front)
  const b = parseOklch(behind)
  if (a === null || b === null) return null

  return ratioBetween(luminanceOf(toLinearRgb(a)), luminanceOf(toLinearRgb(b)))
}

/** Rounded the way a report quotes it, so a threshold is not missed by a rounding artefact. */
export function said(ratio: number): string {
  return `${(Math.floor(ratio * 100) / 100).toFixed(2)}:1`
}
