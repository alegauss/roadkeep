import { DEFAULT_LIMITS } from './limits'
import { isRowOrder, type RowOrder } from './portfolio'
import { DEFAULT_DEPTH, DEPTH_CEILING, NO_DEFAULT_ROOTS, type ScanRoot } from './roots'
import { DEFAULT_POLICY } from './scanning'
import { asRecord } from './reading'

/**
 * The one thing this app owns.
 *
 * Everything on screen is read from a repository except this: the roots, their depths, the
 * ignore set, the pool width, the theme, the locale, how a session draws its notes, where
 * its cards sit and the order the portfolio opens in. Small, versioned, validated on read.
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
 * **It holds no project data and no cached answer.** The project list is the catalogue's and
 * a remembered reading is its own record (RG251); the line between them and this file is
 * that those can be rebuilt by looking or by asking, and a choice cannot be rebuilt at all.
 *
 * Where the file lives needs an operating system, so that half is `shell`'s.
 */

/** What this build writes. A file claiming a higher number is not read. */
export const SETTINGS_VERSION = 1

/** Which ground the window paints. `system` follows the desktop. */
export type Theme = 'system' | 'light' | 'dark'

/**
 * Whether a session's stream draws its system notes one row each, or folds each run of them
 * into one counted row (RG208). `shown` is what every build before this one drew.
 */
export type SessionNotes = 'shown' | 'hidden'

/**
 * A card the session screen draws beside its stream (RG276), named after its grid's
 * `data-region` less the `session-` prefix. The stream is not one: it is the editor area and
 * stays in the middle, so no arrangement can move it or leave it out.
 */
export type SessionCard = 'handed' | 'moved' | 'files'

/** One of the two side bars a card sits in. */
export type SessionSide = 'left' | 'right'

/**
 * Where the session screen's cards sit (RG276): an ordered list for each side bar. A choice
 * nobody can rebuild by looking, which is what this file holds; the widths are not in it.
 */
export interface SessionLayout {
  readonly left: readonly SessionCard[]
  readonly right: readonly SessionCard[]
}

/** Every card this build draws, in the order the default arrangement lists them. */
export const SESSION_CARDS: readonly SessionCard[] = ['handed', 'moved', 'files']

/**
 * How wide each session side bar is drawn (RG279): its share of the row it and the stream
 * divide, in per cent, as its edge was last dragged to. `null` is the width every earlier build
 * drew, 18rem, which a side bar nobody dragged keeps. A side bar with no card keeps its share for
 * when one comes back to it.
 *
 * On disk and never in the browser's storage, which is neither this file nor one a person can
 * read — the library's own `autoSaveId` would put it there.
 */
export interface SessionSides {
  readonly left: number | null
  readonly right: number | null
}

/**
 * The narrowest and widest share a side bar is drawn at, in per cent: the panels' own bounds,
 * and so the reader's — two at the widest still leave the stream a fifth of the row.
 */
export const SIDE_SHARE = { min: 12, max: 40 } as const

export interface Settings {
  readonly version: number
  /** The folders to scan, and how far under each. The person's statement, never a scan's. */
  readonly roots: readonly ScanRoot[]
  /** Directory names a scan does not walk into. */
  readonly skip: readonly string[]
  /** How many engine calls may be in flight at once. */
  readonly width: number
  /**
   * How many projects a cold start reads at once (RG250), or zero for the machine's own
   * number — one per four cores, which only a process can count.
   *
   * Zero is a choice and not an absence, the way an empty `locale` is: a file that names no
   * number follows the machine it is on, and one that names a number means it.
   */
  readonly projectsAtOnce: number
  readonly theme: Theme
  /** A BCP-47 tag, or the empty string for whatever the desktop says. */
  readonly locale: string
  /** How a session's stream draws its system notes (RG208). */
  readonly sessionNotes: SessionNotes
  /**
   * The order the portfolio opens in (RG241): the choice alone, never the ranking it produced.
   * A list of paths ranked by open lines would be a copy of what `stats` printed, stale the
   * moment a line ships, in a file that holds only what somebody chose.
   */
  readonly portfolioOrder: RowOrder
  /** Where the session screen's side cards sit, and in what order (RG276). */
  readonly sessionLayout: SessionLayout
  /** How wide the session screen's side bars are drawn (RG279). */
  readonly sessionSides: SessionSides
}

