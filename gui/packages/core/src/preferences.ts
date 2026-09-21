import { LOCALE_TAGS } from './locales'
import { isRowOrder } from './portfolio'
import { isSessionLayout, isSessionNotes, isTheme, type Settings } from './settings'

/**
 * What the renderer may write into the settings file, and nothing past it (RG207).
 *
 * Two preferences were written by two bridge methods, `saveTheme` and `saveLocale`, and the
 * bridge said a third would be the moment to ask again. The answer is not `Partial<Settings>`:
 * that hands a page the roots and the ignore list, which decide what this app scans and are
 * chosen through a dialog the main process opens. It is this table — each writable field
 * beside the check a value has to pass — and one method over it.
 *
 * **The check is the reader's.** A value written here is read back by `readSettings` at the
 * next launch, so a validator looser than the reader's stores something the reader resets,
 * and that looks exactly like a choice that was never kept. `isTheme` is the same set the
 * reader uses; a locale is narrower than the reader's `string`, because a tag this build does
 * not ship reads back as the base language.
 *
 * **A preference is one row.** A field added to `Settings` that a person chooses from a screen
 * is a row here, a field in the reader and an entry in the catalogue — and the bridge, the
 * preload and the main process do not change.
 */

/** Which fields a preference write reaches: the table's keys, and so exactly its rows. */
export type PreferenceKey = keyof typeof PREFERENCES

/** A value checked for one key, typed as the settings field it lands in. */
type Check<K extends keyof Settings> = (value: unknown) => value is Settings[K]

function isShippedLocale(value: unknown): value is string {
  return typeof value === 'string' && LOCALE_TAGS.includes(value)
}

export const PREFERENCES = {
  theme: isTheme satisfies Check<'theme'>,
  locale: isShippedLocale satisfies Check<'locale'>,
  sessionNotes: isSessionNotes satisfies Check<'sessionNotes'>,
  portfolioOrder: isRowOrder satisfies Check<'portfolioOrder'>,
  // Each known card exactly once, which is stricter than the reader's repair (RG276).
  sessionLayout: isSessionLayout satisfies Check<'sessionLayout'>,
} as const

/** Whether a key the renderer named is one it may write. The renderer's word, so unknown. */
export function isPreferenceKey(key: unknown): key is PreferenceKey {
  return typeof key === 'string' && Object.hasOwn(PREFERENCES, key)
}

/**
 * The settings with one preference written, or null where the key or the value is refused.
 *
 * Every other field is carried as it was, which is what keeps a root somebody added by hand a
 * moment ago alive across a click on the ground.
 */
export function withPreference(settings: Settings, key: unknown, value: unknown): Settings | null {
  if (!isPreferenceKey(key)) return null
  if (!PREFERENCES[key](value)) return null
  return { ...settings, [key]: value }
}
