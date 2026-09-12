/**
 * Following the end of a stream that grows (RG206).
 *
 * A session writes several lines a second, and a reader watching it wants the newest act in
 * view without chasing it. A reader who scrolled up to read something wants the opposite:
 * not to be pulled down by the next line. So following is a state the reader moves with the
 * scroll itself, and never a setting — scrolling away is how it is turned off, and coming
 * back to the end is how it is turned on.
 *
 * **Pure, because the half that measures has no layout under test.** jsdom computes no
 * heights and implements no `scrollIntoView`, so the rule is stated over the three numbers a
 * scroll region reports and the count of acts, and the screen only feeds them in.
 *
 * **Counted in acts, not in lines.** What the reader missed is what the stream draws, and one
 * line can be read into two acts.
 */

/**
 * How near the end still counts as at it, in pixels.
 *
 * Not zero: a region's scroll position is fractional under zoom, and a reader who scrolled
 * back down by hand stops a few pixels short more often than on the pixel.
 */
export const END_SLACK_PX = 24

/** What a scroll region reports, named for what each number is rather than the DOM's words. */
export interface Scrolled {
  /** How far down it is scrolled: `scrollTop`. */
  readonly top: number
  /** How tall its content is: `scrollHeight`. */
  readonly height: number
  /** How much of it is visible: `clientHeight`. */
  readonly visible: number
}

/**
 * Where following stands. `leftAt` is how many acts the stream held when the reader scrolled
 * away, and null while it follows.
 */
export interface Follow {
  readonly leftAt: number | null
}

/** Following, which is where every stream starts. */
export const FOLLOWING: Follow = { leftAt: null }

/** Whether a region scrolled like this shows its end, within the slack. */
export function atEnd(scrolled: Scrolled): boolean {
  return scrolled.height - scrolled.top - scrolled.visible <= END_SLACK_PX
}

/**
 * Following after the reader scrolled, with this many acts in the stream.
 *
 * The same object comes back where nothing changed, so a screen that stores it redraws only
 * when following actually turned on or off. Scrolling further up after leaving keeps the count
 * from when the reader first left, since that is where what they have not seen begins.
 */
export function scrolledTo(follow: Follow, scrolled: Scrolled, count: number): Follow {
  if (atEnd(scrolled)) return follow.leftAt === null ? follow : FOLLOWING
  return follow.leftAt === null ? { leftAt: count } : follow
}

/** How many acts arrived since the reader left the end. Zero while following. */
export function arrivedSince(follow: Follow, count: number): number {
  return follow.leftAt === null ? 0 : Math.max(count - follow.leftAt, 0)
}
