import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { drawWindow } from './harness'

/**
 * RG127: the drawings the next screen is designed against, held to the window.
 *
 * `docs/design/Main.dc.html` and `Shell.dc.html` draw the chrome, and three lines changed
 * the chrome without redrawing either: RG63 added the palette trigger, RG116 the language
 * menu, RG118 the build line under every page. So a person laying out the project surface
 * measured a header with a control fewer than the one their screen would open inside. That
 * is the same class RG109 closed once, and it recurs for a structural reason — the drawings
 * are the input to work and the chrome is the output of it — so a redraw alone would have
 * lasted until the next control.
 *
 * **What holds them is a name on each drawn control.** An artboard marks every control the
 * window renders with `data-control`, spelled as the handle the window's own tests find it
 * by, and the header's region with `data-region`. This renders the window and asks the two
 * to agree, in order. Something drawn and not rendered yet — the engine chip in `Main` —
 * carries no mark and is drawn dashed, which is the convention for *planned*.
 *
 * `vds-*` artboards are not in here: they are the package's, vendored, and
 * `viglet-ds-page-reference --check` is what keeps those current.
 */
const DESIGN = path.resolve(import.meta.dirname, '..', '..', '..', 'docs', 'design')

/** The artboards that draw this app's chrome, which is every one a screen is laid out in. */
const DRAWING_CHROME = ['Main.dc.html', 'Shell.dc.html'] as const

function artboard(name: string): Document {
  return new DOMParser().parseFromString(readFileSync(path.join(DESIGN, name), 'utf8'), 'text/html')
}

/** The controls an artboard says its header carries, in the order it draws them. */
function drawnControls(drawing: Document): string[] {
  return [...drawing.querySelectorAll('[data-region="header"] [data-control]')].map(
    (element) => element.getAttribute('data-control') ?? '',
  )
}

/** A mark's shapes as numbers, which is the part of it a drawing and a window must share. */
function geometryOf(mark: Element | null): string[] {
  return [...(mark?.querySelectorAll('rect') ?? [])].map((rect) =>
    ['x', 'y', 'width', 'height', 'rx'].map((attribute) => rect.getAttribute(attribute)).join(' '),
  )
}

/** The controls the window's header renders, by the handle its tests find each one with. */
function renderedControls(): string[] {
  const { container } = drawWindow({ initial: 'light' })
  const header = container.querySelector('header')
  if (header === null) throw new Error('the window rendered no header to compare against')

  return [...header.querySelectorAll('[data-testid]')].map(
    (element) => element.getAttribute('data-testid') ?? '',
  )
}

describe('RG127: the chrome the drawings say the window has', () => {
  it('renders four controls, which is what makes the comparison below mean anything', () => {
    // The control. A header that rendered nothing with a handle would agree with an
    // artboard that marked nothing, and both would be wrong.
    expect(renderedControls()).toEqual(['palette-trigger', 'shortcuts', 'language', 'ground'])
  })

  it.each(DRAWING_CHROME)('draws the header the window renders, in its order: %s', (name) => {
    expect(
      drawnControls(artboard(name)),
      `${name} draws a different header from the one the window renders. Redraw it — it is` +
        ' what the next screen is laid out against — and mark each control with the' +
        ' `data-testid` the window gives it.',
    ).toEqual(renderedControls())
  })

  it.each(DRAWING_CHROME)('draws the footer the window carries under every page: %s', (name) => {
    const { container } = drawWindow({ initial: 'light' })

    // Both, rather than the artboard alone: the day the footer goes, the drawing's region is
    // what should go with it, and a check on one side only would pass that.
    expect(container.querySelector('footer')).not.toBeNull()
    expect(artboard(name).querySelector('[data-region="footer"]')).not.toBeNull()
  })

  it.each(DRAWING_CHROME)('draws the mark the window renders, rect for rect: %s', (name) => {
    // RG136: the drawings led the header with an amber folder glyph the window never had,
    // and a mark is not a control, so the check above could not see it. Both now carry
    // roadkeep's own mark in a `brand` region, and what is held is its geometry — a colour
    // is the ground's to choose, and the drawing is one ground of two.
    const { container } = drawWindow({ initial: 'light' })
    const rendered = container.querySelector('header [data-region="brand"] svg')
    const drawn = artboard(name).querySelector('[data-region="header"] [data-region="brand"] svg')

    expect(rendered).not.toBeNull()
    expect(drawn).not.toBeNull()
    expect(geometryOf(drawn)).toEqual(geometryOf(rendered))
    expect(geometryOf(rendered)).toHaveLength(6)
  })

  it('leaves unmarked what is drawn and not rendered, rather than lying about the window', () => {
    // The engine chip RG118 misread as the app's build: a real thing this app will need,
    // kept in the drawing and marked as not yet there — by the absence of a handle and by a
    // dashed outline. A `data-control` on it would be a claim this file would then refute.
    const main = artboard('Main.dc.html')
    const header = main.querySelector('[data-region="header"]')

    expect(header?.textContent).toContain('ENGINE')
    expect(drawnControls(main)).not.toContain('engine')
  })
})
