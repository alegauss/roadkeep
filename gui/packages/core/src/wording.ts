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
 * identifier. A locale file is never a reason for a screen to show `app.tagline`.
 *
 * **Two things are never in here.** What a payload printed is the project's own prose, in
 * whatever language its author wrote it, and translating it would be this app rewriting
 * somebody's backlog. A refusal is the engine's words, quoted. What is translated is this
 * app's own voice and nothing else.
 *
 * The word *catalogue* is already spoken for by the project record in `catalogue.ts`, which
 * is why this file is not called that. Two catalogues in one app is one too many names.
 */

import type { PackageName } from './packages'
import type { Theme } from './settings'

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
  'app.tagline': 'The window opens and the three packages are wired. No backlog is read yet.',

  'transport.asking': 'asking the bridge',
  'transport.absent': 'no bridge - running as a plain browser page',
  'transport.ipc': 'bridged over IPC',
  'transport.http': 'bridged over HTTP',

  'shell.home': 'Home',
  'shell.palette': 'Find a line in every backlog',
  'shell.shortcuts': 'Keyboard shortcuts',

  'ground.system': 'ground: following the desktop',
  'ground.light': 'ground: light',
  'ground.dark': 'ground: dark',
  'ground.action': 'Change the ground',

  'packages.core':
    'The transport interface, the verb table and the payload shapes. No Electron, no React.',
  'packages.ui':
    'React over Tailwind. Receives payloads and renders them, and knows no path and no process.',
  'packages.shell': 'The Electron main process. It spawns, it watches files, it holds settings.',
} as const

/** What a screen may ask for. Anything else is a string somebody typed into a component. */
export type MessageKey = keyof typeof EN

/**
 * Which string says what a package is for.
 *
 * Spelled out rather than built from the name, so a package added without a sentence fails
 * to compile instead of asking for a key nobody wrote.
 */
export const PACKAGE_TEXT: Readonly<Record<PackageName, MessageKey>> = {
  core: 'packages.core',
  ui: 'packages.ui',
  shell: 'packages.shell',
}

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

/** A translation. Partial because a translation in progress is still worth shipping. */
export type Wording = Partial<Readonly<Record<MessageKey, string>>>

/** The base, widened: every key present, which is what makes the fallback total. */
export const BASE: Readonly<Record<MessageKey, string>> = EN

/** The tag the base is written in. */
export const BASE_LOCALE = 'en'

/** Every key there is, in the order they were written. */
export function keys(): readonly MessageKey[] {
  return Object.keys(BASE) as MessageKey[]
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
