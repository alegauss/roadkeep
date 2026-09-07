import { describe, expect, it } from 'vitest'

import {
  describeFilter,
  filterAsInput,
  filterChoices,
  FILTER_FIELDS,
  isNarrowed,
  NO_FILTER,
  withField,
} from './filters'
import type { ConfigKey, ConfigPayload, StatsPayload } from './payloads'
import { EVERY_INPUT } from './verbs'

const key = (table: string, name: string, set: string | null): ConfigKey => ({
  table,
  key: name,
  address: table === '' ? name : `${table}.${name}`,
  declared: set !== null,
  set,
})

const CONFIG: ConfigPayload = {
  version: '0.2.366',
  source: 'roadkeep.toml',
  keys: [
    key('files', 'roadmap', '"docs/ROADMAP.md"'),
    key('files', 'changelog', '"docs/CHANGELOG.md"'),
    key('files', 'deferred', '"docs/DEFERRED.md"'),
    key('files', 'strategy', null),
    key('markers', 'open', '["📋", "💭", "⏳", "🛠"]'),
    key('markers', 'shipped', '"✅"'),
    key('markers', 'retired', '"🗑"'),
    key('markers', 'deferred', null),
    key('requirements', 'declared', '["signing-cert", "macos-machine"]'),
  ],
}

const STATS: StatsPayload = {
  file: 'docs/ROADMAP.md',
  total: 60,
  uncounted: 0,
  markers: {},
  startable: null,
  blocks: [
    { block: 'A', counted: 9, uncounted: 0, markers: {} },
    { block: 'B', counted: 6, uncounted: 0, markers: {} },
  ],
}

describe('RG22: a filter is a call, not a predicate', () => {
  it('declares exactly the fields the list verb takes', () => {
    // The guard this file exists for. A field here that `list` does not take would be a
    // predicate this app evaluates, and an invented narrowing can disagree with the
    // tool's — quietly, by leaving a line out of a list somebody is deciding from.
    expect([...FILTER_FIELDS].sort()).toEqual(Object.keys(EVERY_INPUT.list).sort())
  })

  it('turns into the arguments of a read', () => {
    expect(filterAsInput({ block: 'C', marker: '📋' })).toEqual({ block: 'C', marker: '📋' })
  })

  it('sends nothing for a field nobody set', () => {
    expect(filterAsInput(NO_FILTER)).toEqual({})
    expect(filterAsInput({ block: 'C' })).not.toHaveProperty('marker')
  })

  it('drops an empty requirement list rather than sending one', () => {
    expect(filterAsInput({ have: [] })).toEqual({})
    expect(filterAsInput({ have: ['signing-cert'] })).toEqual({ have: ['signing-cert'] })
  })

  it('says whether anything is narrowed at all', () => {
    expect(isNarrowed(NO_FILTER)).toBe(false)
    expect(isNarrowed({ have: [] })).toBe(false)
    expect(isNarrowed({ block: 'C' })).toBe(true)
  })
})

describe('RG22: changing one field', () => {
  it('sets a field without touching the others', () => {
    const filter = withField({ block: 'C', marker: '📋' }, 'role', 'changelog')

    expect(filter).toEqual({ block: 'C', marker: '📋', role: 'changelog' })
  })

  it('clears a field when the value goes away', () => {
    const filter = withField({ block: 'C', marker: '📋' }, 'marker', undefined)

    expect(filter).toEqual({ block: 'C' })
    expect(Object.hasOwn(filter, 'marker')).toBe(false)
  })

  it('does not change the filter it was given', () => {
    const before = { block: 'C' }
    withField(before, 'block', 'D')

    expect(before).toEqual({ block: 'C' })
  })
})

describe('RG22: what a filter may be set to', () => {
  it('reads the markers the project declares rather than a list written here', () => {
    // The marker set is per project. A list in this file would be this app's idea of
    // another project's format.
    const choices = filterChoices(CONFIG, STATS)

    expect(choices.markers).toEqual(['📋', '💭', '⏳', '🛠', '✅', '🗑'])
  })

  it('reads the governed roles, and only the declared ones', () => {
    const choices = filterChoices(CONFIG, STATS)

    expect(choices.roles).toEqual(['roadmap', 'changelog', 'deferred'])
    expect(choices.roles).not.toContain('strategy')
  })

  it('reads the requirements this project declares', () => {
    expect(filterChoices(CONFIG, STATS).requirements).toEqual([
      'signing-cert',
      'macos-machine',
    ])
  })

  it('reads the blocks off the counts, in the order they came', () => {
    expect(filterChoices(CONFIG, STATS).blocks).toEqual(['A', 'B'])
  })

  it('offers no blocks when nothing has been counted yet', () => {
    expect(filterChoices(CONFIG).blocks).toEqual([])
  })

  it('survives a config that declares almost nothing', () => {
    const bare: ConfigPayload = { version: '0.1.0', source: 'roadkeep.toml', keys: [] }

    expect(filterChoices(bare)).toEqual({
      blocks: [],
      roles: [],
      markers: [],
      requirements: [],
    })
  })

  it('takes a value the file spells without quotes', () => {
    const odd: ConfigPayload = {
      ...CONFIG,
      keys: [key('markers', 'shipped', 'done')],
    }

    expect(filterChoices(odd).markers).toEqual(['done'])
  })
})

describe('RG22: saying what is narrowed', () => {
  it('says nothing when nothing is', () => {
    expect(describeFilter(NO_FILTER)).toBe('')
  })

  it('names the role, the block, the marker and the requirements', () => {
    const described = describeFilter({
      role: 'changelog',
      block: 'C',
      marker: '📋',
      have: ['signing-cert'],
    })

    expect(described).toBe('the changelog, block C, marker 📋, with signing-cert')
  })

  it('joins two requirements readably', () => {
    expect(describeFilter({ have: ['signing-cert', 'macos-machine'] })).toBe(
      'with signing-cert and macos-machine',
    )
  })
})
