import { translator, type Translate, type Wording } from '@rk/core'
import { createContext, useContext, useMemo, type ReactNode } from 'react'

/**
 * How a screen reaches the wording.
 *
 * One context, one hook, and the lookup itself belongs to `core`. What lives here is only
 * the React-shaped part — the renderer is the only package that has React, and the
 * catalogue is not allowed to depend on which framework draws it.
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
  /** The translation in force. Absent is English. */
  readonly over?: Wording
  readonly children: ReactNode
}) {
  // Rebuilt only when the translation itself changes: a lookup that was a new function on
  // every render would re-render every screen that reads one.
  const say = useMemo(() => translator(over), [over])

  return <Wording.Provider value={say}>{children}</Wording.Provider>
}

/** The one call a component makes for a string a person will read. */
export function useWording(): Translate {
  return useContext(Wording)
}
