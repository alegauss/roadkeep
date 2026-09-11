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

/**
 * The same caption as a heading of its own, which is what a panel's title is.
 *
 * An element and not a class: a panel's title is a heading a screen reader announces, and the
 * inline one above is a label beside a field. Both were declared in three screens under the
 * design system's own name for something else (RG186) — one `Label` that is a real `<label>`
 * — so they live here, named for what they are.
 */
export function PanelTitle({ children }: { readonly children: ReactNode }) {
  return (
    <h3 className="text-muted-foreground mb-2 text-[11px] font-semibold tracking-wider uppercase">
      {children}
    </h3>
  )
}
