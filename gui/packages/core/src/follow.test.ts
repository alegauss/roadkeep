import { describe, expect, it } from 'vitest'

import { arrivedSince, atEnd, END_SLACK_PX, FOLLOWING, regionHeight, scrolledTo } from './follow'

/** A region 400 tall showing 100, scrolled to `top`. */
const region = (top: number) => ({ top, height: 400, visible: 100 })

describe('RG206: whether the reader is at the end', () => {
  it('is at the end on the last pixel, and within the slack short of it', () => {
    expect(atEnd(region(300))).toBe(true)
    expect(atEnd(region(300 - END_SLACK_PX))).toBe(true)
    expect(atEnd(region(300 - END_SLACK_PX - 1))).toBe(false)
  })

  it('is at the end where everything fits, which is how a short stream starts', () => {
    expect(atEnd({ top: 0, height: 80, visible: 100 })).toBe(true)
    // And where nothing was measured, as in a window without layout.
    expect(atEnd({ top: 0, height: 0, visible: 0 })).toBe(true)
  })
})

describe('RG206: following, moved by the scroll', () => {
  it('stops where the reader scrolls away, remembering how many acts there were', () => {
    const left = scrolledTo(FOLLOWING, region(0), 12)

    expect(left).toEqual({ leftAt: 12 })
    expect(arrivedSince(left, 12)).toBe(0)
    expect(arrivedSince(left, 15)).toBe(3)
  })

  it('keeps the first count while the reader scrolls further, since that is what they missed', () => {
    const left = scrolledTo(FOLLOWING, region(150), 12)

    expect(scrolledTo(left, region(40), 20)).toBe(left)
  })

  it('follows again once the reader is back at the end', () => {
    const left = scrolledTo(FOLLOWING, region(0), 12)

    expect(scrolledTo(left, region(300), 20)).toBe(FOLLOWING)
    expect(arrivedSince(FOLLOWING, 20)).toBe(0)
  })

  it('hands back the same state where nothing changed, so a screen does not redraw', () => {
    expect(scrolledTo(FOLLOWING, region(300), 30)).toBe(FOLLOWING)
  })
})

describe('RG217: how much room a stream region has', () => {
  /** The session surface at 1280 by 800, where RG210's pictures were read. */
  const desktop = { top: 288, viewport: 800, gutter: 40, floor: 320 }

  it('gives it the space under its own top, less the page gutter', () => {
    // 472, against the 608 that `calc(100dvh - 12rem)` gave it — the 136 pixels the region
    // ran past the bottom of the window, with the newest act inside them.
    expect(regionHeight(desktop)).toBe(472)
  })

  it('measures from where the region actually is, not from a subtraction', () => {
    // A hero that wrapped, which is what a long symptom or a second language does. The old
    // rule answered the same number for both and this one does not.
    expect(regionHeight({ ...desktop, top: 360 })).toBe(400)
    expect(regionHeight({ ...desktop, top: 240 })).toBe(520)
  })

  it('never goes under the floor, below which the page scrolls instead', () => {
    // At 400 wide the columns stack, so the region's top is far down the page: there is no
    // arrangement that makes a region of forty pixels worth scrolling inside.
    expect(regionHeight({ ...desktop, top: 700 })).toBe(320)
    expect(regionHeight({ ...desktop, top: 440 })).toBe(320)
    expect(regionHeight({ ...desktop, top: 439 })).toBe(321)
  })

  it('follows the window rather than a width, so a resize is a new answer', () => {
    expect(regionHeight({ ...desktop, viewport: 1000 })).toBe(672)
    expect(regionHeight({ ...desktop, viewport: 600 })).toBe(320)
  })
})
