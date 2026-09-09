import { DEFAULT_LIMITS } from './limits'
import { DEFAULT_DEPTH, DEPTH_CEILING, NO_DEFAULT_ROOTS, type ScanRoot } from './roots'
import { DEFAULT_POLICY } from './scanning'

/**
 * The one thing this app owns.
 *
 * Everything on screen is read from a repository except this: the roots, their depths, the
 * ignore set, the pool width, the theme and the locale. Small, versioned, validated on
 * read.
 *
 * **A bad file resets and says so, rather than taking the window down** — and field by
 * field: a pool width typed as a word should not cost somebody the roots they spent a
 * minute naming. Each recovery is a sentence a screen can show, because a file silently
 * replaced is one whose loss the person discovers later by noticing the list is empty.
 *
 * **The version is read first.** A file from a future build is not guessed at: its fields
 * might mean something else, so it is kept, defaults are used, and the version found is
 * named.
 *
 * **It holds no project data and no cached answer**, which is `No store of its own`
 * restated as a file format. The project list is the catalogue's, and the line between them
 * is that one can be rebuilt by looking and the other cannot be rebuilt at all.
 *
 * Where the file lives needs an operating system, so that half is `shell`'s.
 */

/** What this build writes. A file claiming a higher number is not read. */
export const SETTINGS_VERSION = 1

/** Which ground the window paints. `system` follows the desktop. */
export type Theme = 'system' | 'light' | 'dark'

export interface Settings {
  readonly version: number
  /** The folders to scan, and how far under each. The person's statement, never a scan's. */
  readonly roots: readonly ScanRoot[]
  /** Directory names a scan does not walk into. */
  readonly skip: readonly string[]
  /** How many engine calls may be in flight at once. */
  readonly width: number
  readonly theme: Theme
  /** A BCP-47 tag, or the empty string for whatever the desktop says. */
  readonly locale: string
}

export const DEFAULT_SETTINGS: Settings = {
  version: SETTINGS_VERSION,
  roots: NO_DEFAULT_ROOTS,
  skip: DEFAULT_POLICY.ignore,
  width: DEFAULT_LIMITS.width,
  theme: 'system',
  locale: '',
}

export interface SettingsRead {
  readonly settings: Settings
  /**
   * What could not be used, each said as a sentence. Empty is a clean read.
   *
   * Sentences rather than codes because these are shown: somebody whose roots were dropped
   * needs to know that, and a code would be a second thing to look up.
   */
  readonly reset: readonly string[]
}

const THEMES = new Set<Theme>(['system', 'light', 'dark'])

/**
 * Whether a value is a ground setting this build knows.
 *
 * Exported because two callers have to agree on it: reading the file, and the main process
 * taking a theme the renderer named. A second spelling of the same set is a build that
 * accepts a value its own reader would reset.
 */
export function isTheme(value: unknown): value is Theme {
  return typeof value === 'string' && THEMES.has(value as Theme)
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null
}

/** One root, or null where it is not one. A bad entry is dropped, not the whole list. */
function rootOf(value: unknown): ScanRoot | null {
  const record = asRecord(value)
  if (record === null) return null
  const path = record['path']
  if (typeof path !== 'string' || path === '') return null

  const depth = record['depth']
  const whole = typeof depth === 'number' && Number.isInteger(depth) ? depth : DEFAULT_DEPTH
  return { path, depth: Math.min(Math.max(whole, 0), DEPTH_CEILING) }
}

/**
 * One field: the value where it can be used, the default where it cannot, and the sentence
 * saying which.
 *
 * A field absent from the file is not a loss — it is a file written by a build that had
 * fewer settings, or by a person who only set what they cared about — so `undefined` takes
 * the default and says nothing.
 */
function field<T>(
  raw: unknown,
  usable: (value: unknown) => boolean,
  fallback: T,
  lost: string,
): readonly [T, string | null] {
  if (raw === undefined) return [fallback, null]
  return usable(raw) ? [raw as T, null] : [fallback, lost]
}

