import { timeIn, translator, wordingFor, type Translate, type Wording } from '@rk/core'
import { createContext, useContext, useMemo, type ReactNode } from 'react'

import { useSpokenLocale } from './speaking'

/**
 * How a screen reaches the wording.
 *
 * One context, one hook, and the lookup itself belongs to `core`. What lives here is only
 * the React-shaped part — the renderer is the only package that has React, and the
 * catalogue is not allowed to depend on which framework draws it.
 *
 * **The tag comes from i18next and not from a second place.** The design system's own
 * components read the language off the shared instance, so a provider that took its tag
 * anywhere else would be a second translation system on the same screen — see `speaking`,
 * which is where that answer is kept.
 *
 * **There is no default that means English-by-accident.** A component rendered outside the
 * provider gets the base wording, which is right, but the provider is what a test replaces
 * to render the whole screen under another locale — and that is the mechanism the design
 * rests on, so it is deliberately the only way in.
 */
const Wording = createContext<Translate>(translator())

export function WordingProvider({
  over,
  children,
}: {
  /**
   * The translation to force, which is a test's door. Absent is whatever i18next is
   * speaking — the base included, since `en` is the catalogue itself and not a translation.
   */
  readonly over?: Wording
  readonly children: ReactNode
}) {
  const spoken = useSpokenLocale()
  const wording = over ?? wordingFor(spoken)

  // Rebuilt only when the translation itself changes: a lookup that was a new function on
  // every render would re-render every screen that reads one. `wordingFor` returns the
  // stored object, so the identity is stable for as long as the tag is.
  const say = useMemo(() => translator(wording), [wording])

  return <Wording.Provider value={say}>{children}</Wording.Provider>
}

/** The one call a component makes for a string a person will read. */
export function useWording(): Translate {
  return useContext(Wording)
}

/**
 * The one call a component makes for a time a person will read (RG177).
 *
 * The same arrangement as the wording: the rule is `core`'s and what lives here is the tag
 * in force. A screen that wrote a time any other way would be writing it in the desktop's
 * language while its sentences are in the window's.
 */
export function useWhen(): (stamp: string) => string {
  const spoken = useSpokenLocale()
  return useMemo(() => (stamp: string) => timeIn(stamp, spoken), [spoken])
}
