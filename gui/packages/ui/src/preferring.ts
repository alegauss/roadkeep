import {
  BASE,
  DEFAULT_SETTINGS,
  type RowOrder,
  type SessionLayout,
  type SessionNotes,
  type SessionSides,
  type Settings,
} from '@rk/core'
import { toast } from '@viglet/viglet-design-system'
import { useSyncExternalStore } from 'react'

import { getBridge } from './bridge'

/**
 * The preferences with no library behind them, as this window holds them: how a session draws
 * its system notes (RG208), the order the portfolio opens in (RG241), and where a session's
 * cards sit (RG277) and how wide its side bars are (RG279) — one of each for the window, since
 * the task and gate routes draw one screen.
 *
 * **Held once for the window, like the language.** The ground has `next-themes` and the
 * language has i18next; these have neither, so this is the smallest store that does the same
 * job — one value each for the window's life, set from the launch read, moved by a screen, and
 * read through a subscription so a choice made in one place redraws the other. One store for
 * both, rather than a second one growing beside it.
 *
 * **Changed on screen first, then kept.** As with the ground, nothing waits on the write: the
 * screen already redraws, so a write that fails leaves nothing to undo and one thing worth
 * saying — that the next launch will not have it.
 */

/** The settings rows held here, typed as the file's own fields so a write takes them as they are. */
type Held = Pick<Settings, 'sessionNotes' | 'portfolioOrder' | 'sessionLayout' | 'sessionSides'>

let held: Held = {
  sessionNotes: DEFAULT_SETTINGS.sessionNotes,
  portfolioOrder: DEFAULT_SETTINGS.portfolioOrder,
  sessionLayout: DEFAULT_SETTINGS.sessionLayout,
  sessionSides: DEFAULT_SETTINGS.sessionSides,
}
const listeners = new Set<() => void>()

function told(): void {
  for (const listen of listeners) listen()
}

/** Take a value the settings file holds. Not a write: the file already says it. */
function hold<K extends keyof Held>(key: K, value: Settings[K]): void {
  if (held[key] === value) return
  held = { ...held, [key]: value }
  told()
}

/** Choose, redraw every screen that reads it, and keep it in the file. */
function choose<K extends keyof Held>(key: K, value: Settings[K]): void {
  if (held[key] === value) return
  hold(key, value)
  void getBridge()
    ?.savePreference(key, value)
    .catch(() => {
      toast.warning(BASE['settings.unsaved'])
    })
}

function subscribe(listen: () => void): () => void {
  listeners.add(listen)
  return () => {
    listeners.delete(listen)
  }
}

/** Take what the settings file holds, at launch. */
export function holdSessionNotes(notes: SessionNotes): void {
  hold('sessionNotes', notes)
}

export function chooseSessionNotes(notes: SessionNotes): void {
  choose('sessionNotes', notes)
}

function currentNotes(): SessionNotes {
  return held.sessionNotes
}

/** The choice in force, as a screen reads it. */
export function useSessionNotes(): SessionNotes {
  return useSyncExternalStore(subscribe, currentNotes, currentNotes)
}

/** Take what the settings file holds, at launch (RG241). */
export function holdPortfolioOrder(order: RowOrder): void {
  hold('portfolioOrder', order)
}

/** Choose from a column head: the table redraws first and the file is written after. */
export function choosePortfolioOrder(order: RowOrder): void {
  choose('portfolioOrder', order)
}

function currentOrder(): RowOrder {
  return held.portfolioOrder
}

/** The order in force, as the portfolio reads it. */
export function usePortfolioOrder(): RowOrder {
  return useSyncExternalStore(subscribe, currentOrder, currentOrder)
}

/** Take what the settings file holds, at launch (RG277). */
export function holdSessionLayout(layout: SessionLayout): void {
  hold('sessionLayout', layout)
}

/** Move a card: the screen redraws first and the file is written after. */
export function chooseSessionLayout(layout: SessionLayout): void {
  choose('sessionLayout', layout)
}

function currentLayout(): SessionLayout {
  return held.sessionLayout
}

/** The arrangement in force, as the session screen reads it. */
export function useSessionLayout(): SessionLayout {
  return useSyncExternalStore(subscribe, currentLayout, currentLayout)
}

/** Take what the settings file holds, at launch (RG279). */
export function holdSessionSides(sides: SessionSides): void {
  hold('sessionSides', sides)
}

/** Keep a side bar's width once its edge is let go: the panel already draws it. */
export function chooseSessionSides(sides: SessionSides): void {
  choose('sessionSides', sides)
}

function currentSides(): SessionSides {
  return held.sessionSides
}

/** The widths in force, as the session screen reads them. */
export function useSessionSides(): SessionSides {
  return useSyncExternalStore(subscribe, currentSides, currentSides)
}