/** The roots, keeping the ones that read and counting the ones that did not. */
function rootsIn(raw: unknown): readonly [readonly ScanRoot[], string | null] {
  if (raw === undefined) return [DEFAULT_SETTINGS.roots, null]
  if (!Array.isArray(raw))
    return [DEFAULT_SETTINGS.roots, 'the roots were not a list, so none were read']

  const kept = raw.map(rootOf).filter((root): root is ScanRoot => root !== null)
  const dropped = raw.length - kept.length
  return [
    kept,
    dropped === 0 ? null : `${String(dropped)} root(s) could not be read and were dropped`,
  ]
}

/**
 * What the file says about its version, or the reason it cannot be read at all.
 *
 * A version above this build's is the one case that stops everything: the fields might
 * mean something else, so the file is left alone and defaults are used.
 */
function versionIn(raw: unknown): readonly [string | null, boolean] {
  if (typeof raw !== 'number' || !Number.isInteger(raw)) {
    return ['the settings file names no version, so it is read as this build writes them', false]
  }
  if (raw > SETTINGS_VERSION) {
    return [
      `the settings file is version ${String(raw)} and this build reads ${String(
        SETTINGS_VERSION,
      )}, so defaults are used and the file is left alone`,
      true,
    ]
  }
  return [null, false]
}

/**
 * Read a settings file into settings and a list of what it lost.
 *
 * Takes the parsed value rather than the text: parsing is the caller's, because a file that
 * is not JSON at all and a file that is JSON of the wrong shape are two different failures
 * and only one of them belongs here.
 */
export function readSettings(source: unknown): SettingsRead {
  const file = asRecord(source)
  if (file === null) {
    return {
      settings: DEFAULT_SETTINGS,
      reset: ['the settings file is not an object, so every setting is back to its default'],
    }
  }

  const [saidOfVersion, unreadable] = versionIn(file['version'])
  if (unreadable) return { settings: DEFAULT_SETTINGS, reset: [saidOfVersion ?? ''] }

  const [roots, saidOfRoots] = rootsIn(file['roots'])
  const [skip, saidOfSkip] = field<readonly string[]>(
    file['skip'],
    (value) => Array.isArray(value) && value.every((one) => typeof one === 'string'),
    DEFAULT_SETTINGS.skip,
    'the skip list was not a list of names, so the default one is used',
  )
  const [width, saidOfWidth] = field(
    file['width'],
    (value) => typeof value === 'number' && Number.isInteger(value) && value > 0,
    DEFAULT_SETTINGS.width,
    `the pool width was not a whole number, so it is back to ${String(DEFAULT_SETTINGS.width)}`,
  )
  const [theme, saidOfTheme] = field<Theme>(
    file['theme'],
    isTheme,
    DEFAULT_SETTINGS.theme,
    `the theme was not one this build knows, so it is back to ${DEFAULT_SETTINGS.theme}`,
  )
  const [locale, saidOfLocale] = field(
    file['locale'],
    (value) => typeof value === 'string',
    DEFAULT_SETTINGS.locale,
    'the locale was not a string, so the desktop decides',
  )

  return {
    settings: { version: SETTINGS_VERSION, roots, skip, width, theme, locale },
    reset: [saidOfVersion, saidOfRoots, saidOfSkip, saidOfWidth, saidOfTheme, saidOfLocale].filter(
      (said): said is string => said !== null,
    ),
  }
}

/**
 * The file to write, as text.
 *
 * Indented, because a person editing it by hand is a supported way to use it — and a file
 * meant to be edited is one a diff has to be readable for.
 */
export function settingsText(settings: Settings): string {
  return `${JSON.stringify({ ...settings, version: SETTINGS_VERSION }, null, 2)}\n`
}

/** Whether anything was lost reading it, which is what a screen puts a notice on. */
export function wasReset(read: SettingsRead): boolean {
  return read.reset.length > 0
}
