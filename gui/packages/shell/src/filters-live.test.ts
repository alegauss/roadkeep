import {
  allLines,
  backlogFrom,
  createCachingTransport,
  createClient,
  filterAsInput,
  filterChoices,
  type BacklogFilter,
  type ConfigPayload,
  type StatsPayload,
} from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { blockWithOpenLines, liveEngine as engine, markerWithOpenLines, read, REPO } from './live'

/**
 * Filters against this repository's own backlog, which is the one place a narrowing can be
 * checked against the thing it narrows. The claim under test is not that the arguments are
 * passed — the unit tests hold that — but that the answer a filter produces is the same
 * answer the command gives, because it *is* that answer.
 */

let calls = 0
const counted = createCachingTransport(
  {
    run: (request) => {
      calls += 1
      return engine.run(request)
    },
  },
  { stampFor: () => Promise.resolve('live'), cacheable: () => true },
)
const client = createClient(counted)

let config: ConfigPayload
let stats: StatsPayload
/** A block that has open lines to narrow to, found rather than named (see `blockWithOpenLines`). */
let busy = ''

async function listWith(filter: BacklogFilter) {
  return backlogFrom(await read(REPO, 'list', filterAsInput(filter), { client }))
}

beforeAll(async () => {
  config = await read(REPO, 'config', {}, { client })
  stats = await read(REPO, 'stats', {}, { client })
  busy = await blockWithOpenLines()
}, 180000)

describe('RG22: what this project offers as filters', () => {
  it('lists the blocks it actually declares', () => {
    const choices = filterChoices(config, stats)

    expect(choices.blocks).toContain('A')
    expect(choices.blocks).toContain('H')
    expect(choices.blocks.length).toBeGreaterThan(4)
  })

  it('lists the markers this project declares, not a set written down here', () => {
    const choices = filterChoices(config, stats)

    expect(choices.markers).toContain('📋')
    expect(choices.markers).toContain('✅')
    expect(choices.markers).toContain('🗑')
  })

  it('lists the governed roles and the three requirements this repository chose', () => {
    const choices = filterChoices(config, stats)

    expect(choices.roles).toContain('roadmap')
    expect(choices.roles).toContain('changelog')
    expect(choices.requirements).toEqual(['signing-cert', 'macos-machine', 'published-artifact'])
  })
})

describe('RG22: a filter is the command answer', () => {
  it('narrows to a block, and every line comes back under it', async () => {
    const backlog = await listWith({ block: busy })

    expect(backlog.blocks.map((block) => block.block)).toEqual([busy])
    expect(allLines(backlog).every((line) => line.block === busy)).toBe(true)
  })

  it('narrows to a marker, and every line carries it', async () => {
    // A marker an open line carries, found (RG163): `💭` by name failed the day the last idea
    // here shipped, on a backlog nothing had broken.
    const marker = await markerWithOpenLines()
    const backlog = await listWith({ marker })

    expect(allLines(backlog).length).toBeGreaterThan(0)
    expect(allLines(backlog).every((line) => line.status === marker)).toBe(true)
  })

  it('narrows to another governed role', async () => {
    const backlog = await listWith({ role: 'changelog' })

    expect(backlog.file).toContain('CHANGELOG.md')
  })

  it('combines two arguments into one read', async () => {
    // A marker the chosen block actually carries, read off that block rather than named
    // (RG158): `💭` with this block selected nothing, and `every` over no lines is true — so
    // this passed while asserting nothing about combining anything.
    const inBusy = allLines(await listWith({ block: busy }))
    const marker = inBusy[0]?.status ?? ''
    expect(marker, `block ${busy} has no open line to take a marker from`).not.toBe('')

    const backlog = await listWith({ block: busy, marker })

    expect(allLines(backlog).length).toBeGreaterThan(0)
    expect(allLines(backlog).every((line) => line.block === busy && line.status === marker)).toBe(
      true,
    )
  })

  it('gives the same answer as the unfiltered read, narrowed', async () => {
    // The property that makes re-reading worth the call: the filtered answer is a subset
    // of the whole one, line for line, because both came from the same verb.
    const everything = await listWith({})
    const justOne = await listWith({ block: busy })

    const ids = new Set(allLines(everything).map((line) => line.id))
    expect(allLines(justOne).every((line) => ids.has(line.id))).toBe(true)
    expect(allLines(justOne).length).toBeLessThan(allLines(everything).length)
  })

  it('costs nothing to go back to a filter already seen', async () => {
    await listWith({ block: busy })
    const before = calls
    await listWith({ block: busy })

    // One call per change is the cost, and the cache is what makes toggling back free.
    expect(calls).toBe(before)
  })
})
