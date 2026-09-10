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

/**
 * The two grounds, in the order a browser resolves them (RG107).
 *
 * Source order and not intent. `index.css` imports the package and then opens its own
 * `:root`, and `:root` and `.dark, [data-theme="dark"]` are unlayered and equally specific —
 * so a token this app overrides at `:root` beats the package's *dark* block, which is later
 * in nobody's sheet but earlier in this one.
 *
 * Modelling it the other way round is what let the dark focus ring be the light accent while
 * this test agreed it was not: the map said what the author meant and the browser rendered
 * what the file said. Every block, in the order it is written, is the only model that reads
 * the way the cascade does.
 *
 * The dark selector is a pattern and not a literal because the two sheets spell it
 * differently: the package ships it minified, and Prettier writes this app's across two
 * lines with the value quoted. Both are the block a browser applies.
 */
const DARK_SELECTOR = String.raw`\.dark,\s*\[data-theme=['"]?dark['"]?\]`

const LIGHT = new Map([...tokensUnder(PACKAGE_CSS, ':root'), ...tokensUnder(APP_CSS, ':root')])

const DARK = new Map([
  ...tokensUnder(PACKAGE_CSS, ':root'),
  ...tokensUnder(PACKAGE_CSS, DARK_SELECTOR),
  ...tokensUnder(APP_CSS, ':root'),
  ...tokensUnder(APP_CSS, DARK_SELECTOR),
])

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
  {
    what: 'muted text on a card',
    front: '--vg-muted-foreground',
    behind: '--vg-card',
    least: AA_TEXT,
  },
  // No screen puts these two together yet, and this is the exception to the rule above (RG90):
  // the package names them as a pair, so the first muted panel reaches for both. It was
  // 4.33:1 in light until the package darkened the foreground to 0.52 (VDS92, 2026.3.9).
  {
    what: 'muted text on a muted panel',
    front: '--vg-muted-foreground',
    behind: '--vg-muted',
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

describe('RG107: a token this app overrides, on the ground it did not mean to', () => {
  it('rings in the dark accent and not the light one', () => {
    // 3.57:1 against 10.7:1 — both clear the 3:1 a focus indicator owes, so contrast alone
    // said nothing while the wrong colour rendered. What is asserted is the value.
    expect(resolve(DARK, DARK.get('--vg-ring') ?? '')).toBe(
      resolve(DARK, DARK.get('--vg-accent-text-dark') ?? ''),
    )
    expect(resolve(DARK, DARK.get('--vg-ring') ?? '')).not.toBe(
      resolve(LIGHT, LIGHT.get('--vg-ring') ?? ''),
    )
  })

  it('leaves every other override this app makes reaching one ground only', () => {
    // The shape rather than the instance: any token declared at this app's `:root` that the
    // package re-points in dark lands on both grounds, because `:root` here is written after
    // that dark block. A second one would be the same defect with another name.
    const own = tokensUnder(APP_CSS, ':root')
    const packageDark = tokensUnder(PACKAGE_CSS, DARK_SELECTOR)
    const ownDark = tokensUnder(APP_CSS, DARK_SELECTOR)

    const leaking = [...own.keys()].filter((token) => packageDark.has(token) && !ownDark.has(token))

    expect(
      leaking,
      'these are overridden at `:root` and re-pointed by the package in dark, so the light' +
        " value wins in both. Declare each in this app's own dark block as well.",
    ).toEqual([])
  })
})

describe('RG105: the colour that says where you are', () => {
  /** What the package ships when nobody has claimed it: a neutral, at zero chroma. */
  const NEUTRAL = /oklch\(\s*[\d.]+%?\s+0\s+0\s*\)/

  it('claims `--primary` through the inputs and never through the token', () => {
    // One value set on `--vg-primary` here would land after the package's dark block at the
    // same specificity and in no layer, so it would win on *both* grounds and the dark one
    // would silently get the light value. The inputs are read per ground instead.
    const own = tokensUnder(APP_CSS, ':root')

    expect(own.get('--vg-primary'), 'set the four inputs, never the token').toBeUndefined()
    for (const input of [
      '--vg-primary-base',
      '--vg-primary-base-dark',
      '--vg-primary-foreground-base',
      '--vg-primary-foreground-base-dark',
    ]) {
      expect(own.get(input), `${input} is what claims the token on one ground`).toBeDefined()
    }
  })

  it.each(GROUNDS)('is this product`s colour and not the package`s grey in %s', (_, tokens) => {
    // The pair below already has to clear AA, and the package's own neutral clears it easily
    // — so contrast alone would pass a build that had quietly stopped claiming the token.
    // What says the mark is *this* product's is that it has colour at all.
    expect(resolve(tokens, tokens.get('--vg-primary') ?? '')).not.toMatch(NEUTRAL)
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
