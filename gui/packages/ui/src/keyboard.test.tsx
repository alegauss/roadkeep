import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { App } from './App'
import { GroundProvider } from './ground'
import { WordingProvider } from './wording'

/**
 * RG54: the half a screenshot cannot show.
 *
 * A dialog that cannot be closed from a keyboard looks correct in every screenshot ever
 * taken of it. What is asserted here is the shape that keeps that from happening — real
 * controls, named, in document order — against the screen there is now, so the screens
 * after it inherit the assertion rather than each having to remember.
 */

/** Everything a person can reach with Tab, plus everything that behaves as a control. */
const FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex], [role="button"]'

function drawScreen() {
  return render(
    <GroundProvider initial="light">
      <WordingProvider>
        <App />
      </WordingProvider>
    </GroundProvider>,
  )
}

/** The accessible name, as far as a DOM without a full accname implementation gives it. */
function nameOf(element: Element): string {
  const label = element.getAttribute('aria-label')?.trim()
  if (label !== undefined && label !== '') return label

  const described = element.getAttribute('aria-labelledby')
  if (described !== null) {
    const target = element.ownerDocument.getElementById(described)
    const text = target?.textContent?.trim() ?? ''
    if (text !== '') return text
  }

  return element.textContent?.trim() ?? ''
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  document.documentElement.className = ''
  localStorage.clear()
})

describe('RG54: what a keyboard can reach', () => {
  it('has controls at all, so the assertions below are about something', () => {
    const { container } = drawScreen()

    expect(container.querySelectorAll(FOCUSABLE).length).toBeGreaterThan(0)
  })

  it('gives every control a name a person hears', () => {
    // An unnamed button is announced as "button", which is a screen with two of them and
    // no way to tell which is which.
    const { container } = drawScreen()

    const unnamed = [...container.querySelectorAll(FOCUSABLE)]
      .filter((element) => nameOf(element) === '')
      .map((element) => element.outerHTML.slice(0, 120))

    expect(unnamed).toEqual([])
  })

  it('makes every control a real one, not a div that listens', () => {
    // A `div` with an `onClick` is not in the tab order and does not answer Enter or
    // Space; the browser gives all three away free to an element that is a control.
    const { container } = drawScreen()

    const pretenders = [...container.querySelectorAll('[onclick], [role="button"]')]
      .filter((element) => element.tagName !== 'BUTTON' && element.tagName !== 'A')
      .map((element) => element.tagName)

    expect(pretenders).toEqual([])
  })

  it('invents no tab order of its own', () => {
    // A positive `tabindex` moves an element ahead of everything the document already
    // ordered, and the next control added lands in a sequence nobody intended.
    const { container } = drawScreen()

    const jumped = [...container.querySelectorAll('[tabindex]')]
      .map((element) => element.getAttribute('tabindex') ?? '')
      .filter((value) => Number(value) > 0)

    expect(jumped).toEqual([])
  })

  it('takes nothing out of the tab order that a person has to use', () => {
    const { container } = drawScreen()

    const removed = [...container.querySelectorAll('button, a[href]')].filter(
      (element) => element.getAttribute('tabindex') === '-1',
    )

    expect(removed).toEqual([])
  })

  it('leaves a control enabled unless it says why it is not', () => {
    // A disabled control is unreachable, so one with no explanation beside it is a dead
    // end a keyboard finds and a mouse does not.
    const { container } = drawScreen()

    const disabled = [
      ...container.querySelectorAll('button[disabled], button[aria-disabled="true"]'),
    ]

    for (const element of disabled) {
      expect(
        element.getAttribute('aria-describedby') ?? element.getAttribute('title'),
      ).not.toBeNull()
    }
  })
})

describe('RG54: what is announced', () => {
  it('hides no text behind an image of it', () => {
    // Text as an image is text nobody can select, resize, translate or read aloud.
    const { container } = drawScreen()

    expect(container.querySelectorAll('img').length).toBe(0)
  })

  it('names the ground control by what it does, not by what it currently says', () => {
    // The label changes as it cycles; the accessible name must not, or a person listening
    // hears the state where they expected the action.
    drawScreen()
    const control = screen.getByTestId('ground')

    expect(control.getAttribute('aria-label')).not.toBe('')
    expect(control.getAttribute('aria-label')).not.toBe(control.textContent)
  })

  it('gives the heading a level rather than a size', () => {
    drawScreen()

    expect(screen.getAllByRole('heading').length).toBeGreaterThan(0)
  })
})
