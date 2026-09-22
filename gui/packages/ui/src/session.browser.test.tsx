import { BASE, fill, REGION_FLOOR_REM } from '@rk/core'
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

/** A run's worth of acts as a session record already holds them, for a stream opened long. */
function longRun(): string[] {
  return Array.from({ length: LONG_RUN }, (_, index) => said(index + 1))
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

    expect(region.clientHeight).toBeLessThan(window.innerHeight)
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
  })
})

/**
 * RG217: the region ends inside the window.
 *
 * RG206 bounded it at `calc(100dvh - 12rem)`, and the header and the hero take about 290
 * pixels rather than 192 — so at 1280 by 800 the region ran past the bottom of the window and
 * its end, the newest act, was below the fold. A reader still scrolled the page to see what
 * had just arrived, which is the complaint RG206 answered.
 *
 * Measured here and not in jsdom for the reason the rest of this file is: the old rule was a
 * class, and a class is only a number once a browser has read the stylesheet.
 */
describe('RG217: the room the stream is given', () => {
  it('ends inside the window at 1280 by 800, with its newest act in view', async () => {
    const { region } = await overflowing()
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })

    // The bottom of the region, which under the old rule was some way past 800.
    expect(region.getBoundingClientRect().bottom).toBeLessThanOrEqual(window.innerHeight)
    // And it is the room it has rather than a token height: most of what is under its top.
    const room = window.innerHeight - region.getBoundingClientRect().top
    expect(region.clientHeight).toBeGreaterThan(room - 80)
  })

  it('keeps the way back on screen, which is what a reader presses', async () => {
    const { region } = await overflowing()
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
    await userEvent.wheel(region, { delta: { y: -2000 } })

    const back = await screen.findByRole('button', { name: BASE['session.follow'] })
    const seen = back.getBoundingClientRect()
    expect(seen.bottom).toBeLessThanOrEqual(window.innerHeight)
    expect(seen.top).toBeGreaterThanOrEqual(0)
    // And the page itself never moved. Under the old rule the control was below the fold and
    // reaching the region at all scrolled the window to it, which is the reader's complaint.
    expect(window.scrollY).toBe(0)
  })

  it('opens at the end of a stream that was already long, not at its top', async () => {
    // The bound is measured after the first paint, so a stream placed while the region was
    // still unbounded had nowhere to scroll to and stayed at its top — the newest act out of
    // sight and no way back offered, since the region believed it was at its end. Every other
    // test here appends acts after mounting, which places it again and hides this.
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), {
      sessions: [{ ...RECORD, lines: [...RECORD.lines, ...longRun()] }],
    })
    const region = await screen.findByTestId('stream')

    await waitFor(() => {
      expect(region.scrollHeight).toBeGreaterThan(region.clientHeight + 200)
    })
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
    expect(wired.listeners.length).toBeGreaterThan(0)
  })

  it('bounds a stream that opened with no acts, as one a task has just handed over does', async () => {
    // A task navigates here the moment the session spawns, before its first line (RG275). The
    // region was not drawn yet, so the room was measured against nothing and never again, and the
    // stream grew the page with every act. The gate's link is pressed later, which hid this.
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [{ ...RECORD, lines: [] }] })
    await screen.findByText(BASE['session.stream.empty'])

    append(wired, 0, LONG_RUN)
    const region = await screen.findByTestId('stream')
    await waitFor(() => {
      expect(region.scrollHeight).toBeGreaterThan(region.clientHeight + 200)
    })
    expect(region.getBoundingClientRect().bottom).toBeLessThanOrEqual(window.innerHeight)
    await waitFor(() => {
      expect(atEnd(region)).toBe(true)
    })
    expect(window.scrollY).toBe(0)
  })

  it('takes the room a narrower window leaves, down to a floor it stops at', async () => {
    // At 400 the columns stack, so the region's top is far down the page and the measurement
    // hits its floor — below which a region is not worth scrolling inside and the page is.
    await page.viewport(400, 800)
    const { region } = await overflowing()

    expect(region.clientHeight).toBeGreaterThanOrEqual(REGION_FLOOR_REM * 16 - 1)
  })

  it('answers the new window when the reader resizes, not the one it mounted in', async () => {
    const { region } = await overflowing()
    const tall = region.clientHeight

    // Shorter, and still above the floor, so what is being read is the measurement and not
    // the bound under it — at 560 the floor is what answers and the page scrolls instead.
    await page.viewport(1280, 700)
    await waitFor(() => {
      expect(region.clientHeight).toBeLessThan(tall)
    })
    expect(region.getBoundingClientRect().bottom).toBeLessThanOrEqual(window.innerHeight)
  })
})

