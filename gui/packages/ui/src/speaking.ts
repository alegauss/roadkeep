import { BASE, LOCALE_NAMES, LOCALE_TAGS } from '@rk/core'
import { toast } from '@viglet/viglet-design-system'
// The i18n runtime is its own subpath since 2026.3.10: the root barrel no longer re-exports
// it, so a consumer that never speaks more than one language stops resolving i18next.
import { initVigI18n } from '@viglet/viglet-design-system/i18n'
import type { LanguageOption } from '@viglet/viglet-design-system'
// The default export is the shared instance and the named ones are bound to it, which is
// the whole reason this file exists: there is one instance and everybody reads it.
import i18next, { changeLanguage } from 'i18next'
import { useSyncExternalStore } from 'react'

import { AREA_WORDING } from './areas'
import { getBridge } from './bridge'

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
 * The locales this build ships, in the shape the package's menu reads them (RG116).
 *
 * Built once at module scope rather than per render: it is a prop, and a fresh array every
 * pass is a menu that re-renders whenever anything above it does.
 *
 * **Named and not flagged.** `LanguageOption` takes an optional flag and the package's own
 * default list uses one per language, which is the mistake that arrangement invites: a flag
 * is a country and English is not the United States. The name each language uses for itself
 * is the label, from `LOCALE_NAMES` -- an endonym, because the person opening a language
 * menu is the one who cannot read the language currently on screen.
 */
export const SPOKEN_LOCALES: readonly LanguageOption[] = LOCALE_TAGS.map((code) => ({
  code,
  label: LOCALE_NAMES[code] ?? code,
}))

/**
 * What the settings file is known to hold, so a change that is not a change is not a write.
 *
 * Empty means *unknown*, which is the honest state before a launch and after a refused
 * write: the next change is written whatever it is.
 */
let onFile = ''

/**
 * Keep whatever language is now being spoken (RG116).
 *
 * **Hung on i18next's own event and not on a control's handler.** i18next holds the
 * language -- that is this file's whole design -- so the place that always knows a change
 * happened is the instance, not whichever menu asked for it. A write wired into one control
 * is a write the *next* control forgets, and the design system's `LanguageSwitcher` is
 * exactly that next control: it calls `changeLanguage` itself and persists only to the
 * browser cache, which is the split source RG87 removed for the ground. Wired here, an
 * uncontrolled menu is not a gap but the design working.
 *
 * **A tag the file already holds is not written**, and that is the whole guard rather than
 * an optimisation. The launch is itself a language change -- the shell resolves an empty
 * setting against the desktop and this speaks the answer -- so a keeper that wrote every
 * event would pin *follow the desktop* to whatever the first start happened to resolve.
 * Comparing against what the file means makes that a non-write no matter when i18next
 * chooses to emit, which ordering alone could not: the emission does not reliably land
 * before `changeLanguage` resolves.
 *
 * Nothing waits on the write and a failure is said out loud, as RG115 has it: the window is
 * already in the new language, so there is nothing to undo -- only a choice that would look
 * kept until the next launch, which is the state worth a sentence. A refusal also forgets
 * what the file holds, so choosing the same language again is a write and not a shrug.
 *
 * The base wording rather than the provider's, for the reason `ground` gives: a rule that
 * needed a hook to say what went wrong could only run inside a render.
 */
function keepSpokenLocale(tag: string): void {
  if (tag === onFile) return
  onFile = tag

  void getBridge()
    ?.saveLocale(tag)
    .catch(() => {
      onFile = ''
      toast.warning(BASE['settings.unsaved'])
    })
}

/** Whether the keeper is attached. One instance, so one listener, for the window's life. */
let keeping = false

/**
 * Start i18next on the tag the shell resolved, and wait for it to be speaking it.
 *
 * Awaited rather than fired off: the caller mounts the window on the next line, and a first
 * frame drawn while `language` is still undefined is a frame in the wrong language.
 *
 * Safe to call twice -- a second `init` would rebuild the instance the package's components
 * are already reading.
 */
export async function startSpeaking(tag: string): Promise<void> {
  // This app's own i18next strings go in at init: the nav labels the package's components
  // resolve, which is the half of the wording RG88 put on this side of the line.
  if (!i18next.isInitialized) initVigI18n(AREA_WORDING)

  // What the shell resolved is what the file already means, whether it holds this tag or
  // holds nothing and defers to the desktop. Said before the change, so the change the
  // launch itself makes is the one thing the keeper does not write back.
  onFile = tag
  if (!keeping) {
    keeping = true
    i18next.on('languageChanged', keepSpokenLocale)
  }

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