export const DEFAULT_SETTINGS: Settings = {
  version: SETTINGS_VERSION,
  roots: NO_DEFAULT_ROOTS,
  skip: DEFAULT_POLICY.ignore,
  width: DEFAULT_LIMITS.width,
  projectsAtOnce: 0,
  theme: 'system',
  locale: '',
  // Every note drawn, as before there was a choice: an upgrade changes nothing on screen.
  sessionNotes: 'shown',
  // The record's order, as before there was a choice.
  portfolioOrder: 'record',
  // The grid `Session.tsx` drew before there was a choice: what was handed over on the left,
  // what moved and the files it touched on the right. A field arriving with a default is not a
  // new version, so `SETTINGS_VERSION` stays where it was.
  sessionLayout: { left: ['handed'], right: ['moved', 'files'] },
  // Neither side bar dragged: both at the 18rem every earlier build drew.
  sessionSides: { left: null, right: null },
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
  | 'projectsAtOnce'
  | 'theme'
  | 'locale'
  | 'sessionNotes'
  | 'portfolioOrder'
  | 'sessionLayout'
  | 'sessionSides'
  | 'sidesClamped'

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

const SESSION_NOTES = new Set<SessionNotes>(['shown', 'hidden'])

/**
 * Whether a value is a way of drawing system notes this build knows (RG208). Exported for the
 * reason `isTheme` is: the reader and the preference table have to accept the same set.
 */
export function isSessionNotes(value: unknown): value is SessionNotes {
  return typeof value === 'string' && SESSION_NOTES.has(value as SessionNotes)
}

const SIDES: readonly SessionSide[] = ['left', 'right']

/**
 * Whether a value names a card this build draws. Exported for the screen, where a dragged
 * card comes back as whatever id the drag library was handed.
 */
export function isSessionCard(value: unknown): value is SessionCard {
  return typeof value === 'string' && (SESSION_CARDS as readonly string[]).includes(value)
}

/**
 * Whether a value is an arrangement exactly as this build writes one (RG276): the two side
 * bars and nothing else, and each known card exactly once between them.
 *
 * Stricter than the reader on purpose. The reader repairs what it can, so a check as loose as
 * the reader would let a page store something the next launch quietly rewrites — and a choice
 * read back as a different one looks exactly like a choice that was never kept.
 */
export function isSessionLayout(value: unknown): value is SessionLayout {
  const record = asRecord(value)
  if (record === null || Object.keys(record).length !== SIDES.length) return false
  const cards: unknown[] = []
  for (const side of SIDES) {
    const list = record[side]
    if (!Array.isArray(list)) return false
    cards.push(...(list as unknown[]))
  }
  return (
    cards.length === SESSION_CARDS.length &&
    cards.every(isSessionCard) &&
    new Set(cards).size === SESSION_CARDS.length
  )
}

/**
 * The arrangement a file holds, repaired card by card, and the loss where it cannot be used.
 *
 * Only a value that is not two lists is a loss. An id this build does not draw is dropped, a
 * repeated one keeps its first place, and a card the file never names goes where the default
 * puts it — which is how a card a later build adds still appears in a file written before it,
 * and why none of the three is a notice: nothing the person chose was lost.
 */
function layoutIn(raw: unknown): readonly [SessionLayout, Reset | null] {
  const fallback = DEFAULT_SETTINGS.sessionLayout
  if (raw === undefined) return [fallback, null]
  const record = asRecord(raw)
  const left: unknown = record?.['left']
  const right: unknown = record?.['right']
  if (!Array.isArray(left) || !Array.isArray(right)) {
    return [fallback, { lost: 'sessionLayout' }]
  }

  const seen = new Set<SessionCard>()
  const kept = (list: readonly unknown[]): SessionCard[] =>
    list.filter((card): card is SessionCard => {
      if (!isSessionCard(card) || seen.has(card)) return false
      seen.add(card)
      return true
    })
  const sides: Record<SessionSide, SessionCard[]> = { left: kept(left), right: kept(right) }

  for (const side of SIDES) {
    fallback[side].forEach((card, index) => {
      if (!seen.has(card)) sides[side].splice(Math.min(index, sides[side].length), 0, card)
    })
  }
  return [sides, null]
}

/**
 * The arrangement with one card moved to a side bar, at an index in that side bar as it reads
 * once the card has left its old place (RG276) — the index a sortable list reports for a drop.
 *
 * One rule for every way a card moves: a drag, a keyboard, a menu entry. An index past either
 * end lands the card at that end.
 */
export function moveCard(
  layout: SessionLayout,
  card: SessionCard,
  side: SessionSide,
  index: number,
): SessionLayout {
  const without = {
    left: layout.left.filter((one) => one !== card),
    right: layout.right.filter((one) => one !== card),
  }
  const target = without[side]
  target.splice(Math.max(0, Math.min(index, target.length)), 0, card)
  return without
}

function clampShare(share: number): number {
  return Math.min(Math.max(share, SIDE_SHARE.min), SIDE_SHARE.max)
}

/**
 * A side bar's share as it is kept (RG279): to a tenth of a per cent, and within the bounds.
 * The drag library answers to the fifteenth decimal, which is noise in a file a person reads.
 */
export function sideShare(share: number): number {
  return clampShare(Math.round(share * 10) / 10)
}

function isShareOrUnset(value: unknown): value is number | null {
  return value === null || (typeof value === 'number' && Number.isFinite(value))
}

/**
 * Whether a value is a pair of side bar widths exactly as this build writes one (RG279): the two
 * sides and nothing else, each unset or a share within the bounds — so nothing a page stores is
 * something the reader would clamp.
 */
export function isSessionSides(value: unknown): value is SessionSides {
  const record = asRecord(value)
  if (record === null || Object.keys(record).length !== SIDES.length) return false
  return SIDES.every((side) => {
    const share = record[side]
    return isShareOrUnset(share) && (share === null || clampShare(share) === share)
  })
}

/**
 * The side bar widths a file holds (RG279). A share outside the bounds is held to the nearest
 * one and said, since the person dragged something the screen will not draw; a value that is not
 * two shares is no widths at all, and both go back to where they started.
 */
function sidesIn(raw: unknown): readonly [SessionSides, Reset | null] {
  const fallback = DEFAULT_SETTINGS.sessionSides
  if (raw === undefined) return [fallback, null]
  const record = asRecord(raw)
  if (record === null) return [fallback, { lost: 'sessionSides' }]
  const left = record['left'] ?? null
  const right = record['right'] ?? null
  if (!isShareOrUnset(left) || !isShareOrUnset(right)) return [fallback, { lost: 'sessionSides' }]

  const held = {
    left: left === null ? null : clampShare(left),
    right: right === null ? null : clampShare(right),
  }
  const clamped = held.left !== left || held.right !== right
  return [
    held,
    clamped ? { lost: 'sidesClamped', fields: { min: SIDE_SHARE.min, max: SIDE_SHARE.max } } : null,
  ]
}

/**
 * A place a card can be moved to (RG277): a side bar, and an index in it counted as `moveCard`
 * counts one, once the card has left — so a place is exactly the two arguments a move takes.
 */
export interface CardPlace {
  readonly side: SessionSide
  readonly index: number
}

/** Where a card sits now, as a place, so moving it there is no move at all. */
export function placeOf(layout: SessionLayout, card: SessionCard): CardPlace | null {
  for (const side of SIDES) {
    const index = layout[side].indexOf(card)
    if (index !== -1) return { side, index }
  }
  return null
}

/** Whether two arrangements put every card in the same place. */
export function sameLayout(one: SessionLayout, other: SessionLayout): boolean {
  return SIDES.every(
    (side) =>
      one[side].length === other[side].length &&
      one[side].every((card, index) => other[side][index] === card),
  )
}

/** One arrow key, as a direction a card being moved is sent in. */
export type CardStep = 'up' | 'down' | 'left' | 'right'

/**
 * The place one arrow key sends a card to, from the place it would land now (RG277).
 *
 * Up and down move it one place along its side bar and stop at either end. Left and right send
 * it to that side bar at the same place, or at the end where that side bar is shorter — the
 * way a caret keeps its column moving between lines of different lengths.
 */
export function steppedPlace(
  layout: SessionLayout,
  card: SessionCard,
  place: CardPlace,
  step: CardStep,
): CardPlace {
  const room = (side: SessionSide): number => layout[side].filter((one) => one !== card).length
  if (step === 'up') return { side: place.side, index: Math.max(0, place.index - 1) }
  if (step === 'down') {
    return { side: place.side, index: Math.min(room(place.side), place.index + 1) }
  }
  return { side: step, index: Math.min(place.index, room(step)) }
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
  const [projectsAtOnce, saidOfProjects] = field(
    file['projectsAtOnce'],
    (value) => typeof value === 'number' && Number.isInteger(value) && value >= 0,
    DEFAULT_SETTINGS.projectsAtOnce,
    { lost: 'projectsAtOnce', fields: { projects: DEFAULT_SETTINGS.projectsAtOnce } },
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
  const [sessionNotes, saidOfNotes] = field<SessionNotes>(
    file['sessionNotes'],
    isSessionNotes,
    DEFAULT_SETTINGS.sessionNotes,
    { lost: 'sessionNotes' },
  )
  const [portfolioOrder, saidOfOrder] = field<RowOrder>(
    file['portfolioOrder'],
    isRowOrder,
    DEFAULT_SETTINGS.portfolioOrder,
    { lost: 'portfolioOrder' },
  )
  const [sessionLayout, saidOfLayout] = layoutIn(file['sessionLayout'])
  const [sessionSides, saidOfSides] = sidesIn(file['sessionSides'])

  return {
    settings: {
      version: SETTINGS_VERSION,
      roots,
      skip,
      width,
      projectsAtOnce,
      theme,
      locale,
      sessionNotes,
      portfolioOrder,
      sessionLayout,
      sessionSides,
    },
    reset: [
      version.said,
      saidOfRoots,
      saidOfSkip,
      saidOfWidth,
      saidOfProjects,
      saidOfTheme,
      saidOfLocale,
      saidOfNotes,
      saidOfOrder,
      saidOfLayout,
      saidOfSides,
    ].filter((said): said is Reset => said !== null),
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
