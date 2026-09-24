import type { ConfigKey, ConfigPayload } from './payloads'

/**
 * What a marker is, read out of the project rather than known here.
 *
 * The markers are whatever the project declared and they arrive as codepoints, so nothing
 * in this file maps one to an icon, a colour or a word of its own — that is the rule
 * compiled into a reader the non-goals refuse. What `config` publishes is the set *and*,
 * in its key names, what each one is for: `markers.working` names the working one. So the
 * label is read out of the config too, and this app writes no table of meanings.
 *
 * **An undeclared key is not an absent one.** Most projects leave `markers.working` to the
 * default and every one of them still has a working marker, so the value is what the file
 * set or, failing that, what the build falls back to.
 */

/** One codepoint and every config key that names it. */
export interface MarkerMeaning {
  /** The codepoint as the project spells it. */
  readonly marker: string
  /** The config keys naming it, in the order the config lists them. */
  readonly roles: readonly string[]
  /** What to put beside the glyph. Never empty while `roles` is not. */
  readonly label: string
}

/** The config table markers live under. */
export const MARKERS_TABLE = 'markers'

/**
 * The key naming the whole open set rather than one state.
 *
 * It gives way to a more particular key naming the same character, because *open* is the
 * set a marker belongs to and not what it says: a line marked with the working glyph is
 * open, but what a person needs to read is that somebody is on it.
 */
export const SET_KEY = 'open'

/** Values arrive as the file spells them — a quoted scalar, or a JSON array of them. */
function valuesIn(entry: ConfigKey): string[] {
  const spelled = entry.set ?? entry.fallback
  if (spelled === null || spelled === '') return []

  try {
    const parsed: unknown = JSON.parse(spelled)
    if (Array.isArray(parsed)) {
      return parsed.filter((one): one is string => typeof one === 'string' && one !== '')
    }
    if (typeof parsed === 'string') return parsed === '' ? [] : [parsed]
  } catch {
    // Not JSON — a bare value the file spells its own way.
  }

  const bare = spelled.replace(/^["']|["']$/g, '')
  return bare === '' ? [] : [bare]
}

/** The label for a set of roles: the particular ones, or the set key when that is all. */
export function labelOf(roles: readonly string[]): string {
  const particular = roles.filter((role) => role !== SET_KEY)
  return (particular.length > 0 ? particular : roles).join(' / ')
}

/**
 * Every marker this project has, each with what it is for.
 *
 * One codepoint often answers to several keys, so the list is by marker and not by key:
 * the working glyph is in the open set as well, and drawing it twice would be drawing the
 * config's shape rather than the project's states.
 */
export function markersOf(config: ConfigPayload): MarkerMeaning[] {
  const roles = new Map<string, string[]>()

  for (const entry of config.keys) {
    if (entry.table !== MARKERS_TABLE) continue
    for (const marker of valuesIn(entry)) {
      const named = roles.get(marker)
      if (named === undefined) roles.set(marker, [entry.key])
      else if (!named.includes(entry.key)) named.push(entry.key)
    }
  }

  return [...roles].map(([marker, named]) => ({
    marker,
    roles: named,
    label: labelOf(named),
  }))
}

/**
 * What one marker means here, or nothing.
 *
 * Nothing is the honest answer for a codepoint this project does not declare — a line
 * carrying one is a line the grammar did not accept, and inventing a meaning for it would
 * draw it as a status rather than as the anomaly it is.
 */
export function meaningOf(config: ConfigPayload, marker: string): MarkerMeaning | null {
  return markersOf(config).find((one) => one.marker === marker) ?? null
}

/** Whether a marker belongs to the open set, which is a different question from its label. */
export function isOpen(meaning: MarkerMeaning): boolean {
  return meaning.roles.includes(SET_KEY)
}
