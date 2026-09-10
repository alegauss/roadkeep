import { describe, expect, it } from 'vitest'

import { isOpen, labelOf, markersOf, meaningOf } from './markers'
import type { ConfigKey, ConfigPayload } from './payloads'

/** A config key as the engine publishes one. */
function key(partial: Partial<ConfigKey> & { key: string }): ConfigKey {
  return {
    table: 'markers',
    address: `markers.${partial.key}`,
    declared: false,
    set: null,
    fallback: null,
    ...partial,
  }
}

function config(...keys: ConfigKey[]): ConfigPayload {
  return { version: '0.2.400', source: 'roadkeep.toml', governed: true, root: '/code/app', keys }
}

/** This repository's own markers, spelled the way `config` spells them. */
const THIS_PROJECT = config(
  key({ key: 'deferred', fallback: '"⏸"' }),
  key({ key: 'dismissed', fallback: '"🚫"' }),
  key({ key: 'open', declared: true, set: '["📋", "💭", "⏳", "🛠"]', fallback: '["📋"]' }),
  key({ key: 'partial', fallback: '"⏳"' }),
  key({ key: 'retired', declared: true, set: '"🗑"', fallback: '"🗑"' }),
  key({ key: 'shipped', declared: true, set: '"✅"', fallback: '"✅"' }),
  key({ key: 'undesigned', declared: true, set: '["💭"]', fallback: '["💭"]' }),
  key({ key: 'working', fallback: '"🛠"' }),
)

describe('RG53: the set comes from the project', () => {
  it('finds every marker the config names, once each', () => {
    const found = markersOf(THIS_PROJECT).map((one) => one.marker)

    expect(found).toEqual(['⏸', '🚫', '📋', '💭', '⏳', '🛠', '🗑', '✅'])
  })

  it('keeps a marker that several keys name as one entry, not as several', () => {
    // The working glyph is in the open set too. Drawing it twice would be drawing the
    // config's shape rather than the project's states.
    const working = meaningOf(THIS_PROJECT, '🛠')

    expect(working?.roles).toEqual(['open', 'working'])
  })

  it('uses a key nobody declared, because undeclared is not absent', () => {
    // `markers.working` is undeclared in this project and this project still has one.
    expect(meaningOf(THIS_PROJECT, '🛠')).not.toBeNull()
    expect(meaningOf(THIS_PROJECT, '⏸')?.label).toBe('deferred')
  })

  it('prefers what the file set over what the build falls back to', () => {
    const theirs = config(key({ key: 'shipped', declared: true, set: '"🎉"', fallback: '"✅"' }))

    expect(markersOf(theirs).map((one) => one.marker)).toEqual(['🎉'])
  })

  it('knows nothing about a codepoint this project does not declare', () => {
    // A line carrying it is one the grammar did not accept, and inventing a meaning would
    // draw it as a status rather than as the anomaly it is.
    expect(meaningOf(THIS_PROJECT, '🔥')).toBeNull()
  })

  it('answers an empty config with an empty list rather than a guess', () => {
    expect(markersOf(config())).toEqual([])
  })
})

describe('RG53: what a glyph is labelled', () => {
  it('says the particular role rather than the set it belongs to', () => {
    expect(meaningOf(THIS_PROJECT, '🛠')?.label).toBe('working')
    expect(meaningOf(THIS_PROJECT, '💭')?.label).toBe('undesigned')
    expect(meaningOf(THIS_PROJECT, '⏳')?.label).toBe('partial')
  })

  it('says the set where that is genuinely all there is', () => {
    expect(meaningOf(THIS_PROJECT, '📋')?.label).toBe('open')
  })

  it('keeps both where two particular keys name the same glyph', () => {
    expect(labelOf(['open', 'partial', 'working'])).toBe('partial / working')
  })

  it('gives every marker something to say', () => {
    for (const meaning of markersOf(THIS_PROJECT)) expect(meaning.label).not.toBe('')
  })
})

describe('RG53: open is a question of its own', () => {
  it('is not answered by the label', () => {
    // The working marker is labelled `working` and is still open; a screen filtering by
    // the label would lose it.
    const working = meaningOf(THIS_PROJECT, '🛠')

    expect(working?.label).toBe('working')
    expect(working && isOpen(working)).toBe(true)
  })

  it('is false for the ones that leave the roadmap', () => {
    for (const marker of ['✅', '🗑', '⏸']) {
      const meaning = meaningOf(THIS_PROJECT, marker)
      expect(meaning && isOpen(meaning)).toBe(false)
    }
  })
})

describe('RG53: however the file spells it', () => {
  it('takes the quotes off a bare scalar', () => {
    expect(
      markersOf(config(key({ key: 'shipped', set: "'✅'" }))).map((one) => one.marker),
    ).toEqual(['✅'])
  })

  it('reads an array as the several markers it is', () => {
    expect(
      markersOf(config(key({ key: 'open', set: '["a", "b"]' }))).map((one) => one.marker),
    ).toEqual(['a', 'b'])
  })

  it('ignores a key that names nothing at all', () => {
    expect(
      markersOf(config(key({ key: 'open', set: '[]' }), key({ key: 'shipped', set: '""' }))),
    ).toEqual([])
  })

  it('reads only the markers table, whatever else the config carries', () => {
    const mixed = config(
      key({ key: 'shipped', set: '"✅"' }),
      {
        table: 'files',
        key: 'roadmap',
        address: 'files.roadmap',
        declared: true,
        set: '"docs/ROADMAP.md"',
        fallback: null,
      },
      {
        table: 'limits',
        key: 'line',
        address: 'limits.line',
        declared: true,
        set: '320',
        fallback: '320',
      },
    )

    expect(markersOf(mixed).map((one) => one.marker)).toEqual(['✅'])
  })
})
