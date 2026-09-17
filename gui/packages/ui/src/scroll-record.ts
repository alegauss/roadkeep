/**
 * What was last brought into view, for a test that leads somewhere to say where it went (RG266).
 *
 * A test instrument and not shipped code — nothing in `main` imports it, as with `stub-bridge`.
 * jsdom implements no `scrollIntoView`, and the session screen calls it on the frame after an edit
 * leads back to its act (RG246). Absent, that call threw after the test had ended, so every unit
 * run reported an unhandled `TypeError` and the scroll itself was checked by nothing.
 *
 * **Recorded rather than swallowed.** A lead that stopped scrolling, or scrolled to the wrong act,
 * then fails the test that asserts it instead of passing over a throw nobody reads.
 */
export const scrolledIntoView: Element[] = []

/** Give this document a `scrollIntoView` that records, starting from nothing asked. */
export function recordScrolls(): void {
  scrolledIntoView.length = 0
  Element.prototype.scrollIntoView = function scrollIntoView(this: Element) {
    scrolledIntoView.push(this)
  }
}
