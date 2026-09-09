import { graphFrom, listedTasks, routeOf, type Graph } from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { read, REPO } from './live'

/**
 * The graph read against this repository's own backlog, which has every edge worth
 * drawing: shipped deps, a line blocked on an open one, and two lines waiting on work in
 * another repository that shipping here can never satisfy.
 */

async function graphOf(id: string): Promise<Graph> {
  return graphFrom(await read(REPO, 'deps', { id }))
}

/**
 * Ids found rather than written down.
 *
 * An id was named here once, and naming one asserts it is still open — the claim that
 * stops being true the day it ships. So the states under test are located by asking every
 * line in the backlog for its graph, and the assertions are about the states rather than
 * about which id happens to be in one.
 */
let outside: Graph | undefined
let blocked: Graph | undefined
let leverage: Graph | undefined

beforeAll(async () => {
  const ids = listedTasks(await read(REPO, 'list', {})).map((one) => one.id)

  for (const id of ids) {
    const graph = await graphOf(id)
    outside ??= graph.outside.length > 0 ? graph : undefined
    blocked ??= graph.blockers.length > 0 ? graph : undefined
    leverage ??= (graph.unblocks?.count ?? 0) > 0 ? graph : undefined
    if (outside && blocked && leverage) break
  }
}, 300000)

describe('RG25: a blocker inside the backlog against one outside it', () => {
  it('finds a line waiting on work no ship here can ever satisfy', () => {
    expect(outside).toBeDefined()
    expect(outside?.outside[0]?.status).toBe('unresolvable')
    expect(outside?.outside[0]?.detail).not.toBe('')
    expect(outside?.readiness).not.toBe('ready')
  })

  it('finds a line held by an open one, which shipping does clear', () => {
    expect(blocked).toBeDefined()
    expect(blocked?.blockers.length).toBeGreaterThan(0)
    // Every id the engine calls a blocker is a line in this backlog, so it is one an id
    // can be looked up by — which is what makes it different from the outside case.
    expect(blocked?.blockers.every((id) => /^RG\d+$/.test(id))).toBe(true)
  })

  it('carries a settled dep without calling it a blocker', () => {
    const settled = blocked?.edges.filter((edge) => edge.standing === 'settled') ?? []

    for (const edge of settled) {
      expect(blocked?.blockers).not.toContain(edge.dep)
    }
  })
})

describe('RG25: a chain, drawn once', () => {
  it('spells a route from the line outward, this id at its head', () => {
    const chain = (blocked ?? outside)?.chains[0]

    expect(chain).toBeDefined()
    expect(chain?.path[0]).toBe((blocked ?? outside)?.id)
    expect(routeOf(chain!)).toContain('→')
  })

  it('ends a chain out of the backlog in a standing shipping cannot change', () => {
    const chain = outside?.chains.find((one) => one.standing === 'never')

    expect(chain).toBeDefined()
    expect(chain?.detail).not.toBe('')
    expect(chain?.path.at(-1)).toBe(outside?.outside[0]?.dep)
  })
})

describe('RG25: what shipping this would free', () => {
  it('names the direct set and the cascade, against the size of the backlog', () => {
    expect(leverage).toBeDefined()
    expect(leverage?.unblocks?.of).toBeGreaterThan(0)
    expect(leverage?.unblocks?.direct.length).toBeGreaterThan(0)
    // Every direct id is in the transitive set: the second contains the first.
    for (const id of leverage?.unblocks?.direct ?? []) {
      expect(leverage?.unblocks?.transitive).toContain(id)
    }
    expect(leverage?.onward).not.toContain(leverage?.unblocks?.direct[0])
  })

  it('reads a cycle as absent, because this backlog has none', () => {
    expect(leverage?.deadlocked).toBe(false)
    expect(blocked?.cycle).toEqual([])
  })
})
