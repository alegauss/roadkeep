import { AA_NON_TEXT, fromSrgbBytes, luminanceOf, ratioBetween } from '@rk/core'

/**
 * What an accessibility pass over a rendered surface found, and what the run does with it
 * (RG211).
 *
 * RG54 holds token pairs to AA and keyboard reach in jsdom. Neither sees what a component
 * draws: RG207's chosen toggle was the package's accent on its panel, 1.27:1, and passed both.
 * So every surface `npm run shots` photographs is also scanned in the window it was drawn in —
 * by axe, through Playwright, and by one rule axe does not have.
 *
 * **A pass is a floor and never a verdict.** Axe's own documentation says automated checks
 * find some problems and not most: keyboard order, what a screen reader says, and a state no
 * fixture reaches are still somebody's to check.
 *
 * **The exception list is the design `advisories.ts` has.** A finding is accepted by writing
 * down its rule, the element it names and why, and everything else at `serious` or above fails
 * the run. An exception no scan names any more fails too, so the list stays a record of what is
 * true rather than of what somebody once excused.
 */

/** The impacts that fail a run. Below them a finding is written to the report and gates nothing. */
export const GATED_IMPACTS: readonly string[] = ['serious', 'critical']

/** The WCAG levels axe is asked about: A and AA, as 2.0 and 2.1 name them. */
export const AXE_TAGS: readonly string[] = ['wcag2a', 'wcag2aa', 'wcag21aa']

/** This app's own rule, named like one of axe's so the report and the exceptions read alike. */
export const CHOSEN_RULE = 'chosen-state-told-by-shade'

export interface Finding {
  readonly rule: string
  readonly impact: string
  readonly help: string
  /** The element, as axe's selector names it. */
  readonly target: string
  readonly surface: string
  readonly ground: string
}

export interface AcceptedFinding {
  readonly rule: string
  readonly target: string
  /** Why it stands, and the line that will take it away where there is one. */
  readonly why: string
  readonly established: string
}

/** The findings this project has read and accepted. Empty is the aim. */
export const ACCEPTED_FINDINGS: readonly AcceptedFinding[] = [
  {
    rule: 'color-contrast',
    target: '.text-muted-foreground\\/70',
    why: "the design system's AppFooter draws the product and version at muted-foreground/70, which misses AA in the light ground; the component is the package's, and a correction belongs in the package rather than an override here (viglet-ds-pages, boundary.md)",
    established: '2026-09-12',
  },
]

