import { markersOf, type ConfigPayload, type MarkerMeaning } from '@rk/core'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Marker } from './Marker'

/**
 * RG53: what a marker looks like, and what survives a machine with no glyph for it.
 *
 * The meanings come from `markersOf` rather than being written here, so this is a test of
 * the rendering and never a second table of what a marker means.
 */
const CONFIG: ConfigPayload = {
  version: '0.2.400',
  source: 'roadkeep.toml',
  keys: [
    { table: 'markers', key: 'open', address: 'markers.open', declared: true, set: '["📋", "🛠"]', fallback: null },
    { table: 'markers', key: 'working', address: 'markers.working', declared: false, set: null, fallback: '"🛠"' },
    { table: 'markers', key: 'shipped', address: 'markers.shipped', declared: true, set: '"✅"', fallback: null },
  ],
}

const MEANINGS = markersOf(CONFIG)

function meaning(marker: string): MarkerMeaning {
  const found = MEANINGS.find((one) => one.marker === marker)
  if (!found) throw new Error(`the fixture has no ${marker}`)
  return found
}

describe('RG53: a marker on screen', () => {
  it('draws the codepoint the project declared, not an icon of its own', () => {
    render(<Marker meaning={meaning('🛠')} />)

    expect(screen.getByTestId('marker-glyph').textContent).toBe('🛠')
  })

  it('says the word beside it, always', () => {
    // Not only when the glyph is missing: nothing can ask the browser whether a codepoint
    // came out as a tofu box, so a label shown on failure is one that never shows.
    render(<Marker meaning={meaning('🛠')} />)

    expect(screen.getByTestId('marker-label').textContent).toBe('working')
    expect(screen.getByTestId('marker-label').className).not.toContain('sr-only')
  })

  it('keeps the word reachable even where the row does not repeat it', () => {
    render(<Marker meaning={meaning('✅')} showLabel={false} />)

    const label = screen.getByTestId('marker-label')
    expect(label.textContent).toBe('shipped')
    expect(label.className).toContain('sr-only')
  })

  it('hides the glyph from a reader that would announce it as a name', () => {
    // The word is the accessible text; a screen reader saying "hammer and wrench" beside
    // "working" is one status read out twice, one of the times wrongly.
    render(<Marker meaning={meaning('📋')} />)

    expect(screen.getByTestId('marker-glyph').getAttribute('aria-hidden')).toBe('true')
  })

  it('holds the glyph in a box of its own width, so a column does not go ragged', () => {
    render(<Marker meaning={meaning('📋')} />)

    const glyph = screen.getByTestId('marker-glyph').className
    expect(glyph).toContain('w-5')
    expect(glyph).toContain('shrink-0')
  })

  it('asks for the face this app named, and no value of its own', () => {
    render(<Marker meaning={meaning('📋')} />)

    expect(screen.getByTestId('marker-glyph').getAttribute('style')).toContain('var(--font-marker)')
  })

  it('draws every marker the config named, whatever they are', () => {
    for (const one of MEANINGS) {
      const { unmount } = render(<Marker meaning={one} />)
      expect(screen.getByTestId('marker-glyph').textContent).toBe(one.marker)
      expect(screen.getByTestId('marker-label').textContent).toBe(one.label)
      unmount()
    }
  })
})
