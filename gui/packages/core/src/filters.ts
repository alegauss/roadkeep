import { governedFiles, type ConfigPayload, type StatsPayload } from './payloads'
import type { VerbInputs } from './verbs'

/**
 * Narrowing a backlog, using the arguments the verb already takes.
 *
 * Every filter on this screen is an argument `list` accepts: the block, the marker, the
 * role, and the requirement a caller says it has. Choosing one **re-runs the read** rather
 * than filtering an array that is already in memory.
 *
 * That is slower and it is the point. A narrowing this app performs is a narrowing this
 * app invented, and an invented one can disagree with the tool's — quietly, in the
 * direction where a line is missing from a list somebody is using to decide what to work
 * on. Re-reading means the answer on screen is the answer `roadkeep list --block C` gives,
 * always, because it is literally that answer.
 *
 * The cost is one call per change, which is what the cache is for: a filter toggled back
 * to a value already seen costs nothing at all.
 *
 * What stays in the client is text search, and only because no argument covers it.
 *
 * The choices offered are read as well. Which markers a project declares, which roles are
 * governed and which requirements exist are all in `config`, so a dropdown here lists what
 * the project says rather than what this app remembers.
 */

/**
 * The filter, which is exactly the shape of a `list` call.
 *
 * `FILTER_FIELDS` below is asserted against the verb's own input in the tests: a field
 * added here that `list` does not take would be a predicate this app evaluates, which is
 * the thing this whole file exists to avoid.
 */
export interface BacklogFilter {
  readonly block?: string
  readonly role?: string
  readonly marker?: string
  readonly have?: readonly string[]
  /**
   * The deferred store, which `--stale` names without a `--role`. A narrowing like the
   * rest: the store is a governed role and reading it is one call, not a predicate.
   */
  readonly stale?: boolean
}

export const FILTER_FIELDS = ['block', 'role', 'marker', 'have', 'stale'] as const

export const NO_FILTER: BacklogFilter = {}

/** The read that answers this filter. Nothing is dropped and nothing is added. */
export function filterAsInput(filter: BacklogFilter): VerbInputs['list'] {
  return {
    ...(filter.block === undefined ? {} : { block: filter.block }),
    ...(filter.role === undefined ? {} : { role: filter.role }),
    ...(filter.marker === undefined ? {} : { marker: filter.marker }),
    ...(filter.have === undefined || filter.have.length === 0 ? {} : { have: filter.have }),
    // False is not a narrowing, so it is left off rather than sent as a flag the engine
    // would then have to read as "not the store".
    ...(filter.stale === true ? { stale: true } : {}),
  }
}

/** Whether anything is narrowed at all, so a screen can say "showing everything". */
export function isNarrowed(filter: BacklogFilter): boolean {
  return Object.keys(filterAsInput(filter)).length > 0
}

/** Change one field, which is how a screen toggles a filter without rebuilding it. */
export function withField<K extends keyof BacklogFilter>(
  filter: BacklogFilter,
  field: K,
  value: BacklogFilter[K],
): BacklogFilter {
  const next = { ...filter }
  if (value === undefined) delete next[field]
  else next[field] = value
  return next
}

export interface FilterChoices {
  readonly blocks: readonly string[]
  readonly roles: readonly string[]
  readonly markers: readonly string[]
  readonly requirements: readonly string[]
}

/** A `config` value, read by its address and unwrapped from the spelling the file uses. */
function declared(config: ConfigPayload, address: string): string[] {
  const entry = config.keys.find((key) => key.address === address)
  if (entry?.set === undefined || entry.set === null || entry.set === '') return []

  try {
    const parsed: unknown = JSON.parse(entry.set)
    if (Array.isArray(parsed))
      return parsed.filter((value): value is string => typeof value === 'string')
    if (typeof parsed === 'string') return [parsed]
  } catch {
    // Not JSON — a bare value the file spells its own way. Strip the quotes and take it.
  }
  return [entry.set.replace(/^["']|["']$/g, '')]
}

/**
 * What each filter may be set to, according to the project.
 *
 * Read rather than enumerated: the marker set is per project, the governed roles are
 * whatever `[files]` declares, and the requirements are three words this repository chose.
 * A list written here would be this app's idea of another project's format.
 */
export function filterChoices(
  config: ConfigPayload,
  stats: StatsPayload | null = null,
): FilterChoices {
  const markers = [
    ...declared(config, 'markers.open'),
    ...declared(config, 'markers.shipped'),
    ...declared(config, 'markers.retired'),
    ...declared(config, 'markers.deferred'),
  ]

  return {
    blocks: (stats?.blocks ?? []).map((block) => block.block),
    roles: Object.keys(governedFiles(config)),
    markers: [...new Set(markers)],
    requirements: declared(config, 'requirements.declared'),
  }
}

/** What is currently narrowed, as something a screen can put next to a result. */
export function describeFilter(filter: BacklogFilter): string {
  const parts: string[] = []
  if (filter.stale === true) parts.push('the deferred store')
  if (filter.role !== undefined) parts.push(`the ${filter.role}`)
  if (filter.block !== undefined) parts.push(`block ${filter.block}`)
  if (filter.marker !== undefined) parts.push(`marker ${filter.marker}`)
  if (filter.have !== undefined && filter.have.length > 0) {
    parts.push(`with ${filter.have.join(' and ')}`)
  }
  return parts.join(', ')
}
