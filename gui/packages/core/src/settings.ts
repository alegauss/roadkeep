import { DEFAULT_LIMITS } from './limits'
import { DEFAULT_DEPTH, DEPTH_CEILING, NO_DEFAULT_ROOTS, type ScanRoot } from './roots'
import { DEFAULT_POLICY } from './scanning'
import { asRecord } from './reading'

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

/**
 * What a settings file can lose, as a code rather than a sentence (RG123).
 *
 * These were English prose composed here, which put half of every notice outside the
 * catalogue: RG115 shows them under a translated frame, so a window in Portuguese said the
 * frame in Portuguese and the detail in English. Each carries an interpolated value — a
 * count, a version, a default — which is why they are not ten more `MessageKey`s used
 * directly but a code and its fields, resolved through `RESET_TEXT` the way a theme is.
 *
 * `unparsable` is the one this file does not raise: a file that is not JSON at all is a
 * different failure from one of the wrong shape, and only the second is `core`'s. It is
 * named here because the sentence belongs to the same notice and the same catalogue.
 */
export type Lost =
  | 'unparsable'
  | 'file'
  | 'unversioned'
  | 'version'
  | 'roots'
  | 'dropped'
  | 'skip'
  | 'width'
  | 'theme'
  | 'locale'

export interface Reset {
  readonly lost: Lost
  /**
   * The values its sentence names, by hole. Absent where it names none, rather than an
   * empty object: a sentence with no holes is the ordinary case, and `fill` leaves any hole
   * nobody filled visible.
   */
  readonly fields?: Readonly<Record<string, string | number>>
}

export interface SettingsRead {
  readonly settings: Settings
  /**
   * What could not be used, each as a code a screen says in its own language. Empty is a
   * clean read.
   */
  readonly reset: readonly Reset[]
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
  lost: Reset,
): readonly [T, Reset | null] {
  if (raw === undefined) return [fallback, null]
  return usable(raw) ? [raw as T, null] : [fallback, lost]
}

/** The roots, keeping the ones that read and counting the ones that did not. */
function rootsIn(raw: unknown): readonly [readonly ScanRoot[], Reset | null] {
  if (raw === undefined) return [DEFAULT_SETTINGS.roots, null]
  if (!Array.isArray(raw)) return [DEFAULT_SETTINGS.roots, { lost: 'roots' }]

  const kept = raw.map(rootOf).filter((root): root is ScanRoot => root !== null)
  const dropped = raw.length - kept.length
  return [kept, dropped === 0 ? null : { lost: 'dropped', fields: { count: dropped } }]
}

/**
 * What the file says about its version, or the reason it cannot be read at all.
 *
 * A version above this build's is the one case that stops everything: the fields might
 * mean something else, so the file is left alone and defaults are used. Said as two shapes
 * rather than as a flag beside a nullable, so the caller cannot reach the stop without the
 * sentence that explains it.
 */
type Versioned =
  /** Usable, with a note where the version itself could not be read. */
  | { readonly kind: 'read'; readonly said: Reset | null }
  /** Written by a build that reads more than this one. Nothing else in it is read. */
  | { readonly kind: 'ahead'; readonly said: Reset }

function versionIn(raw: unknown): Versioned {
  if (typeof raw !== 'number' || !Number.isInteger(raw)) {
    return { kind: 'read', said: { lost: 'unversioned' } }
  }
  if (raw > SETTINGS_VERSION) {
    return {
      kind: 'ahead',
      said: { lost: 'version', fields: { found: raw, reads: SETTINGS_VERSION } },
    }
  }
  return { kind: 'read', said: null }
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
    return { settings: DEFAULT_SETTINGS, reset: [{ lost: 'file' }] }
  }

  const version = versionIn(file['version'])
  if (version.kind === 'ahead') return { settings: DEFAULT_SETTINGS, reset: [version.said] }

  const [roots, saidOfRoots] = rootsIn(file['roots'])
  const [skip, saidOfSkip] = field<readonly string[]>(
    file['skip'],
    (value) => Array.isArray(value) && value.every((one) => typeof one === 'string'),
    DEFAULT_SETTINGS.skip,
    { lost: 'skip' },
  )
  const [width, saidOfWidth] = field(
    file['width'],
    (value) => typeof value === 'number' && Number.isInteger(value) && value > 0,
    DEFAULT_SETTINGS.width,
    { lost: 'width', fields: { width: DEFAULT_SETTINGS.width } },
  )
  const [theme, saidOfTheme] = field<Theme>(file['theme'], isTheme, DEFAULT_SETTINGS.theme, {
    lost: 'theme',
    fields: { theme: DEFAULT_SETTINGS.theme },
  })
  const [locale, saidOfLocale] = field(
    file['locale'],
    (value) => typeof value === 'string',
    DEFAULT_SETTINGS.locale,
    { lost: 'locale' },
  )

  return {
    settings: { version: SETTINGS_VERSION, roots, skip, width, theme, locale },
    reset: [version.said, saidOfRoots, saidOfSkip, saidOfWidth, saidOfTheme, saidOfLocale].filter(
      (said): said is Reset => said !== null,
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
