import type { DepChain, DepsPayload, ResolvedDep, Unblocks } from './payloads'

/**
 * A line's edges, laid out for a screen to draw and never walked again.
 *
 * `deps` resolves the whole graph already: each dep with what became of it, the blockers,
 * the chains spelled from this id outward with the hop behind each one, what shipping
 * would free directly and transitively, and the ids caught in a cycle. This module lays
 * that answer out.
 *
 * **Nothing here walks the graph.** A chain arrives as a path and the vias behind it, and
 * a second traversal in this app would be a resolver able to disagree with the one that
 * answered — the same reason readiness is carried rather than recomputed.
 *
 * **One distinction earns the pixels**: a blocker inside the backlog, which shipping
 * clears, against a dep outside it, which shipping never will. `unresolvable` is the
 * engine's word for the second, and sorting its statuses into settled, waiting and never
 * is the only reading taken here — an explicit set, spelled the way `detail.ts` spells
 * settled, so a status nobody anticipated lands in waiting and stays visible.
 */

/**
 * What shipping inside this backlog can do about one dep.
 *
 * `never` is the one that changes a decision. A line waiting on work in another
 * repository does not become ready by anything happening here, and drawn as an ordinary
 * blocker it reads as a queue that is about to move.
 */
export type DepStanding = 'settled' | 'waiting' | 'never'

/**
 * The engine's words for a dep that is done with, either way it got there.
 *
 * Retired counts: the resolver reads a retired dep as never coming, and a client that
 * treated it as still-blocking would hold a line back for a task nobody is going to do.
 */
const SETTLED = new Set(['shipped', 'retired'])

/** The engine's word for a dep nothing in this backlog can ever satisfy. */
const UNRESOLVABLE = 'unresolvable'

/**
 * Sort one engine status into what can be done about it.
 *
 * The default is `waiting` on purpose. A status this app has never seen is a dep somebody
 * still has to deal with, and defaulting the other way would quietly clear it.
 */
export function standingOf(status: string): DepStanding {
  if (SETTLED.has(status)) return 'settled'
  if (status === UNRESOLVABLE) return 'never'
  return 'waiting'
}

export interface Edge extends ResolvedDep {
  readonly standing: DepStanding
}

export interface Chain extends DepChain {
  readonly standing: DepStanding
  /** The path without this line at its head — what a screen draws after the arrow. */
  readonly hops: readonly string[]
}

export interface Graph {
  readonly id: string
  /** The engine's word for where this line stands. Read, never worked out. */
  readonly readiness: string
  readonly edges: readonly Edge[]
  /** Inside the backlog and holding this line. The engine's list, not a filter of `edges`. */
  readonly blockers: readonly string[]
  /** The edges shipping can never clear, named rather than counted. */
  readonly outside: readonly Edge[]
  readonly chains: readonly Chain[]
  readonly unblocks: Unblocks | null
  /** Everything freed downstream but not by shipping this line alone. */
  readonly onward: readonly string[]
  readonly cycle: readonly string[]
  /** In a cycle, where no amount of shipping inside the group starts anything. */
  readonly deadlocked: boolean
}

export function graphFrom(payload: DepsPayload): Graph {
  const edges: Edge[] = payload.deps.map((dep) => ({ ...dep, standing: standingOf(dep.status) }))
  const unblocks = payload.unblocks
  const direct = new Set(unblocks?.direct ?? [])

  return {
    id: payload.id,
    readiness: payload.readiness,
    edges,
    blockers: payload.blockers,
    outside: edges.filter((edge) => edge.standing === 'never'),
    chains: payload.chains.map((chain) => ({
      ...chain,
      standing: standingOf(chain.end),
      hops: chain.path.slice(1),
    })),
    unblocks,
    // The transitive list contains the direct ones, and the difference is why both are
    // shown: four lines freed by shipping this, against four more freed by those four.
    onward: (unblocks?.transitive ?? []).filter((id) => !direct.has(id)),
    cycle: payload.cycle,
    deadlocked: payload.cycle.length > 0,
  }
}

/**
 * One chain as a route, drawn once.
 *
 * The ids in the order the engine spelled them, so a chain is read rather than followed
 * an id at a time. The separator is a rendering choice and the only thing composed here.
 */
export function routeOf(chain: Chain, arrow = ' → '): string {
  return chain.path.join(arrow)
}

/**
 * The dep behind a hop, where it is not the hop itself.
 *
 * A dep naming a block or a range expands to the members behind it, so `via` and `path`
 * differ exactly where the file said one thing and the graph walked to another — which is
 * the case a reader cannot work out from the ids alone.
 */
export function expandedFrom(chain: Chain, index: number): string {
  const via = chain.via[index]
  const hop = chain.hops[index]
  return via === undefined || via === hop ? '' : via
}
