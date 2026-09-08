import path from 'node:path'

import {
  createClient,
  isOpen,
  markersOf,
  meaningOf,
  openMarkers,
  readConfigPayload,
  readPayload,
  type ConfigPayload,
} from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { createProcessTransport } from './process-transport'

/**
 * RG53: the marker set, read off a real engine.
 *
 * A hand-written config is this app's idea of what one looks like. This one asks the engine
 * that governs this repository, which is the only build the reading can be true about — and
 * asserts about the *shape*, never about which emoji this project chose.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const LAUNCHER = path.join(REPO, '.claude', 'hooks', 'roadkeep-launch.py')
const CEILING = 60000

const client = createClient(createProcessTransport({ command: 'python', prefixArgs: [LAUNCHER] }))

let config: ConfigPayload

beforeAll(async () => {
  const result = await client.call(REPO, 'config', {}, { timeoutMs: CEILING })
  const parsed = readPayload(readConfigPayload, result.stdout, { verb: 'config', engineVersion: '' })
  if (!parsed.ok) throw new Error('config did not read')
  config = parsed.value
}, 120000)

describe('RG53: what a real config says about markers', () => {
  it('finds markers at all, which is the whole premise', () => {
    expect(markersOf(config).length).toBeGreaterThan(0)
  })

  it('gives every one of them something to say', () => {
    for (const meaning of markersOf(config)) {
      expect(meaning.marker).not.toBe('')
      expect(meaning.label).not.toBe('')
      expect(meaning.roles.length).toBeGreaterThan(0)
    }
  })

  it('agrees with the open set the write path reads, which is derived another way', () => {
    // `openMarkers` reads `markers.open` alone for the status dropdown. Two readings of one
    // config that disagreed would put a marker in a list the other says is not a state.
    const open = openMarkers(config)
    const byRole = markersOf(config)
      .filter(isOpen)
      .map((one) => one.marker)

    expect(byRole.sort()).toEqual([...open].sort())
  })

  it('carries a key this project never declared', () => {
    // The point of reading the fallback: a project that leaves a marker to the default
    // still has that marker, and a reader that only took `set` would lose it.
    const undeclared = config.keys.filter(
      (entry) => entry.table === 'markers' && !entry.declared && entry.fallback !== null,
    )

    expect(undeclared.length).toBeGreaterThan(0)
    for (const entry of undeclared) {
      const value = JSON.parse(entry.fallback ?? 'null') as unknown
      const first = Array.isArray(value) ? (value[0] as string) : (value as string)
      expect(meaningOf(config, first)).not.toBeNull()
    }
  })

  it('names each marker once, however many keys reach it', () => {
    const found = markersOf(config).map((one) => one.marker)

    expect(found).toEqual([...new Set(found)])
  })

  it('labels the marker that is both open and something more by the something more', () => {
    // This project's open set overlaps its particular keys; whichever emoji they are, the
    // label has to be the particular one or the list says `open` three times.
    const overlapping = markersOf(config).filter(
      (one) => one.roles.length > 1 && isOpen(one),
    )

    expect(overlapping.length).toBeGreaterThan(0)
    for (const meaning of overlapping) expect(meaning.label).not.toBe('open')
  })
})
