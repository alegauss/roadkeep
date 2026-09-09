import { localeFor, LOCALE_TAGS } from '@rk/core'

/**
 * Which locale the window speaks, decided where the desktop can be asked.
 *
 * `Settings.locale` documents the empty string as *whatever the desktop says*, and `core`
 * cannot keep that promise: it has no environment to read, so `localeFor` answers `en` for
 * an empty tag and is right to. The substitution belongs here, in the package that has the
 * process — which is the whole of what this file adds.
 *
 * **The setting wins where there is one.** A person who chose a language chose it on this
 * machine, and a desktop set to something else is not a correction. The desktop is consulted
 * only for the tag that says *ask*.
 */
export function localeChoice(asked: string, desktop: string): string {
  return localeFor(asked.trim() === '' ? desktop : asked, LOCALE_TAGS)
}
