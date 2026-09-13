import { BASE, fill } from '@rk/core'
import { screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { page, userEvent } from 'vitest/browser'

import { sessionPath } from './areas'
import { at, hear, KEY, RECORD, ROOT, type Wired } from './session-harness'

/**
 * RG206, held in a real layout (RG213).
 *
 * These were jsdom tests that defined `scrollHeight` and `clientHeight` on the region by hand, so
 * they passed whatever the stylesheet said. Here nothing is measured by hand: the app's CSS
 * bounds the region, acts are appended until it overflows, the reader scrolls with the wheel,
 * and the viewport is narrowed to phone width. A region the CSS stops bounding fails every test
 * below, which is the one thing the jsdom copies could never do.
 */

/** How near the end still counts as at it: a reader's wheel stops a few pixels short. */
const SLACK = 24

/** Enough acts to overflow the region at either width, and a page's worth past it. */
const LONG_RUN = 40

function said(index: number): string {
  return JSON.stringify({
    type: 'assistant',
    message: { content: [{ type: 'text', text: `Act ${String(index)} of a long run.` }] },
  })
}

/** Append `count` acts from line `from`, and answer the line after the last. */
function append(wired: Wired, from: number, count: number): number {
  for (let index = from; index < from + count; index += 1) {
    hear(wired, 'session', { session: KEY, index, line: said(index) })
  }
  return from + count
}

function atEnd(region: HTMLElement): boolean {
  return region.scrollHeight - region.scrollTop - region.clientHeight <= SLACK
}

/** The session's screen with a run long enough that the region scrolls. */
async function overflowing() {
  const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
  const region = await screen.findByTestId('stream')
  const next = append(wired, 1, LONG_RUN)
  await waitFor(() => {
    expect(region.scrollHeight).toBeGreaterThan(region.clientHeight + 200)
  })
  return { wired, region, next }
}

function jump(): HTMLElement | null {
  return screen.queryByRole('button', { name: /^Jump to latest/ })
}

beforeEach(async () => {
  await page.viewport(1280, 800)
})

afterEach(() => {
  Reflect.deleteProperty(window, 'roadkeep')
})

describe('RG206: a stream that follows its end, in the stylesheet’s own layout', () => {
  it('scrolls within a region the window holds, and keeps the newest act in view', async () => {
    const { region } = await overflowing()

    // Bounded: the region scrolls by itself rather than growing the page around it.
    expect(region.clientHeight).toBeLessThan(window.innerHeight)
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
    expect(jump()).toBeNull()
  })

  it('leaves a reader who wheeled up where they are, and says what arrived since', async () => {
    const { wired, region, next } = await overflowing()
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })

    await userEvent.wheel(region, { delta: { y: -2000 } })
    expect(await screen.findByRole('button', { name: BASE['session.follow'] })).toBeTruthy()
    const left = region.scrollTop
    expect(atEnd(region)).toBe(false)

    append(wired, next, 5)

    const back = await screen.findByRole('button', {
      name: fill(BASE['session.follow.since'], { count: 5 }),
    })
    // Not pulled down: the acts landed and the reader is still where the wheel put them.
    expect(Math.abs(region.scrollTop - left)).toBeLessThanOrEqual(1)

    await userEvent.click(back)

    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
    await waitFor(() => {
      expect(jump()).toBeNull()
    })
  })

  it('follows again once the reader wheels back down to the end', async () => {
    const { wired, region, next } = await overflowing()
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })

    await userEvent.wheel(region, { delta: { y: -2000 } })
    await screen.findByRole('button', { name: BASE['session.follow'] })

    await userEvent.wheel(region, { delta: { y: 4000 } })
    await waitFor(() => {
      expect(jump()).toBeNull()
    })

    append(wired, next, 3)
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
  })

  it('stays bounded and follows at phone width, where the columns stack', async () => {
    await page.viewport(400, 800)
    const { region } = await overflowing()

    // `max-h-[70dvh]` below `lg`: most of the window, and never taller than it.
    expect(region.clientHeight).toBeLessThanOrEqual(Math.ceil(window.innerHeight * 0.7) + 1)
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
  })
})