/**
 * RG225: the stream first, where the columns stack.
 *
 * RG217 measured the room under the stream's own top, and at 1280 that put its end inside the
 * window. At 400 the three columns stacked in the order they were written — what was handed
 * over, the stream, what moved — so the stream's top sat past the middle of the window, the
 * floor answered, and the newest act was below the fold whatever the region did.
 */
describe('RG225: the session at phone width opens on its own words', () => {
  /** A panel's box, found by the region the screen marks it with. */
  function region(name: string): DOMRect {
    const found = document.querySelector(`[data-region="session-${name}"]`)
    if (found === null) throw new Error(`the session drew no ${name} column`)
    return found.getBoundingClientRect()
  }

  it('draws the stream above the other two at 400 wide, with its newest act in view', async () => {
    await page.viewport(400, 800)
    const { region: stream } = await overflowing()
    await waitFor(() => {
      expect(atEnd(stream)).toBe(true)
    })

    expect(region('stream').top).toBeLessThan(region('handed').top)
    expect(region('handed').top).toBeLessThan(region('moved').top)
    // The claim itself: the end of the stream is on screen without the page being scrolled.
    expect(window.scrollY).toBe(0)
    expect(stream.getBoundingClientRect().bottom).toBeLessThanOrEqual(window.innerHeight)
  })

  it('keeps the drawing at 1280: handed over, the stream, what moved, left to right', async () => {
    await overflowing()

    const handed = region('handed')
    const stream = region('stream')
    const moved = region('moved')
    expect(handed.right).toBeLessThanOrEqual(stream.left)
    expect(stream.right).toBeLessThanOrEqual(moved.left)
    // One row: the three tops agree, which a column that fell to a second row would not.
    expect(Math.abs(handed.top - stream.top)).toBeLessThanOrEqual(1)
    expect(Math.abs(stream.top - moved.top)).toBeLessThanOrEqual(1)
  })
})

/**
 * RG303: the person's own reply, in the layout it is drawn in.
 *
 * Here rather than in jsdom because what is in question is a paragraph of somebody's prose in a
 * region 400 pixels wide: whether it wraps or pushes the stream sideways is the stylesheet's
 * answer, and jsdom lays nothing out to give one.
 */
describe('RG303: the reply drawn in the stream', () => {
  /** A reply as the far side keeps one, which is the only way this row is reached. */
  const REPLIED = JSON.stringify({
    type: 'roadkeep_reply',
    text: 'The first one, and keep the suggested-permissions-for-this-session wording as it is.',
  })

  async function drawn(): Promise<HTMLElement> {
    const wired = await at(sessionPath(ROOT, 'AL1', KEY), { sessions: [RECORD] })
    hear(wired, 'session', { session: KEY, index: 1, line: REPLIED })
    return waitFor(() => {
      const row = screen.getAllByTestId('act').find((one) => one.dataset['kind'] === 'replied')
      if (row === undefined) throw new Error('no replied act')
      return row
    })
  }

  it('wraps inside the stream at phone width rather than pushing it sideways', async () => {
    await page.viewport(400, 800)
    const row = await drawn()
    const region = screen.getByTestId('stream')

    // Inside the region it was written into, at its width and not past it.
    expect(row.getBoundingClientRect().right).toBeLessThanOrEqual(
      region.getBoundingClientRect().right + 1,
    )
    expect(region.scrollWidth).toBeLessThanOrEqual(region.clientWidth + 1)
    // Wrapped: a single line of that sentence would not fit in 400 pixels.
    expect(row.getBoundingClientRect().height).toBeGreaterThan(40)
  })

  it('says whose words they are, and keeps them as typed', async () => {
    const row = await drawn()

    expect(row.textContent).toContain(BASE['session.act.replied'])
    expect(row.textContent).toContain('keep the suggested-permissions-for-this-session wording')
  })
})
