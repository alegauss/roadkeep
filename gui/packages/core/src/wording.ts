/**
 * Every string this app says in its own voice, in one place.
 *
 * English is the base and **English is the type**: `MessageKey` is this object's own keys,
 * so a screen cannot ask for a string nobody wrote, and a key no screen asks for shows up
 * as dead the way an unused export does.
 *
 * A second locale is a `Partial` of the same shape beside it. That is deliberate — a
 * half-translated locale is the normal state of a translation, not a broken one — and the
 * fallback is **per key**, so a missing entry shows the English sentence rather than the
 * identifier. A locale file is never a reason for a screen to show `portfolio.footnote`.
 *
 * **Two things are never in here.** What a payload printed is the project's own prose, in
 * whatever language its author wrote it, and translating it would be this app rewriting
 * somebody's backlog. A refusal is the engine's words, quoted. What is translated is this
 * app's own voice and nothing else.
 *
 * The word *catalogue* is already spoken for by the project record in `catalogue.ts`, which
 * is why this file is not called that. Two catalogues in one app is one too many names.
 */

import type { Lost, Theme } from './settings'
import { keysOf } from './reading'

/** Named holes, filled by name. Positional would be a promise about word order. */
export type Fill = Readonly<Record<string, string | number>>

/**
 * The base wording. Values may carry `{name}` holes; nothing else is special.
 *
 * Keys read from the general to the particular, so one screen's strings sort together and
 * an unused one is visible.
 */
export const EN = {
  'app.name': 'roadkeep',

  'transport.absent': 'no bridge - running as a plain browser page',

  'portfolio.kicker': 'Portfolio',
  'portfolio.title': '{count} projects on this machine',
  'portfolio.title.unknown': 'Projects on this machine',
  'portfolio.tally': '{read} read · {pending} still reading · {unreadable} unreadable',
  'portfolio.progress': '{stage}: {done} of {total}',
  'portfolio.stage.counting': 'counting each backlog',
  'portfolio.stage.next': 'asking for each next line',
  'portfolio.asking': 'Looking under the roots the settings name.',
  'portfolio.failed': 'The bridge did not say which projects there are: {reason}',
  'portfolio.none': 'No project was found under the roots the settings name.',
  'portfolio.none.hint':
    'A folder holding a roadkeep.toml under one of those roots is listed here the next time the window asks.',
  'portfolio.filter.all': 'All {count}',
  'portfolio.filter.drifted': 'Gate drifted {count}',
  'portfolio.filter.disagrees': 'Engine disagrees {count}',
  'portfolio.filter.unreadable': 'Unreadable {count}',
  'portfolio.filter.label': 'Narrow the list',
  'portfolio.order': "order: the record's",
  'portfolio.column.project': 'Project',
  'portfolio.column.backlog': 'Backlog',
  'portfolio.column.next': 'Next ready line',
  'portfolio.column.gate': 'Gate',
  'portfolio.column.engine': 'Engine',
  'portfolio.worktree': 'worktree',
  'portfolio.pending': 'still reading',
  'portfolio.open': '{count} open',
  'portfolio.startable': '{startable} startable · {waiting} waiting',
  'portfolio.uncounted': '{count} not counted',
  'portfolio.tier': 'tier: {tier}',
  'portfolio.next.none': 'nothing ready · {blocked} blocked',
  'portfolio.next.missing': 'the next line did not arrive',
  'portfolio.gate.unknown': 'unknown',
  'portfolio.gate.clean': 'clean',
  'portfolio.gate.drifted': 'drifted',
  'portfolio.gate.never': 'never run here',
  'portfolio.gate.findings': '{count} findings',
  'portfolio.gate.stale': 'stale',
  'portfolio.engine.modified': 'working tree',
  'portfolio.unreadable': 'unreadable',
  'portfolio.tried': 'what was tried',
  'portfolio.kept': 'still on the list',
  'portfolio.footnote':
    'Every number on this screen is one a verb printed. Nothing is summed across projects.',

  'project.back': 'Portfolio',
  'project.open': 'Open {name}',
  'project.counts':
    '{open} open · {startable} startable · {waiting} waiting on a requirement · {uncounted} uncounted',
  'project.opening': 'Opening the project.',
  'project.refused': 'This project did not open: {reason}',
  'project.roles': 'Governed files',
  'project.blocks': 'Blocks',
  'project.block.finished': 'finished',
  'project.filter.marker': 'marker',
  'project.filter.requirement': 'requirement',
  'project.filter.note': 'readiness is what deps answered for each line, never worked out here',
  'project.listing': 'Reading the lines.',
  'project.none': 'No line answers this narrowing.',
  'project.design.written': 'design written · §{ref}',
  'project.design.none': 'no design yet',
  'project.deps.none': 'no deps',
  'project.readiness.asking': 'asking',
  'project.waiting': 'waiting on {ids}',
  'project.cycle': 'in a cycle with {ids}',
  'project.unheld': 'marked, unheld',
  'project.unheld.why': 'the marker says started; the claim registry names nobody',
  'project.held': 'held by {by}',

  'roots.label': 'Roots',
  'roots.add': 'Add a root',
  'roots.rescan': 'Rescan roots',
  'roots.choose': 'Choose a folder to look under',
  'roots.depth': '{depth} levels deep',
  'roots.missing': 'missing',
  'roots.remove': 'Stop looking under {path}',
  'roots.none': 'No root is named yet, so nothing is walked.',
  'roots.none.hint': 'Add a root to name a folder this window may look under.',
  'roots.unsaved': 'The roots could not be saved: {reason}',

  'settings.reset': 'Some settings could not be read, so they are back to their defaults.',
  'settings.unsaved': 'That choice could not be saved, so the next launch will not have it.',

  'settings.lost.unparsable': '{file} is not readable as JSON, so it is left alone',
  'settings.lost.file':
    'the settings file is not an object, so every setting is back to its default',
  'settings.lost.unversioned':
    'the settings file names no version, so it is read as this build writes them',
  'settings.lost.version':
    'the settings file is version {found} and this build reads {reads}, so the file is left alone',
  'settings.lost.roots': 'the roots were not a list, so none were read',
  'settings.lost.dropped': '{count} root(s) could not be read and were dropped',
  'settings.lost.skip': 'the skip list was not a list of names, so the default one is used',
  'settings.lost.width': 'the pool width was not a whole number, so it is back to {width}',
  'settings.lost.theme': 'the theme was not one this build knows, so it is back to {theme}',
  'settings.lost.locale': 'the locale was not a string, so the desktop decides',

  'shell.home': 'Home',
  'shell.palette': 'Find a line in every backlog',
  'shell.shortcuts': 'Keyboard shortcuts',
  'shell.notices': 'Notifications',

  'menu.help': 'Help',
  'update.check': 'Check for updates…',
  'update.title': 'Updates',
  'update.newer': 'You are on {current}. The newest published is {latest}.',
  'update.current': 'You are on {current}, which is the newest published.',
  'update.none': 'You are on {current}. No release has been published yet.',
  'update.failed': 'You are on {current}. The check did not reach an answer: {reason}',
  'update.open': 'Open the release page',
  'update.close': 'Close',

  'ground.system': 'ground: following the desktop',
  'ground.light': 'ground: light',
  'ground.dark': 'ground: dark',
  'ground.action': 'Change the ground',
} as const

