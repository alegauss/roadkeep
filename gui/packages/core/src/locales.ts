/**
 * Which locales this build ships, and how a tag becomes a lookup.
 *
 * `localeFor` takes the list rather than discovering it, on purpose: a catalogue cannot
 * enumerate what a bundler decided to include, and a list built by scanning would be a list
 * that changes with the build tool. So the list is written here, one line per locale, and
 * adding a language is adding a line beside an import — which is also the moment the suite
 * starts holding that language complete.
 *
 * **The base is in the list.** `en` maps to no translation at all, because the base *is* the
 * answer for `en` and a file repeating it would be a second place for an English string to
 * be wrong. That is what makes `wordingFor` total: every tag has an answer, and a tag nobody
 * wrote has the same answer as `en`.
 *
 * Nothing here resolves an empty tag. An empty tag means the desktop's own, the desktop is a
 * process, and `core` has no process to ask — the shell substitutes before it calls in.
 */

import { PT_BR, PT_BR_LOCALE } from './pt-br'
import { BASE_LOCALE, type Wording } from './wording'

/** No translation, which is how the base answers for itself. */
const NONE: Wording = {}

/** Every locale this build can speak, by tag. */
export const LOCALES: Readonly<Record<string, Wording>> = {
  [BASE_LOCALE]: NONE,
  [PT_BR_LOCALE]: PT_BR,
}

/**
 * The tags, in the order they were written, which is what `localeFor` chooses among.
 *
 * The base is first, so a request that matches two by language takes the base — a
 * preference nothing currently exercises and the right one if it ever does.
 */
export const LOCALE_TAGS: readonly string[] = Object.keys(LOCALES)

/**
 * The lookup for a tag, already resolved.
 *
 * Returns the stored object rather than a copy: the renderer memoises its translator on
 * identity, and a fresh object per call would rebuild every screen on every render.
 */
export function wordingFor(tag: string): Wording {
  return LOCALES[tag] ?? NONE
}
