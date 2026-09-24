import type { ReactNode } from 'react'

/**
 * What a page puts on the trailing edge of its hero (RG215).
 *
 * `BentoHero` takes a `trailing` node and puts it in a row that neither shrinks nor wraps,
 * which is right at desktop width and is why every surface scrolled sideways at 400: two
 * buttons beside a title need more room than a phone has, and the second one was cut.
 *
 * So the actions are a row of their own that wraps, marked with a `data-region` the app's
 * stylesheet keys one rule on — the hero's own row may run onto a second line, and the
 * actions fall under the title instead of past the edge. The marker is this app's and not
 * the package's class names, so a release that renames a class does not silently take the
 * rule with it.
 *
 * Every hero's actions come through here, single button included: a lone button is the same
 * overflow with fewer pixels, and a page that wrapped its own would be the one that forgets.
 *
 * **The actions meet at their tops** (RG235). An action is often a column — its button, then
 * the note that says what pressing it did — and one note may reserve its line while its
 * neighbour's does not. Centred, the task's two buttons sat eight pixels apart. The button is
 * the first thing in every column, so the top is the one edge they always share; a floor on
 * each note would align these two and misalign the next action written without one.
 */
export function HeroActions({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <span className="flex flex-wrap items-start gap-2" data-region="hero-actions">
      {children}
    </span>
  )
}