/** What a screen may ask for. Anything else is a string somebody typed into a component. */
export type MessageKey = keyof typeof EN

/**
 * What the ground control says it is set to.
 *
 * `system` has wording of its own rather than borrowing whichever ground it resolved to:
 * *following the desktop* and *light* look identical on a machine set to light, and the
 * difference is the whole reason `system` is a setting.
 */
export const THEME_TEXT: Readonly<Record<Theme, MessageKey>> = {
  system: 'ground.system',
  light: 'ground.light',
  dark: 'ground.dark',
}

/**
 * What a settings file lost, said in this app's own voice (RG123).
 *
 * The same arrangement as the theme and for a sharper reason: these sentences used to be
 * composed where the file is read, which is `core` for nine of them and `shell` for the
 * tenth, and neither has a locale. RG115 draws them under a translated frame, so a window
 * in Portuguese said the frame in Portuguese and the detail in English.
 *
 * Spelled out rather than built from the code, so a loss added without a sentence fails to
 * compile — and the values carry the holes the reader fills, which is why the reader hands
 * back fields and not prose.
 */
export const RESET_TEXT: Readonly<Record<Lost, MessageKey>> = {
  unparsable: 'settings.lost.unparsable',
  file: 'settings.lost.file',
  unversioned: 'settings.lost.unversioned',
  version: 'settings.lost.version',
  roots: 'settings.lost.roots',
  dropped: 'settings.lost.dropped',
  skip: 'settings.lost.skip',
  width: 'settings.lost.width',
  theme: 'settings.lost.theme',
  locale: 'settings.lost.locale',
}

/** A translation. Partial because a translation in progress is still worth shipping. */
export type Wording = Partial<Readonly<Record<MessageKey, string>>>

/** The base, widened: every key present, which is what makes the fallback total. */
export const BASE: Readonly<Record<MessageKey, string>> = EN

/** The tag the base is written in. */
export const BASE_LOCALE = 'en'

/** Every key there is, in the order they were written. */
export function keys(): readonly MessageKey[] {
  return keysOf(BASE)
}

/**
 * Fill a value's named holes.
 *
 * A hole nobody filled is left as it was written rather than blanked: a visible `{count}`
 * is a defect somebody reports, and a gap where a number should be is one nobody notices.
 */
export function fill(value: string, values: Fill = {}): string {
  return value.replace(/\{(\w+)\}/g, (whole, name: string) => {
    const given = values[name]
    return given === undefined ? whole : String(given)
  })
}

/** What a screen calls to get a string. */
export type Translate = (key: MessageKey, values?: Fill) => string

/**
 * Build the lookup for one locale.
 *
 * @param over the translation, covering any part of the base. Absent keys fall through to
 *   English one at a time, which is what makes a partial translation usable.
 */
