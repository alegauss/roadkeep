import { describe, expect, it } from 'vitest'

import { arrivedSince, atEnd, END_SLACK_PX, FOLLOWING, scrolledTo } from './follow'

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
