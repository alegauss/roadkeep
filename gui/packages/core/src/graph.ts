import type {
  BriefPayload,
  DepChain,
  DepsPayload,
  Narrowing,
  ResolvedDep,
  Unblocks,
} from './payloads'

/**
 * A line's edges, laid out for a screen to draw and never walked again.
 *
 * `deps` resolves the whole graph already: each dep with what became of it, the blockers,
 * the chains spelled from this id outward with the hop behind each one, what shipping
 * would free directly and transitively, and the ids caught in a cycle. This module lays
 * that answer out.
 *
 * **A brief resolves most of it too**, and the lay-out is the same one. Opening a task
 * costs one read, so the chains that read already sent are drawn from it rather than
 * fetched again; `deps` stays the call for the three things only it answers, and the graph
 * says which those are instead of sending back an empty list that means "none".
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
  /**
   * Which of these lists the read that answered could not fill.
   *
   * An empty `blockers` means nothing is holding the line; an empty `blockers` on a graph
   * that was never asked for one means the caller has no idea. The two look identical and
   * this is the only thing that tells them apart.
   */
  readonly narrowing: Narrowing
}

/**
 * The half of a resolved graph both verbs answer.
 *
 * `deps` fills every field of it. A brief fills the deps, the chains and the unblock
 * counts, which is what an opening task draws — naming the shape here is what lets one
 * lay-out serve both, rather than a second module kept saying the same thing.
 */
interface Resolution {
  readonly id: string
  readonly readiness: string
  readonly deps: readonly ResolvedDep[]
  readonly blockers: readonly string[]
  readonly chains: readonly DepChain[]
  readonly unblocks: Unblocks | null
  readonly cycle: readonly string[]
}

export function graphFrom(payload: DepsPayload): Graph {
  return layout(payload, [])
}

/**
 * The graph a brief already sent, laid out without asking for it again.
 *
 * Block D's criterion is that a task opens in one read, and `brief` resolves this line's
 * deps and spells the same chains from it outward — so the ordinary open task is drawn off
 * the call that opened it. What a brief does not carry is the blockers as a list and the
 * ids caught in a cycle, and `deps` is the call a screen makes when somebody asks for
 * those or for the dep behind a hop. Deferred, not replaced.
 */
export function graphOfBrief(payload: BriefPayload): Graph {
  return layout(
    {
      id: payload.id,
      readiness: payload.readiness,
      deps: payload.depsResolved,
      blockers: [],
      chains: payload.chains,
      unblocks: payload.unblocks,
      cycle: [],
    },
    ['the blockers as a list and the ids in a cycle, which only `deps` names'],
  )
}

/**
 * @param absent what this caller's verb does not answer at all, in its own words — the
 *   one part that cannot be read off the payload, since a list nobody asked for and a
 *   list that came back empty are the same two brackets.
 */
function layout(payload: Resolution, absent: readonly string[]): Graph {
  const edges: Edge[] = payload.deps.map((dep) => ({ ...dep, standing: standingOf(dep.status) }))
  const unblocks = payload.unblocks
  const direct = new Set(unblocks?.direct ?? [])
  const transitive = unblocks?.transitive ?? []

  // The transitive list contains the direct ones, and the difference is why both are
  // shown: four lines freed by shipping this, against four more freed by those four. With
  // no direct list there is no difference to take — subtracting nothing would call every
  // freed id downstream, which is the one reading that is certainly wrong.
  const split = direct.size > 0
  const reasons = [...absent]
  if (!split && transitive.length > 0) {
    reasons.push('which of these ids shipping this line frees on its own, which `deps` separates')
  }

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
    onward: split ? transitive.filter((id) => !direct.has(id)) : [],
    cycle: payload.cycle,
    deadlocked: payload.cycle.length > 0,
    narrowing: { complete: reasons.length === 0, reasons },
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
 * Whether this dep is a line this window can open (RG173).
 *
 * Two conditions, both the engine's. It has to be a task in this backlog — the brief says
 * which, and nothing here recognises an id by its shape, since an id's shape is the
 * project's — and its standing must not be `never`: a dep in another repository, or on work
 * roadkeep has not published, has no route in this window, and a link that opened a refusal
 * would draw it as a line that is merely missing.
 *
 * A shipped dep opens: it briefs as the ledger's entry, which is an answer and not a dead end.
 */
export function opensHere(edge: Edge): boolean {
  return edge.kind === 'task' && edge.standing !== 'never'
}

/**
 * Which hops of a route open, in the order the route draws them (RG173).
 *
 * Every hop is a line this backlog walked to, so every hop opens — except the last of a
 * chain that ends outside it, which is the id the walk stopped at and cannot be followed to.
 */
export function hopsOpening(chain: Chain): readonly boolean[] {
  const outside = chain.standing === 'never'
  return chain.hops.map((_, at) => !(outside && at === chain.hops.length - 1))
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
