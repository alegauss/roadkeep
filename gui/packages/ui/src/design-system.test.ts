import { createRequire } from 'node:module'

import { describe, expect, it } from 'vitest'

/**
 * RG39: the design system is a dependency, and these are the three ways that stops being
 * true without anyone noticing.
 *
 * The pattern is Shio's (`design-system-subpaths.test.mjs`) and the argument is theirs:
 * `^2026.3.5` *permits* a version that has the subpath, which is not the same as the
 * installed tree having it. A fresh install can resolve something older, and the failure
 * then lands on whoever next opens the repository rather than on whoever changed the
 * range.
 */
const require_ = createRequire(import.meta.url)

/** Every subpath this app's source imports. Adding an import here is the point. */
const REQUIRED = [
  '@viglet/viglet-design-system',
  '@viglet/viglet-design-system/styles',
  '@viglet/viglet-design-system/fonts',
  '@viglet/viglet-design-system/preset',
]

function resolutionError(specifier: string): string | null {
  try {
    require_.resolve(specifier)
    return null
  } catch (error) {
    return (error as NodeJS.ErrnoException).code ?? String(error)
  }
}

describe('RG39: the design system this app renders with', () => {
  it('resolves every subpath the source imports', () => {
    const broken = REQUIRED.map((specifier) => ({
      specifier,
      code: resolutionError(specifier),
    })).filter((entry) => entry.code !== null)

    expect(
      broken,
      'ERR_PACKAGE_PATH_NOT_EXPORTED means the installed version predates the subpath.' +
        ' Check `npm view @viglet/viglet-design-system version` and raise the floor in' +
        ' packages/ui/package.json - do not copy a local dist over node_modules, which makes it' +
        ' work on one machine and leaves everyone else to find out.',
    ).toEqual([])
  })

  it('would notice a subpath that is genuinely absent', () => {
    // The control. Without it, a `resolve` that silently succeeded for everything would
    // make the assertion above pass over nothing at all.
    expect(resolutionError('@viglet/viglet-design-system')).toBeNull()
    expect(resolutionError('@viglet/viglet-design-system/never-published')).toBe(
      'ERR_PACKAGE_PATH_NOT_EXPORTED',
    )
  })
})

/**
 * The renderer is a browser page. `boundaries` below is the check that keeps it one, and
 * it is a test rather than a compiler setting because `packages/ui/tsconfig.json` has to
 * carry Node's types for this file and for `vite.config.ts`.
 */
const sources = import.meta.glob('./**/*.{ts,tsx}', { query: '?raw', eager: true }) as Record<
  string,
  { default: string }
>

describe('RG39: what the renderer is allowed to import', () => {
  it('reads its own source, so the assertions below are about something', () => {
    expect(Object.keys(sources).length).toBeGreaterThan(4)
  })

  // RG58 moved the import boundary to `.oxlintrc.json`, where `no-restricted-imports` says
  // it for all three packages at once, reports the line, and catches the spellings a
  // regular expression over source text does not — a dynamic import, a re-export, a
  // `require`. What is left here is the rule oxlint has none of.

  it('names no colour of its own', () => {
    // Outside a test, as with the imports above. RG54 computes contrast over the tokens,
    // which means naming colours to check the arithmetic against — and a test cannot fail
    // to follow the ground, because nothing renders it.
    const offenders = Object.entries(sources)
      .filter(([file]) => !file.includes('.test.'))
      .filter(([, module]) =>
        /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\boklch\(|\bhsla?\(/.test(module.default),
      )
      .map(([file]) => file)

    expect(
      offenders,
      'a component spells a colour instead of naming a token. Every value comes from' +
        ' @viglet/viglet-design-system; a component that writes one cannot follow the ground' +
        ' when RG52 wires the switch.',
    ).toEqual([])
  })
})
