import type { ReactNode } from 'react'

/**
 * The small marks the list screens share: a status pill, a marker's glyph, and the bar that
 * stands where a number will be (RG145, RG148). One place, so the portfolio and a project's
 * backlog draw a verdict and a pending cell the same way.
 */

/** A status in the design system's own intents. No intent is the neutral one. */
export type Intent = 'on' | 'warn' | 'error' | null

/** A status pill in the package's intents: `bento-status` and never a colour named here. */
export function Pill({
  intent,
  children,
}: {
  readonly intent: Intent
  readonly children: ReactNode
}) {
  const tone = intent === null ? 'text-muted-foreground' : `bento-status bento-status-${intent}`
  const dot = intent === null ? 'bg-muted-foreground' : 'bento-status-dot'
  return (
    <span
      className={`inline-flex h-5 items-center gap-1.5 rounded-full border px-2 text-xs font-semibold ${tone}`}
    >
      <span aria-hidden="true" className={`size-1.5 rounded-full ${dot}`} />
      {children}
    </span>
  )
}

/**
 * The face a marker is drawn in, built once — `Marker`'s own, since a marker is the
 * project's codepoint and nothing else. An object literal in the attribute would be a new
 * prop on every row.
 */
const MARKER_FACE = { fontFamily: 'var(--font-marker)' } as const

/** A marker's glyph, in the face every marker in this app is drawn in. */
export function Glyph({ children }: { readonly children: string }) {
  return <span style={MARKER_FACE}>{children}</span>
}

/** Where a number will be, while it is still on its way. Hidden: it says nothing yet. */
export function Bar({ width }: { readonly width: string }) {
  return <span aria-hidden="true" className={`bg-muted block h-2 rounded-full ${width}`} />
}
