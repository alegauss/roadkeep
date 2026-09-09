import { initVigI18n } from '@viglet/viglet-design-system'
// The default export is the shared instance and the named ones are bound to it, which is
// the whole reason this file exists: there is one instance and everybody reads it.
import i18next, { changeLanguage } from 'i18next'
import { useSyncExternalStore } from 'react'

/**
 * The one answer to what language this window is in.
 *
 * **i18next holds it, and the catalogue is fed from it.** The design system translates its
 * own components with i18next — `react-i18next` and `i18next-browser-languagedetector` are
 * dependencies of this package because of that — and those components read the current
 * language off the shared instance and cannot be told otherwise. So there is no arrangement
 * in which this app keeps a second idea of the locale and the two stay equal; there is only
 * one where they agree by luck, which is the defect the design system's own notes describe
 * for the theme.
 *
 * `RG51`'s catalogue is not replaced by this. Its fifty-line lookup, its `MessageKey` type
 * and the pseudo-locale run that catches a literal typed into a component are all worth
 * keeping — what changes is where the tag comes from, which is here.
 *
 * **The rule for a string is whoever draws it.** A sentence this app's own components render
 * is a `MessageKey`. A sentence the package renders is an i18next key, including the labels
 * this app writes and one of the package's components resolves.
 *
 * **The shell decides, and the detector does not.** `initVigI18n` configures a browser
 * detector that would read `localStorage` and then `navigator`, which is a second source in
 * the same shape `RG87` removed for the ground: the settings file is the source, and
 * `changeLanguage` is what overrides the guess and refreshes the cache behind it.
 */

/**
 * Start i18next on the tag the shell resolved, and wait for it to be speaking it.
 *
 * Awaited rather than fired off: the caller mounts the window on the next line, and a first
 * frame drawn while `language` is still undefined is a frame in the wrong language.
 *
 * Safe to call twice — a second `init` would rebuild the instance the package's components
 * are already reading.
 */
export async function startSpeaking(tag: string): Promise<void> {
  if (!i18next.isInitialized) initVigI18n()
  await changeLanguage(tag)
}

/** The tag in force, or the empty string where nothing has started i18next — a test, a tab. */
export function spokenLocale(): string {
  return i18next.isInitialized ? i18next.language : ''
}

function whenLanguageChanges(listen: () => void): () => void {
  i18next.on('languageChanged', listen)
  return () => {
    i18next.off('languageChanged', listen)
  }
}

/**
 * The tag in force, as a screen reads it.
 *
 * Subscribed rather than read once, so a later `changeLanguage` moves this app's catalogue
 * and the package's components together. A one-shot read at mount would be two systems again
 * from the first switch onwards.
 */
export function useSpokenLocale(): string {
  return useSyncExternalStore(whenLanguageChanges, spokenLocale, spokenLocale)
}