function text(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

/**
 * Every violation an axe result names, one per element, at any impact.
 *
 * Read off `violations` alone: `incomplete` is what axe could not decide, which is a person's
 * to look at and not a gate's to fail on.
 */
export function findingsIn(result: unknown, surface: string, ground: string): Finding[] {
  const violations =
    typeof result === 'object' && result !== null && 'violations' in result ? result.violations : []
  if (!Array.isArray(violations)) return []

  const found: Finding[] = []
  for (const violation of violations) {
    if (typeof violation !== 'object' || violation === null) continue
    const nodes: unknown = 'nodes' in violation ? violation.nodes : []
    if (!Array.isArray(nodes)) continue
    for (const node of nodes) {
      const target =
        typeof node === 'object' && node !== null && 'target' in node && Array.isArray(node.target)
          ? node.target.map(text).join(' ')
          : ''
      found.push({
        rule: text('id' in violation ? violation.id : ''),
        impact: text('impact' in violation ? violation.impact : ''),
        help: text('help' in violation ? violation.help : ''),
        target,
        surface,
        ground,
      })
    }
  }
  return found
}

function acceptedFor(finding: Finding, accepted: readonly AcceptedFinding[]): boolean {
  return accepted.some((one) => one.rule === finding.rule && one.target === finding.target)
}

/** The gated findings nobody has written down a reason for. Empty is a clean run. */
export function unexcusedFindings(
  found: readonly Finding[],
  accepted: readonly AcceptedFinding[] = ACCEPTED_FINDINGS,
): Finding[] {
  return found.filter((one) => GATED_IMPACTS.includes(one.impact) && !acceptedFor(one, accepted))
}

/** Exceptions no scan named — an answer to a question nobody is asking any more. */
export function outlivedFindings(
  found: readonly Finding[],
  accepted: readonly AcceptedFinding[] = ACCEPTED_FINDINGS,
): AcceptedFinding[] {
  return accepted.filter(
    (one) => !found.some((finding) => finding.rule === one.rule && finding.target === one.target),
  )
}

/** A chosen option beside an unchosen sibling, as the page measured them. */
export interface ChosenReading {
  /** A name a reader finds it by: its role and its words. */
  readonly target: string
  /** Each background as the window painted it, composited over what is behind it, in bytes. */
  readonly chosen: readonly [number, number, number]
  readonly sibling: readonly [number, number, number]
  /**
   * How many marks each carries: the elements it holds, and each decoration drawn on it — a
   * visible border side, an outline, a shadow, a `::before` or `::after` with content. A mark
   * the sibling lacks is one more of these.
   */
  readonly chosenMarks: number
  readonly siblingMarks: number
}

function isRgb(value: unknown): value is readonly [number, number, number] {
  return Array.isArray(value) && value.length === 3 && value.every((one) => typeof one === 'number')
}

/** The readings a page answered, each checked: the page is another program's answer. */
export function readingsFrom(value: unknown): ChosenReading[] {
  if (!Array.isArray(value)) return []
  const readings: ChosenReading[] = []
  for (const one of value) {
    if (typeof one !== 'object' || one === null) continue
    const target = 'target' in one ? one.target : undefined
    const chosen = 'chosen' in one ? one.chosen : undefined
    const sibling = 'sibling' in one ? one.sibling : undefined
    const chosenMarks = 'chosenMarks' in one ? one.chosenMarks : undefined
    const siblingMarks = 'siblingMarks' in one ? one.siblingMarks : undefined
    if (
      typeof target === 'string' &&
      isRgb(chosen) &&
      isRgb(sibling) &&
      typeof chosenMarks === 'number' &&
      typeof siblingMarks === 'number'
    ) {
      readings.push({ target, chosen, sibling, chosenMarks, siblingMarks })
    }
  }
  return readings
}

export interface ChosenVerdict {
  readonly target: string
  readonly ratio: number
  readonly marked: boolean
  /** Told apart by 3:1 in background, or by a mark: WCAG's non-text contrast, or no colour at all. */
  readonly readable: boolean
}

export function judgeChosen(reading: ChosenReading): ChosenVerdict {
  const ratio = ratioBetween(
    luminanceOf(fromSrgbBytes(...reading.chosen)),
    luminanceOf(fromSrgbBytes(...reading.sibling)),
  )
  const marked = reading.chosenMarks > reading.siblingMarks
  return { target: reading.target, ratio, marked, readable: ratio >= AA_NON_TEXT || marked }
}

/** A verdict that fails, as a finding the report and the exceptions read like axe's. */
export function chosenFindings(
  verdicts: readonly ChosenVerdict[],
  surface: string,
  ground: string,
): Finding[] {
  return verdicts
    .filter((one) => !one.readable)
    .map((one) => ({
      rule: CHOSEN_RULE,
      impact: 'serious',
      help: `a chosen option differs from its sibling by ${one.ratio.toFixed(2)}:1 and carries no mark`,
      target: one.target,
      surface,
      ground,
    }))
}

/**
 * The page expression that reads every chosen option beside an unchosen sibling.
 *
 * Colours are resolved by the browser, not parsed here: a 1×1 canvas is filled with each
 * computed background and read back as bytes, which is what an `oklch` token, a `color-mix` or
 * a variable actually paints. A background with alpha is composited over its ancestors', so a
 * translucent accent is measured over the panel it sits on.
 */
export const CHOSEN_SCRIPT = `(() => {
  const CHOSEN = '[aria-checked="true"],[aria-pressed="true"],[aria-selected="true"],[aria-current]:not([aria-current="false"])'
  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  const context = canvas.getContext('2d', { willReadFrequently: true })
  const bytes = (colour) => {
    context.clearRect(0, 0, 1, 1)
    context.fillStyle = 'rgba(0, 0, 0, 0)'
    context.fillStyle = colour
    context.fillRect(0, 0, 1, 1)
    return Array.from(context.getImageData(0, 0, 1, 1).data)
  }
  const painted = (element) => {
    const layers = []
    for (let at = element; at !== null; at = at.parentElement) layers.push(bytes(getComputedStyle(at).backgroundColor))
    let rgb = [255, 255, 255]
    for (const layer of layers.reverse()) {
      const alpha = layer[3] / 255
      rgb = [0, 1, 2].map((index) => layer[index] * alpha + rgb[index] * (1 - alpha))
    }
    return rgb.map((value) => Math.round(value))
  }
  const unchosen = (element) => {
    const role = element.getAttribute('role')
    return Array.from(element.parentElement ? element.parentElement.children : []).find((other) =>
      other !== element &&
      other.getAttribute('role') === role &&
      !other.matches(CHOSEN) &&
      getComputedStyle(other).display !== 'none'
    )
  }
  // Every decoration drawn on an element, each as a string naming its kind and colour.
  const decorations = (element) => {
    const style = getComputedStyle(element)
    const found = []
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
      const colour = bytes(style['border' + side + 'Color'])
      if (parseFloat(style['border' + side + 'Width']) > 0 && style['border' + side + 'Style'] !== 'none' && colour[3] > 0) found.push('border ' + colour.join(','))
    }
    const outline = bytes(style.outlineColor)
    if (parseFloat(style.outlineWidth) > 0 && style.outlineStyle !== 'none' && outline[3] > 0) found.push('outline ' + outline.join(','))
    if (style.boxShadow !== 'none') found.push('shadow ' + style.boxShadow)
    for (const pseudo of ['::before', '::after']) {
      const content = getComputedStyle(element, pseudo).content
      if (content !== 'none' && content !== 'normal') found.push(pseudo + ' ' + content)
    }
    return found
  }
  // A decoration marks the chosen option only where the sibling draws nothing like it: the
  // first of a joined group has a left border the rest lack, and that is layout, not a mark.
  const marksOf = (element, sibling) => {
    const theirs = new Set(decorations(sibling))
    const own = decorations(element).filter((one) => !theirs.has(one))
    return element.querySelectorAll('*').length + own.length
  }
  const readings = []
  for (const element of document.querySelectorAll(CHOSEN)) {
    const sibling = unchosen(element)
    if (sibling === undefined) continue
    const words = (element.textContent || element.getAttribute('aria-label') || '').trim().slice(0, 40)
    readings.push({
      target: (element.getAttribute('role') || element.tagName.toLowerCase()) + ' "' + words + '"',
      chosen: painted(element),
      sibling: painted(sibling),
      chosenMarks: marksOf(element, sibling),
      siblingMarks: sibling.querySelectorAll('*').length,
    })
  }
  return readings
})()`
