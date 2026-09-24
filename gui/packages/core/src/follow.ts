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

/**
 * What a stream region has to work with, in pixels (RG217).
 *
 * RG206 bounded the region at `calc(100dvh - 12rem)`, which is a guess about how much the
 * header and the hero take. At 1280 by 800 they take about 290 and not 192, so the region ran
 * past the bottom of the window and the newest act — the thing the whole arrangement exists to
 * keep in view — was below the fold. A subtraction cannot be right for every hero: one wraps
 * on a long symptom, in a second language, or at a narrower width.
 */
export interface Space {
  /**
   * The region's own top, in the document's own coordinates rather than the viewport's.
   *
   * Against the document, so a reader who scrolled the page a little does not shrink the
   * region under themselves: what is being measured is where it sits on the page, which the
   * scroll position does not change.
   */
  readonly top: number
  /** How tall the window is. */
  readonly viewport: number
  /** What the page keeps below it, which is the shell's own bottom padding. */
  readonly gutter: number
  /** The least it may be, below which the page scrolls instead of the region being unusable. */
  readonly floor: number
}

/** The least room a stream region is given, in rem — below this a reader scrolls the page. */
export const REGION_FLOOR_REM = 20

/**
 * How tall a stream region may be: from its own top to the bottom gutter, and never under the
 * floor.
 *
 * Pure, for the reason the rest of this file is: jsdom computes no heights, so what a test can
 * hold is the arithmetic, and `session.browser.test.tsx` holds the layout it is fed from.
 */
export function regionHeight(space: Space): number {
  return Math.max(space.viewport - space.top - space.gutter, space.floor)
}
