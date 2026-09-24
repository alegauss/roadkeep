import type { MarkerMeaning } from '@rk/core'

/**
 * A status, drawn.
 *
 * The glyph is the project's codepoint and the word beside it is the project's own key
 * name — neither is chosen here, because a table of icons in this app is the rule compiled
 * into a reader the non-goals refuse. What this file decides is only how the two are
 * arranged.
 *
 * **The label is always there.** Nothing can ask the browser whether a codepoint came out
 * as a tofu box, so a label shown only on failure is one that never appears; and it is the
 * same answer for somebody who cannot see the glyph at all, which is why it is text and
 * not a tooltip.
 *
 * **The glyph sits in a fixed box.** Emoji vary in advance width by platform and by
 * codepoint, and a column of rows whose first character is a different width every time is
 * a column that looks ragged for no reason a reader can name.
 */
/**
 * The face, built once. An object literal in the attribute would be a new object on every
 * render, which is a new prop for every row in a list of them.
 */
const MARKER_FACE = { fontFamily: 'var(--font-marker)' } as const

export function Marker({
  meaning,
  showLabel = true,
  className = '',
}: {
  readonly meaning: MarkerMeaning
  /**
   * Drop the word where the same word is already in the row — a column header, say.
   * It stays reachable to a screen reader either way.
   */
  readonly showLabel?: boolean
  readonly className?: string
}) {
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`} data-testid="marker">
      <span
        aria-hidden="true"
        data-testid="marker-glyph"
        className="inline-flex w-5 shrink-0 justify-center leading-none"
        style={MARKER_FACE}
      >
        {meaning.marker}
      </span>
      <span className={showLabel ? 'text-sm' : 'sr-only'} data-testid="marker-label">
        {meaning.label}
      </span>
    </span>
  )
}
