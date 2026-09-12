import { BASE, DEFAULT_SETTINGS, type SessionNotes } from '@rk/core'
import { toast } from '@viglet/viglet-design-system'
import { useSyncExternalStore } from 'react'

import { getBridge } from './bridge'

/**
 * How a session draws its system notes, as this window holds it (RG208).
 *
 * **Held once for the window, like the language.** The ground has `next-themes` and the
 * language has i18next; this preference has no library behind it, so it is the smallest store
 * that does the same job — one value for the window's life, set from the launch read, moved by
 * the settings screen, and read by every session screen through a subscription so a choice
 * made in one place redraws the other.
 *
 * **Changed on screen first, then kept.** As with the ground, nothing waits on the write: the
 * stream already redraws, so a write that fails leaves nothing to undo and one thing worth
 * saying — that the next launch will not have it.
 */

let held: SessionNotes = DEFAULT_SETTINGS.sessionNotes
const listeners = new Set<() => void>()

function told(): void {
  for (const listen of listeners) listen()
}

/** Take what the settings file holds, at launch. Not a write: the file already says it. */
export function holdSessionNotes(notes: SessionNotes): void {
  if (notes === held) return
  held = notes
  told()
}

/** Choose, redraw every screen that reads it, and keep it in the file. */
export function chooseSessionNotes(notes: SessionNotes): void {
  if (notes === held) return
  holdSessionNotes(notes)
  void getBridge()
    ?.savePreference('sessionNotes', notes)
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

function current(): SessionNotes {
  return held
}

/** The choice in force, as a screen reads it. */
export function useSessionNotes(): SessionNotes {
  return useSyncExternalStore(subscribe, current, current)
}
