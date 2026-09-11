import { describe, expect, it } from 'vitest'

import {
  expandedFrom,
  graphFrom,
  graphOfBrief,
  routeOf,
  standingOf,
  opensHere,
  type Edge,
} from './graph'
import { readBriefPayload, readDepsPayload, type BriefPayload, type DepsPayload } from './payloads'

/** Captured from a real `deps --json` on a line blocked inside the backlog. */
const RAW = {
  id: 'RG40',
  readiness: 'blocked',
  deps: [{ dep: 'RG38', kind: 'task', status: 'open', detail: 'open in Block F' }],
  blockers: ['RG38'],
  chains: [
    {
      path: ['RG40', 'RG38'],
      via: ['RG38'],
      end: 'open',
      detail: 'open and ready to start',
    },
  ],
  unblocks: { direct: [], transitive: [], count: 0, of: 49 },
  cycle: [],
}

function deps(over: Record<string, unknown> = {}): DepsPayload {
  const parsed = readDepsPayload({ ...RAW, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

/**
 * Captured from a real `brief --json` on a line blocked outside the backlog.
 *
 * Kept as it arrived, which is the point of the fixture: the chain has no `via`, the
 * unblocks have no `direct`, and there is no `blockers` key and no `cycle` key at all.
 */
const BRIEFED = {
  id: 'RG15',
  status: '💭',
  block: 'B',
  symptom: 'which copy of roadkeep each project runs is never read',
  why: 'The block is not finished until the verdict sits beside a project counts.',
  deps: ['RG2 ✅', 'RG13'],
  readiness: 'blocked',
  deps_resolved: [
    { dep: 'RG2', kind: 'task', status: 'shipped', detail: 'in the changelog' },
    { dep: 'RG13', kind: 'task', status: 'open', detail: 'open in Block B' },
  ],
  chains: [
    {
      path: ['RG15', 'RG13', 'roadkeep RK1631'],
      end: 'unresolvable',
      detail: 'outside the backlog: shipping cannot satisfy it',
    },
  ],
  unblocks: { count: 0, of: 32, transitive: [], transitive_elided: 0 },
}

function brief(over: Record<string, unknown> = {}): BriefPayload {
  const parsed = readBriefPayload({ ...BRIEFED, ...over }, '')
  if (!parsed.ok) throw new Error(`the fixture does not match the shape: ${parsed.failure.path}`)
  return parsed.value
}

describe('RG25: a blocker inside the backlog against one outside it', () => {
  it('sorts each engine status into what shipping can do about it', () => {
    expect(standingOf('shipped')).toBe('settled')
    expect(standingOf('retired')).toBe('settled')
    expect(standingOf('open')).toBe('waiting')
    expect(standingOf('unresolvable')).toBe('never')
  })

  it('calls a status it has never seen waiting, rather than clearing it', () => {
    // Defaulting the other way would quietly settle a dep somebody still has to deal
    // with, and it would do it silently.
    expect(standingOf('paused-pending-review')).toBe('waiting')
    expect(standingOf('')).toBe('waiting')
  })

  it('names the deps shipping here can never satisfy', () => {
    const graph = graphFrom(
      deps({
        id: 'RG9',
        readiness: 'blocked-outside',
        deps: [
          { dep: 'RG1', kind: 'task', status: 'shipped', detail: 'in the changelog' },
          {
            dep: 'roadkeep RK1632',
            kind: 'external',
            status: 'unresolvable',
            detail: 'outside the backlog: nothing here will ever mark this done',
          },
        ],
        blockers: [],
      }),
    )

    expect(graph.outside.map((edge) => edge.dep)).toEqual(['roadkeep RK1632'])
    expect(graph.outside[0]?.detail).toContain('outside the backlog')
    // Not a blocker in the engine's sense: no amount of shipping here clears it, so it is
    // absent from the list of what is holding the line up.
    expect(graph.blockers).toEqual([])
  })

  it('takes the blockers from the engine rather than filtering the edges', () => {
    const graph = graphFrom(deps())

    expect(graph.blockers).toEqual(['RG38'])
    expect(graph.edges[0]?.standing).toBe('waiting')
  })

  it('carries readiness in the engine own word', () => {
    expect(graphFrom(deps()).readiness).toBe('blocked')
    expect(graphFrom(deps({ readiness: 'blocked-outside' })).readiness).toBe('blocked-outside')
  })
})

describe('RG25: a chain, drawn once', () => {
  it('draws the route the engine spelled, in its order', () => {
    const graph = graphFrom(deps())

    expect(routeOf(graph.chains[0]!)).toBe('RG40 → RG38')
    expect(graph.chains[0]?.hops).toEqual(['RG38'])
  })

  it('walks nothing: a three-hop chain arrives whole', () => {
    const graph = graphFrom(
      deps({
        chains: [
          {
            path: ['RG40', 'RG38', 'RG1', 'roadkeep RK1632'],
            via: ['RG38', 'RG1', 'roadkeep RK1632'],
            end: 'unresolvable',
            detail: 'outside the backlog: shipping cannot satisfy it',
          },
        ],
      }),
    )

    expect(routeOf(graph.chains[0]!)).toBe('RG40 → RG38 → RG1 → roadkeep RK1632')
    expect(graph.chains[0]?.standing).toBe('never')
  })

  it('says which dep the file wrote when a hop was expanded from it', () => {
    // A dep naming a block expands to its members, and `via` is what the line says.
    const graph = graphFrom(
      deps({
        chains: [
          {
            path: ['RG40', 'RG38', 'RG41'],
            via: ['Block F', 'RG41'],
            end: 'open',
            detail: 'open and ready to start',
          },
        ],
      }),
    )

    expect(expandedFrom(graph.chains[0]!, 0)).toBe('Block F')
    expect(expandedFrom(graph.chains[0]!, 1)).toBe('')
    expect(expandedFrom(graph.chains[0]!, 9)).toBe('')
  })

  it('has no chains at all when nothing is holding the line', () => {
    const graph = graphFrom(deps({ readiness: 'ready', blockers: [], chains: [] }))

    expect(graph.chains).toEqual([])
  })
})

describe('RG25: what shipping this would free', () => {
  it('separates the one-hop win from the cascade behind it', () => {
    const graph = graphFrom(
      deps({
        unblocks: {
          direct: ['RG40', 'RG41'],
          transitive: ['RG40', 'RG41', 'RG42', 'RG43'],
          count: 4,
          of: 49,
        },
      }),
    )

    expect(graph.unblocks?.direct).toEqual(['RG40', 'RG41'])
    expect(graph.onward).toEqual(['RG42', 'RG43'])
    expect(graph.unblocks?.count).toBe(4)
  })

  it('leaves onward empty when every id freed is freed directly', () => {
    const graph = graphFrom(
      deps({
        unblocks: {
          direct: ['RG40', 'RG41'],
          transitive: ['RG40', 'RG41'],
          count: 2,
          of: 49,
        },
      }),
    )

    expect(graph.onward).toEqual([])
  })

  it('withholds the split when it was never given the direct half', () => {
    // The brief-shaped unblocks: a sample of the transitive set and no direct list. The
    // difference against nothing is the whole sample, which would call all fifteen freed
    // downstream when some of them are freed by shipping this line itself.
    const graph = graphFrom(
      deps({ unblocks: { transitive: ['RG40'], count: 15, of: 49, transitive_elided: 11 } }),
    )

    expect(graph.unblocks?.direct).toEqual([])
    expect(graph.unblocks?.transitiveElided).toBe(11)
    expect(graph.onward).toEqual([])
    expect(graph.narrowing.complete).toBe(false)
  })
})

describe('RG25: a cycle, where nothing in the group can start', () => {
  it('names the ids caught in it and says so', () => {
    const graph = graphFrom(deps({ cycle: ['RG40', 'RG41', 'RG42'] }))

    expect(graph.deadlocked).toBe(true)
    expect(graph.cycle).toEqual(['RG40', 'RG41', 'RG42'])
  })

  it('is the ordinary answer for every line that is not in one', () => {
    const graph = graphFrom(deps())

    expect(graph.deadlocked).toBe(false)
    expect(graph.cycle).toEqual([])
    expect(graph.narrowing.complete).toBe(true)
  })
})

describe('RG76: the graph a brief already sent', () => {
  it('draws the chain off the read that opened the task', () => {
    const graph = graphOfBrief(brief())

    expect(routeOf(graph.chains[0]!)).toBe('RG15 → RG13 → roadkeep RK1631')
    expect(graph.chains[0]?.standing).toBe('never')
    expect(graph.outside.map((edge) => edge.dep)).toEqual([])
    expect(graph.readiness).toBe('blocked')
  })

  it('defaults the hop behind a chain, which a brief does not spell', () => {
    // `via` is the one field `deps` adds to a chain. The reader defaults it and this says
    // so out loud: an empty answer here means ask `deps`, never that nothing expanded.
    expect(expandedFrom(graphOfBrief(brief()).chains[0]!, 0)).toBe('')
  })

  it('says which lists it was never given, rather than calling them empty', () => {
    const graph = graphOfBrief(brief())

    expect(graph.blockers).toEqual([])
    expect(graph.cycle).toEqual([])
    expect(graph.deadlocked).toBe(false)
    // The two brackets a screen must not read as "nothing is holding this line".
    expect(graph.narrowing.complete).toBe(false)
    expect(graph.narrowing.reasons[0]).toContain('deps')
  })

  it('resolves each dep the same way, because it is the same list', () => {
    const graph = graphOfBrief(brief())

    expect(graph.edges.map((edge) => edge.standing)).toEqual(['settled', 'waiting'])
  })
})

describe('RG173: which ids this window can open', () => {
  const edge = (over: Partial<Edge>): Edge => ({
    dep: 'AL0',
    kind: 'task',
    status: 'shipped',
    detail: '',
    standing: 'settled',
    ...over,
  })

  it('opens a dep the brief calls a task here, shipped or open', () => {
    expect(opensHere(edge({ status: 'shipped', standing: 'settled' }))).toBe(true)
    expect(opensHere(edge({ status: 'open', standing: 'waiting' }))).toBe(true)
  })

  it('does not open one whose standing is never, whatever kind it is', () => {
    // A dep in another repository, or on work roadkeep has not published: a link there
    // would open a refusal and draw the line as merely missing.
    expect(opensHere(edge({ standing: 'never' }))).toBe(false)
    expect(opensHere(edge({ kind: 'task', standing: 'never' }))).toBe(false)
  })

  it('does not open anything the brief does not call a task, whatever its id looks like', () => {
    // Nothing here recognises an id by its shape: an id's shape is the project's.
    expect(opensHere(edge({ kind: 'outside' }))).toBe(false)
    expect(opensHere(edge({ kind: 'block' }))).toBe(false)
    expect(opensHere(edge({ kind: '' }))).toBe(false)
  })
})
