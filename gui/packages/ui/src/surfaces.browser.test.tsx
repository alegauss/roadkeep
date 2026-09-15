import { BASE, LOCALE_TAGS, type Theme } from '@rk/core'
import { screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { page, userEvent } from 'vitest/browser'

import { HOME_ROUTE } from './areas'
import { FOCUSABLE } from './harness'
import { startSpeaking } from './speaking'
import { atSurface, everyRoute } from './surface-harness'

/**
 * RG214: width, tab order and a visible focus, asked of a page that has them.
 *
 * The design system's contract says a page never scrolls sideways at phone width, and RG54 says
 * every control is reachable from a keyboard. Both were asserted in jsdom, which has no width to
 * overflow and fakes its Tab: a table overflowing at 400 wide, or a toolbar whose tab order is
 * not its visual order, passed every one of those tests. RG215 found the first kind by hand, in
 * forty pictures, which is the read this replaces.
 *
 * Every surface the router serves, from `surface-harness` — the fixture the pseudo-locale run
 * already fills them with — so a surface added to the window is one this reads on the day it
 * routes.
 */

const PHONE = { width: 400, height: 800 }
const DESKTOP = { width: 1280, height: 800 }

/** The two grounds a colour is read in. `system` is a setting and paints one of these. */
const GROUNDS: readonly Theme[] = ['light', 'dark']

/**
 * The page, which the shell draws every surface inside.
 *
 * Reading order is asked of this and not of the window: the chrome is a header across the top
 * and a rail down the side, and a rail whose buttons begin above the header's is laid out
 * correctly and reads backwards by the rule below.
 */
function thePage(): HTMLElement {
  const main = document.querySelector('main')
  if (main === null) throw new Error('the shell drew no page')
  return main
}

/** Drawn, and filled in from its reads — the first frame of a surface has none of them. */
async function settled(): Promise<void> {
  await waitFor(() => {
    expect(thePage().textContent.trim()).not.toBe('')
  })
}

/**
 * The controls a Tab is offered, which is RG54's count less what is not being offered.
 *
 * `tabindex="-1"` is a control held out of the order on purpose — `BentoBackToTop` while the
 * page has not scrolled — and RG54 already asserts that nothing a person has to use is in that
 * set. Disabled and hidden are the same kind of absence: at 400 wide the shortcuts button is
 * `max-sm:hidden`, and a run that expected it there would be asserting the wide window.
 */
function offered(): HTMLElement[] {
  return [...document.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (element) =>
      element.getAttribute('tabindex') !== '-1' &&
      !element.hasAttribute('disabled') &&
      element.closest('[aria-hidden="true"], [inert]') === null &&
      element.checkVisibility(),
  )
}

/**
 * Put the caret at the top of the document, so the first Tab lands on the first control.
 *
 * `body` takes a negative `tabindex` for the moment it is focused: that makes it focusable
 * without putting it in the order, and Tab from there goes to whatever the document offers
 * first. The alternative is tabbing until something recognisable has focus, which is a walk
 * that cannot tell a control it skipped from one that comes later.
 */
function atTheTop(): void {
  document.body.setAttribute('tabindex', '-1')
  document.body.focus()
  document.body.removeAttribute('tabindex')
}

/** Tab `count` times, answering what held focus after each — a real key, through Chromium. */
async function tabThrough(count: number): Promise<Element[]> {
  const reached: Element[] = []
  for (let step = 0; step < count; step += 1) {
    await userEvent.tab()
    if (document.activeElement === null) break
    reached.push(document.activeElement)
  }
  return reached
}

/** A pixel of slack, since a rect is a fraction and two things meant to align rarely do. */
const SLACK = 1

/**
 * Whether one control sits below or to the right of the last, which is the rule.
 *
 * Two that share a line — their vertical ranges overlap, which is the test that survives a
 * short control beside a tall one — read left to right, and that is the toolbar case: a row
 * walked right to left is every control at the same height and each one further back.
 *
 * Off that line, either answer is reading order. Below is the plain one; to the right is a
 * column break — the filing screen's form fills the left column and its panels the right, so
 * the walk leaves the last box at the bottom of one column for the first button at the top of
 * the next, which is where a reader's eye goes too.
 */
function follows(last: DOMRect, next: DOMRect): boolean {
  const sameLine = next.top < last.bottom && last.top < next.bottom
  if (sameLine) return next.left >= last.left - SLACK
  return next.top >= last.top - SLACK || next.left >= last.left - SLACK
}

/**
 * Which control a stop answers for: itself, or the group that handed it the focus.
 *
 * A roving-focus group is one tab stop by design — the settings screen's three are
 * `radiogroup`s, whose arrows move between the choices — so Tab reaches the group and the
 * group gives the focus to the chosen item. The item standing for its group is what keeps that
 * pattern from reading as a control this walk skipped.
 */
function standsFor(controls: readonly HTMLElement[], focused: Element): HTMLElement | null {
  return controls.find((control) => control === focused || control.contains(focused)) ?? null
}

/** A control as a failure should name it: where it stands in the order, and what it is called. */
function said(element: Element, at: number): string {
  const name = element.getAttribute('aria-label') ?? element.textContent.trim()
  return `${String(at)}: <${element.tagName.toLowerCase()}> ${name.slice(0, 40)}`
}

/**
 * What a ring is drawn with, either way a stylesheet can draw one.
 *
 * The long hand and never the `outline` shorthand: computed, that is a colour, a style and a
 * width joined — `rgb(115 115 115) none 0px` for an element with no outline at all — so a test
 * comparing it against `'none'` is one that answers yes to every element on the screen.
 */
function ringOf(element: Element): Record<string, string> {
  const style = getComputedStyle(element)
  return {
    outlineStyle: style.outlineStyle,
    outlineWidth: style.outlineWidth,
    outlineColor: style.outlineColor,
    boxShadow: style.boxShadow,
  }
}

/** Whether that is a ring a person can see: an outline with width, or a shadow. */
function isDrawn(ring: Record<string, string>): boolean {
  const outlined =
    ring['outlineStyle'] !== 'none' && Number.parseFloat(ring['outlineWidth'] ?? '0') > 0
  return outlined || ring['boxShadow'] !== 'none'
}

beforeEach(async () => {
  // The ground is cached in the browser and this one is not thrown away between tests, so a
  // run that left it dark would draw the next window dark whatever it asked for.
  localStorage.clear()
  await page.viewport(DESKTOP.width, DESKTOP.height)
})

afterEach(async () => {
  document.documentElement.className = ''
  localStorage.clear()
  Reflect.deleteProperty(window, 'roadkeep')
  // Back to the language the setup started in, since a run that left the window Portuguese
  // would measure every test after it in Portuguese and call that English.
  await startSpeaking('en')
})

/**
 * Every surface in every language this build ships (RG224).
 *
 * English alone is the language that overflows least: RG215's own defect was Portuguese —
 * `Acrescentar uma dependência` beside its box is wider than a phone-width column and `Add a
 * dependency` is not — and with RG215's hero rule taken out, the portfolio and the project
 * surface ran 475 and 461 pixels wide in Portuguese and fitted in English. Read off
 * `LOCALE_TAGS`, so a language added to the catalogue is one this measures the day it ships.
 *
 * Spoken for real rather than forced with `over`: the rail and the language menu are
 * i18next's, and a window whose catalogue is Portuguese and whose chrome is English measures a
 * page nobody opens.
 */
const EVERY_LANGUAGE = everyRoute().flatMap((route) =>
  LOCALE_TAGS.map((tag) => [route, tag] as const),
)

describe('RG214: no surface scrolls sideways at phone width', () => {
  it.each(EVERY_LANGUAGE)('fits %s at 400 wide in %s', async (route, tag) => {
    await startSpeaking(tag)
    await page.viewport(PHONE.width, PHONE.height)
    await atSurface(route)
    await settled()

    // The document and not a list of elements: what the contract forbids is the page
    // scrolling, and a table or a code block wide enough to need it carries its own
    // `overflow-x: auto`, which is what keeps it from growing the document around it.
    const root = document.documentElement
    expect(
      root.scrollWidth,
      `${route} in ${tag} is ${String(root.scrollWidth)} wide in a window of ${String(root.clientWidth)}`,
    ).toBeLessThanOrEqual(root.clientWidth)
  })
})

describe('RG214: Tab walks every surface in reading order', () => {
  it.each(everyRoute())('reaches each control on %s once, top to bottom', async (route) => {
    await atSurface(route)
    await settled()
    const controls = offered()
    expect(controls.length).toBeGreaterThan(0)

    atTheTop()
    const reached = await tabThrough(controls.length)

    // Document order is what the browser walks, and RG54 asserts nothing claims a place of
    // its own with a positive `tabindex` — so this is every control, each once, in order. By
    // where each stop stands in that list, never by what it looks like: two buttons of the
    // same package and the same name are two controls and a comparison of names is one.
    const walked = reached.map((focused) => {
      // A stop no control accounts for is `-1`, which fails this and names what held the
      // focus — a control the query above walked past, rather than one out of order.
      const control = standsFor(controls, focused)
      return said(control ?? focused, control === null ? -1 : controls.indexOf(control))
    })

    expect(walked).toEqual(controls.map(said))
  })

  it.each(everyRoute())('keeps the page’s own controls in reading order on %s', async (route) => {
    await atSurface(route)
    await settled()
    atTheTop()
    const reached = await tabThrough(offered().length)
    const inside = reached.filter((element) => thePage().contains(element))

    const backwards = inside
      .slice(1)
      .map((element, at) => ({ last: inside[at] as Element, next: element, at: at + 1 }))
      .filter(
        (pair) => !follows(pair.last.getBoundingClientRect(), pair.next.getBoundingClientRect()),
      )
      .map((pair) => `${said(pair.next, pair.at)} after ${said(pair.last, pair.at - 1)}`)

    expect({ route, backwards }).toEqual({ route, backwards: [] })
  })
})

describe('RG214: the focus is visible, in both grounds', () => {
  it.each(GROUNDS)('rings the focused control on the %s ground', async (ground) => {
    await atSurface(HOME_ROUTE, { initial: ground })
    await settled()
    const first = offered()[0] as HTMLElement
    const unfocused = ringOf(first)

    atTheTop()
    await userEvent.tab()
    expect(document.activeElement).toBe(first)
    const focused = ringOf(first)

    // A ring is a colour and RG107 was one: this says a ring is drawn at all, and `contrast`
    // holds what it is drawn in. Drawn *and* changed, because a control with a shadow of its
    // own answers the first question without ever having said where the focus is.
    expect({ ground, drawn: isDrawn(focused) }).toEqual({ ground, drawn: true })
    expect(focused).not.toEqual(unfocused)
  })
})

/**
 * RG229: a project's lines, three columns wide and one column narrow — measured.
 *
 * RG223 stacked the rows below `sm` and was held by a test of two class strings. The rows
 * carrying those strings were stacked at 1280 as well, because the design system's stylesheet
 * declares `grid-cols-1` after this app's utilities and a base class beats a responsive one.
 * Only a browser applies the cascade, so this is where the columns are read.
 */
describe('RG229: a project line is gridded wide and stacked narrow', () => {
  const PROJECT = everyRoute().find(
    (route) => route.startsWith('/project/') && !route.includes('/', 9),
  )

  /** The line's first two cells: its marker and id, then its symptom and why. */
  async function cells(): Promise<[DOMRect, DOMRect]> {
    if (PROJECT === undefined) throw new Error('the router serves no project surface')
    await atSurface(PROJECT)
    const [row] = await screen.findAllByTestId('line')
    const [id, symptom] = [...(row as HTMLElement).children]
    if (id === undefined || symptom === undefined)
      throw new Error('a line drew fewer than two cells')
    return [id.getBoundingClientRect(), symptom.getBoundingClientRect()]
  }

  it('puts the symptom beside the id at 1280', async () => {
    const [id, symptom] = await cells()

    expect(symptom.left).toBeGreaterThanOrEqual(id.right)
    expect(Math.abs(symptom.top - id.top)).toBeLessThan(id.height)
  })

  it('puts the symptom under the id at 400', async () => {
    await page.viewport(PHONE.width, PHONE.height)
    const [id, symptom] = await cells()

    expect(symptom.top).toBeGreaterThanOrEqual(id.bottom)
  })
})

/**
 * RG235: a hero's actions meet at their tops — measured.
 *
 * Each action is a column, its button and then the note under it, and the notes differ: Copy
 * the brief reserves its line and the column beside it does not. Centred on the row, the
 * shorter column's button sat eight pixels below its neighbour, which no class string shows —
 * so the tops are read off the laid-out page, on the one hero that carries two actions.
 */
describe('RG235: the task hero`s actions share a line', () => {
  const TASK = everyRoute().find(
    (route) => route.includes('/task/') && !route.includes('/session/'),
  )

  it('puts the first control of every action at one top, at 1280', async () => {
    if (TASK === undefined) throw new Error('the router serves no task surface')
    await atSurface(TASK)
    await screen.findByRole('button', { name: BASE['task.copy'] })
    const row = document.querySelector('[data-region="hero-actions"]')
    if (row === null) throw new Error('the task drew no hero actions')

    const tops = [...row.children].map((action) => {
      const control = action.querySelector('button, a')
      if (control === null) throw new Error('an action drew no control')
      return control.getBoundingClientRect().top
    })

    expect(tops.length).toBeGreaterThan(1)
    expect(Math.max(...tops) - Math.min(...tops)).toBeLessThanOrEqual(SLACK)
  })
})

/**
 * RG237: the session takes the window's width, and its regions sit as an editor's do — measured.
 *
 * The shell held every page to a 64rem column, and the session drew three columns inside it,
 * so at 1280 its stream had about 360 pixels. Whether a route takes the full width is a class
 * on `main`, and whether a grid puts a region beside another is the cascade, so both are read
 * off the laid-out page.
 */
describe('RG237: the session is a workspace the width of the window', () => {
  const SESSION = everyRoute().find((route) => route.includes('/session/'))

  /** Where each of the session's three regions landed. */
  async function regions(): Promise<{ handed: DOMRect; stream: DOMRect; moved: DOMRect }> {
    if (SESSION === undefined) throw new Error('the router serves no session surface')
    await atSurface(SESSION)
    const at = async (name: string): Promise<DOMRect> => {
      const element = await waitFor(() => {
        const found = document.querySelector(`[data-region="session-${name}"]`)
        if (found === null) throw new Error(`the session drew no ${name} region`)
        return found
      })
      return element.getBoundingClientRect()
    }
    return { handed: await at('handed'), stream: await at('stream'), moved: await at('moved') }
  }

  it('runs the page to the window`s edge, handed, stream and moved left to right, at 1280', async () => {
    const { handed, stream, moved } = await regions()

    expect(thePage().getBoundingClientRect().right).toBeGreaterThanOrEqual(
      document.documentElement.clientWidth - SLACK,
    )
    expect(stream.left).toBeGreaterThanOrEqual(handed.right)
    expect(moved.left).toBeGreaterThanOrEqual(stream.right)
    expect(Math.abs(moved.top - handed.top)).toBeLessThanOrEqual(SLACK)
  })

  it('puts what moved under what was handed, the stream beside both, at 1100', async () => {
    await page.viewport(1100, DESKTOP.height)
    const { handed, stream, moved } = await regions()

    expect(Math.abs(moved.left - handed.left)).toBeLessThanOrEqual(SLACK)
    expect(moved.top).toBeGreaterThanOrEqual(handed.bottom)
    expect(stream.left).toBeGreaterThanOrEqual(handed.right)
    expect(Math.abs(stream.top - handed.top)).toBeLessThanOrEqual(SLACK)
  })

  it('keeps the reading column on every other surface', async () => {
    const other = everyRoute().find(
      (route) => route.includes('/task/') && !route.includes('/session/'),
    )
    if (other === undefined) throw new Error('the router serves no task surface')
    await atSurface(other)
    await settled()

    expect(thePage().getBoundingClientRect().right).toBeLessThan(
      document.documentElement.clientWidth - SLACK,
    )
  })
})

/**
 * RG231: the header's width-dependent parts, each where RG215 put it.
 *
 * RG215 hid the shortcuts button below `sm` on the design system's `Button`, whose own
 * `inline-flex` the package declares after this app's utilities — so the `?` stayed at 400
 * wide, and the Tab walk above, which reads only what is visible, passed either way. Every part
 * of the header that changes with the width is held here, so the next one is a line in this
 * table rather than a picture somebody happens to read.
 */
describe('RG231: the header at each width', () => {
  /** Each part, and whether it is drawn at 400 and at 1280. */
  const PARTS: readonly (readonly [string, string, boolean, boolean])[] = [
    ['the shortcuts button', '[data-testid="shortcuts"]', false, true],
    ["the ground's name", '[data-region="ground-said"]', false, true],
    ["the ground's short name", '[data-region="ground-said-short"]', true, false],
  ]

  it.each(PARTS)('draws %s only where it belongs', async (_, selector, narrow, wide) => {
    for (const [width, drawn] of [
      [PHONE.width, narrow],
      [DESKTOP.width, wide],
    ] as const) {
      await page.viewport(width, PHONE.height)
      const { unmount } = await atSurface(HOME_ROUTE)
      const part = document.querySelector(selector)
      if (part === null) throw new Error(`the header drew no ${selector}`)

      expect({ width, drawn: part.checkVisibility() }).toEqual({ width, drawn })
      unmount()
      Reflect.deleteProperty(window, 'roadkeep')
    }
  })
})