export function translator(over: Wording = {}): Translate {
  return (key, values) => fill(over[key] ?? BASE[key], values)
}

/**
 * Choose which locale answers, from what the settings asked for.
 *
 * A tag is tried whole and then by its language — `pt-BR` before `pt` — because a
 * translation is usually written for the language and specialised later, if ever. An empty
 * request means the desktop's own tag, which the caller passes in: nothing here reads an
 * environment, because `core` has none to read.
 */
export function localeFor(asked: string, available: readonly string[]): string {
  const wanted = asked.trim().toLowerCase()
  if (wanted === '') return BASE_LOCALE

  const language = wanted.split('-')[0] ?? wanted
  const found =
    available.find((one) => one.toLowerCase() === wanted) ??
    available.find((one) => one.toLowerCase() === language) ??
    available.find((one) => (one.toLowerCase().split('-')[0] ?? '') === language)

  return found ?? BASE_LOCALE
}

/**
 * Which keys a translation has not covered yet, in the base's own order.
 *
 * A report and never a refusal: a locale is allowed to be incomplete, and what the person
 * translating it needs is the list of what is left.
 */
export function untranslated(over: Wording): readonly MessageKey[] {
  return keys().filter((key) => over[key] === undefined)
}

/** Keys a translation carries that the base no longer has — a string that outlived its screen. */
export function stale(over: Wording): readonly string[] {
  return Object.keys(over).filter((key) => !(key in BASE))
}

/**
 * The other half of the wording, and the same two questions asked of it (RG125).
 *
 * This app's strings reach the screen two ways: through the catalogue above, and through an
 * i18next bundle the design system's own components resolve — the nav labels, and the name
 * the language menu gives itself. The second half is nested rather than flat, is written
 * once per language rather than as a `Partial` of a base, and had nothing comparing the
 * copies at all: a key added to `en` and missed in `pt` drew English inside a Portuguese
 * window, and RG51's run could not see it, wrapping the base locale being the language it
 * renders in.
 *
 * **The rules are the catalogue's, not new ones.** A path the base names and a translation
 * does not is `untranslated`; a path a translation names and the base no longer does is
 * `stale`; and a value identical in both is the case `app.name` already settles — a name is
 * the same word in either language, and everything else identical is a translation nobody
 * wrote. All three come off one walk, because the answer wanted is all three at once.
 *
 * Here rather than beside the object it is asked about, for the reason every rule in this
 * package is: comparing two trees of strings needs no DOM and no i18next.
 */

/** A bundle as i18next takes one: a tree whose leaves are strings. */
export interface Bundle {
  readonly [key: string]: string | Bundle
}

export interface BundleGaps {
  /** Paths the base names and this translation does not. */
  readonly untranslated: readonly string[]
  /** Paths this translation names that the base does not. */
  readonly stale: readonly string[]
  /** Paths both name with the same string. A name, or a translation nobody wrote. */
  readonly identical: readonly string[]
}

/** Every path to a string in a bundle, dotted, in the order they were written. */
export function bundlePaths(bundle: Bundle, under = ''): readonly string[] {
  return Object.entries(bundle).flatMap(([key, value]) => {
    const path = under === '' ? key : `${under}.${key}`
    return typeof value === 'string' ? [path] : bundlePaths(value, path)
  })
}

/** What a bundle says at a dotted path, or `undefined` where it says nothing there. */
export function bundleSays(bundle: Bundle, path: string): string | undefined {
  let at: string | Bundle | undefined = bundle
  for (const step of path.split('.')) {
    if (at === undefined || typeof at === 'string') return undefined
    at = at[step]
  }
  return typeof at === 'string' ? at : undefined
}

/** One translation against the base it is a translation of. A report, never a refusal. */
export function bundleGaps(base: Bundle, over: Bundle): BundleGaps {
  const mine = bundlePaths(base)
  const theirs = bundlePaths(over)

  return {
    untranslated: mine.filter((path) => bundleSays(over, path) === undefined),
    stale: theirs.filter((path) => bundleSays(base, path) === undefined),
    identical: mine.filter((path) => bundleSays(over, path) === bundleSays(base, path)),
  }
}

/**
 * A locale nobody speaks, which is what proves the screens read from here.
 *
 * Every value is wrapped and every hole is kept, so rendering under it leaves anything
 * unwrapped on screen visible as a string written into a component instead of into this
 * file. A test sees that on the run after somebody types it, rather than on the day a
 * second locale is added.
 */
export const PSEUDO_OPEN = '⟦'
export const PSEUDO_CLOSE = '⟧'
export const PSEUDO_LOCALE = 'zz'

export function pseudo(): Wording {
  const out: Record<string, string> = {}
  for (const key of keys()) out[key] = `${PSEUDO_OPEN}${BASE[key]}${PSEUDO_CLOSE}`
  return out
}

/** Whether a string on screen came through the pseudo-locale. */
export function isPseudo(text: string): boolean {
  return text.includes(PSEUDO_OPEN) && text.includes(PSEUDO_CLOSE)
}
