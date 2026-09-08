import { createRequire } from 'node:module'
import { readFileSync } from 'node:fs'
import path from 'node:path'

import { AA_LARGE, AA_NON_TEXT, AA_TEXT, contrastOf, saidOfRatio as said } from '@rk/core'
import { describe, expect, it } from 'vitest'

/**
 * RG54: the contrast this app actually renders, in both grounds.
 *
 * The values are read out of the two stylesheets that produce them — the design system's,
 * and this app's own accent block — because a fixture of colours copied here would be a
 * test of the copy. `oklch()` is a literal in both, so the maths in `core` can have it.
 *
 * jsdom is no help: it does not compute `oklch()`, so `getComputedStyle` hands back the
 * string it was given and a test asking the browser would assert on its own input.
 */
const require_ = createRequire(import.meta.url)

const PACKAGE_CSS = readFileSync(require_.resolve('@viglet/viglet-design-system/styles'), 'utf8')
const APP_CSS = readFileSync(path.join(import.meta.dirname, 'index.css'), 'utf8')

/**
 * Every `--token: value` in the blocks a selector opens, later winning over earlier.
 *
 * Deliberately not a CSS parser: these two files spell their token blocks as flat
 * declaration lists, and anything cleverer would be this app knowing a format it has no
 * business knowing. A token that stops being found fails the pairs below by name.
 */
