import {
  isOpen,
  markersOf,
  meaningOf,
  openMarkers,
  workingMarker,
  type ConfigPayload,
} from '@rk/core'
import { beforeAll, describe, expect, it } from 'vitest'

import { read, REPO } from './live'

/**
 * RG53: the marker set, read off a real engine.
 *
 * A hand-written config is this app's idea of what one looks like. This one asks the engine
 * that governs this repository, which is the only build the reading can be true about — and
 * asserts about the *shape*, never about which emoji this project chose.
 */

let config: ConfigPayload

beforeAll(async () => {
  config = await read(REPO, 'config', {})
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

  it('offers the write path a set that is part of the one it renders', () => {
    // RG89 made `openMarkers` a filter over `markersOf`, so this no longer holds two
    // derivations equal — there is one. What is still worth asserting against a real config
    // is that the dropdown's set is non-empty and is drawn from the markers this project
    // actually has: a filter that matched nothing would leave the status verb with no
    // marker to offer, and nothing else in the suite would notice.
    const open = openMarkers(config)

    expect(open.length).toBeGreaterThan(0)
    expect(markersOf(config).map((one) => one.marker)).toEqual(expect.arrayContaining(open))
    expect(markersOf(config).filter(isOpen)).toHaveLength(open.length)
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
    const overlapping = markersOf(config).filter((one) => one.roles.length > 1 && isOpen(one))

    expect(overlapping.length).toBeGreaterThan(0)
    for (const meaning of overlapping) expect(meaning.label).not.toBe('open')
  })
})

describe('RG74: the marker this project moves a line to', () => {
  it('reads one, and it is one this project can actually carry', () => {
    const working = workingMarker(config)

    // Read and never guessed: most projects declare no `markers.working`, and the config
    // carries what the build uses when nothing does. Held to the open set, because a
    // marker outside it names a state no line here may be in.
    expect(working).not.toBe('')
    expect(openMarkers(config)).toContain(working)
  })

  it('is the marker a claim actually moves a line to', () => {
    // The whole point of reading it rather than declaring one: this is the emoji the
    // engine writes when somebody takes a line, and RG74 compares against it.
    expect(workingMarker(config)).toBe('🛠')
  })
})
