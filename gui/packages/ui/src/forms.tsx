import type { ReactNode } from 'react'

/**
 * The two pieces every form on a surface here shares.
 *
 * Here rather than in one screen because the second screen that needed them is the reason
 * they moved: a heading and a box drawn twice are two things to keep the same by hand.
 */

/** A box a person types in, dressed the same wherever one appears. */
export const BOX = 'border-input bg-background rounded-md border px-3 py-2 text-sm'

/**
 * A small heading over a field or a panel.
 *
 * Not `Label`: the design system's `Label` is a real `<label>` element, and this sits inside
 * one. Two things with one name is what the duplicates gate is there to refuse.
 */
export function Caption({ children }: { readonly children: ReactNode }) {
  return (
    <span className="text-muted-foreground text-[11px] font-semibold tracking-wider uppercase">
      {children}
    </span>
  )
}