function tokensUnder(source: string, selector: string): Map<string, string> {
  // Comments first: a declaration is `name: value;`, and a comment sitting between two of
  // them ends up glued to the front of the next name, which then silently is not a token.
  const css = source.replace(/\/\*[\s\S]*?\*\//g, '')
  const found = new Map<string, string>()
  const blocks = new RegExp(`${selector}\\s*\\{([^}]*)\\}`, 'g')

  let block = blocks.exec(css)
  while (block !== null) {
    for (const declaration of (block[1] ?? '').split(';')) {
      const at = declaration.indexOf(':')
      if (at < 0) continue
      const name = declaration.slice(0, at).trim()
      if (name.startsWith('--')) found.set(name, declaration.slice(at + 1).trim())
    }
    block = blocks.exec(css)
  }
  return found
}

/**
 * Follow a token that points at another token.
 *
 * `var(--x)` is a value the browser resolves, so resolving it here is reading what gets
 * rendered rather than passing over it — `--vg-ring` is the accent in dark exactly this
 * way. `color-mix` and anything else stays unread and fails by name, which is the point:
 * only the indirection whose answer is knowable is followed.
 */
function resolve(tokens: Map<string, string>, value: string, depth = 4): string {
  const points = /^var\(\s*(--[\w-]+)\s*\)$/.exec(value.trim())
  if (points === null || depth === 0) return value

  const next = tokens.get(points[1] ?? '')
  return next === undefined ? value : resolve(tokens, next, depth - 1)
}

/** The light ground: the package's `:root`, then this app's, which overrides it. */
const LIGHT = new Map([...tokensUnder(PACKAGE_CSS, ':root'), ...tokensUnder(APP_CSS, ':root')])

/** The dark ground: the light one re-pointed by the package's dark block. */
const DARK = new Map([...LIGHT, ...tokensUnder(PACKAGE_CSS, '\\.dark,\\[data-theme=dark\\]')])

const GROUNDS: readonly [string, Map<string, string>][] = [
  ['light', LIGHT],
  ['dark', DARK],
]

/**
 * The pairs this app puts together, and what each has to clear.
 *
 * Every one of these is on the screen or one component away from it. A pair nobody
 * renders would be a number this test defends for no reason.
 */
const PAIRS: readonly {
  readonly what: string
  readonly front: string
  readonly behind: string
  readonly least: number
}[] = [
  {
    what: 'body text on the ground',
    front: '--vg-foreground',
    behind: '--vg-background',
    least: AA_TEXT,
  },
  {
    what: 'muted text on the ground',
    front: '--vg-muted-foreground',
    behind: '--vg-background',
    least: AA_TEXT,
  },
  // Muted text on a card, which is what this screen renders. Not muted text on `--vg-muted`:
  // that pair is 4.33:1 in light and nothing here puts them together — filed rather than
  // enforced, because enforcing a pair nobody renders defends a number for no reason.
  {
    what: 'muted text on a card',
    front: '--vg-muted-foreground',
    behind: '--vg-card',
    least: AA_TEXT,
  },
  {
    what: 'card text on a card',
    front: '--vg-card-foreground',
    behind: '--vg-card',
    least: AA_TEXT,
  },
  {
    what: 'popover text on a popover',
    front: '--vg-popover-foreground',
    behind: '--vg-popover',
    least: AA_TEXT,
  },
  {
    what: 'a primary button label',
    front: '--vg-primary-foreground',
    behind: '--vg-primary',
    least: AA_TEXT,
  },
  {
    what: 'a secondary badge label',
    front: '--vg-secondary-foreground',
    behind: '--vg-secondary',
    least: AA_TEXT,
  },
  {
    what: 'an accent surface label',
    front: '--vg-accent-foreground',
    behind: '--vg-accent',
    least: AA_TEXT,
  },
  {
    what: 'a border against the ground',
    front: '--vg-border',
    behind: '--vg-background',
    least: 1.2,
  },
  {
    what: 'a focus ring against the ground',
    front: '--vg-ring',
    behind: '--vg-background',
    least: AA_NON_TEXT,
  },
  {
    what: 'a destructive label on the ground',
    front: '--vg-destructive',
    behind: '--vg-background',
    least: AA_LARGE,
  },
]

describe('RG54: the stylesheets this test reads', () => {
  it('found both of them, so the pairs below are about something', () => {
    expect(LIGHT.size).toBeGreaterThan(20)
    expect(DARK.size).toBeGreaterThanOrEqual(LIGHT.size)
  })

  it('sees the dark block re-point the ground, which is the whole of RG52', () => {
    expect(DARK.get('--vg-background')).not.toBe(LIGHT.get('--vg-background'))
    expect(DARK.get('--vg-foreground')).not.toBe(LIGHT.get('--vg-foreground'))
  })

  it("reads this app's own accent, which overrides the package", () => {
    expect(LIGHT.get('--vg-accent-text')).toBe(
      tokensUnder(APP_CSS, ':root').get('--vg-accent-text'),
    )
  })
})

describe.each(GROUNDS)('RG54: contrast in %s', (ground, tokens) => {
  it.each(PAIRS)('$what clears its threshold', ({ front, behind, least }) => {
    const declared = tokens.get(front)
    const behindDeclared = tokens.get(behind)

    // A token that has gone missing is a failure by name, not a skipped case.
    expect(declared, `${front} is not declared in ${ground}`).toBeDefined()
    expect(behindDeclared, `${behind} is not declared in ${ground}`).toBeDefined()

    const above = resolve(tokens, declared ?? '')
    const below = resolve(tokens, behindDeclared ?? '')
    const ratio = contrastOf(above, below)

    // And so is one that stopped being a literal: `color-mix` resolves to something, and a
    // check that quietly passed over it is one whose coverage shrinks as the package grows.
    expect(
      ratio,
      `${front} on ${behind} in ${ground} is not a pair of oklch literals: ${above} on ${below}`,
    ).not.toBeNull()

    expect(
      ratio ?? 0,
      `${front} on ${behind} in ${ground} is ${said(ratio ?? 0)}, under ${String(least)}:1`,
    ).toBeGreaterThanOrEqual(least)
  })
})

describe("RG54: this app's own accent, which is the value it added", () => {
  it('carries text on the light ground', () => {
    const ratio = contrastOf(
      LIGHT.get('--vg-accent-text') ?? '',
      LIGHT.get('--vg-background') ?? '',
    )

    expect(ratio, `the accent is ${said(ratio ?? 0)} on light`).toBeGreaterThanOrEqual(AA_LARGE)
  })

  it('carries text on the dark ground, which is why there are two of it', () => {
    // `--vg-accent-text-dark` exists because amber at full chroma does not carry text on
    // light; the dark one has the opposite job and nobody had checked it.
    const ratio = contrastOf(
      LIGHT.get('--vg-accent-text-dark') ?? '',
      DARK.get('--vg-background') ?? '',
    )

    expect(ratio, `the dark accent is ${said(ratio ?? 0)} on dark`).toBeGreaterThanOrEqual(AA_LARGE)
  })

  it('would fail if the accent were the bright one on light, which is the trap', () => {
    // The control: the reason two accent tokens exist is that this pair does not clear.
    const wrong = contrastOf(
      LIGHT.get('--vg-accent-from') ?? '',
      LIGHT.get('--vg-background') ?? '',
    )

    expect(wrong).not.toBeNull()
    expect(wrong ?? 0).toBeLessThan(AA_LARGE)
  })
})
