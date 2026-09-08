import path from 'node:path'

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

import { createProcessTransport } from './process-transport'

/**
 * Filters against this repository's own backlog, which is the one place a narrowing can be
 * checked against the thing it narrows. The claim under test is not that the arguments are
 * passed — the unit tests hold that — but that the answer a filter produces is the same
 * answer the command gives, because it *is* that answer.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

let calls = 0
const engine = createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] })
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

async function listWith(filter: BacklogFilter) {
  const answer = await client.call(REPO, 'list', filterAsInput(filter), { timeoutMs: CEILING })
  if (!answer.ok) throw new Error(`list did not read: ${answer.failure.path}`)
  if (answer.value.kind === 'refused') throw new Error('list was refused')
  return backlogFrom(answer.value.value)
}

beforeAll(async () => {
  const configRead = await client.call(REPO, 'config', {}, { timeoutMs: CEILING })
  if (!configRead.ok || configRead.value.kind === 'refused') {
    throw new Error('config did not read')
  }
  config = configRead.value.value

  const statsRead = await client.call(REPO, 'stats', {}, { timeoutMs: CEILING })
  if (!statsRead.ok || statsRead.value.kind === 'refused') {
    throw new Error('stats did not read')
  }
  stats = statsRead.value.value
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
    const backlog = await listWith({ block: 'A' })

    expect(backlog.blocks.map((block) => block.block)).toEqual(['A'])
    expect(allLines(backlog).every((line) => line.block === 'A')).toBe(true)
  })

  it('narrows to a marker, and every line carries it', async () => {
    const backlog = await listWith({ marker: '💭' })

    expect(allLines(backlog).length).toBeGreaterThan(0)
    expect(allLines(backlog).every((line) => line.status === '💭')).toBe(true)
  })

  it('narrows to another governed role', async () => {
    const backlog = await listWith({ role: 'changelog' })

    expect(backlog.file).toContain('CHANGELOG.md')
  })

  it('combines two arguments into one read', async () => {
    const backlog = await listWith({ block: 'A', marker: '💭' })

    expect(allLines(backlog).every((line) => line.block === 'A' && line.status === '💭')).toBe(true)
  })

  it('gives the same answer as the unfiltered read, narrowed', async () => {
    // The property that makes re-reading worth the call: the filtered answer is a subset
    // of the whole one, line for line, because both came from the same verb.
    const everything = await listWith({})
    const justA = await listWith({ block: 'A' })

    const ids = new Set(allLines(everything).map((line) => line.id))
    expect(allLines(justA).every((line) => ids.has(line.id))).toBe(true)
    expect(allLines(justA).length).toBeLessThan(allLines(everything).length)
  })

  it('costs nothing to go back to a filter already seen', async () => {
    await listWith({ block: 'A' })
    const before = calls
    await listWith({ block: 'A' })

    // One call per change is the cost, and the cache is what makes toggling back free.
    expect(calls).toBe(before)
  })
})
