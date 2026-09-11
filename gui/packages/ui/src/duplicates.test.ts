import { readdirSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG186: the copy nobody exported.
 *
 * RG62's gate reads a file for the names it **exports**: its pattern is anchored on `export`
 * before `const`, `function`, `class` or `type`, plus what an `export { … }` list carries. A
 * screen declaring `function Label()` for its own use and never exporting it is a copy that
 * gate cannot see — the ordinary shape of the mistake here, a component private to one
 * surface having no reason to be exported.
 *
 * It was found by moving one: a caption used by two screens became an exported helper, and
 * the gate reported it the moment it crossed that line. It had been sitting unexported in a
 * screen for weeks with the same name the design system publishes, and every run passed.
 *
 * **Unexported is where the drift is worse, not better.** A copy nobody exports is one
 * nobody can be pointed at from elsewhere, so it diverges quietly: the design system's
 * `Label` is a real `<label>` and the local ones were caption spans — two different things
 * sharing a name in one repository.
 *
 * The correction belongs in the package, since every consumer has the same hole. This is the
 * rule held here in the meantime, over this repository's own sources, reading the same
 * `exports.json` the package's gate reads so the two can never disagree about what is
 * published.
 */
const require_ = createRequire(import.meta.url)
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const ROOTS = ['packages/core/src', 'packages/shell/src', 'packages/ui/src']

/** Every name the design system publishes, off its own manifest rather than a list here. */
function published(): Set<string> {
  const manifest = require_('@viglet/viglet-design-system/exports.json') as {
    readonly entries: Readonly<Record<string, unknown>>
  }
  const names = new Set<string>()
  for (const value of Object.values(manifest.entries)) {
    if (Array.isArray(value)) for (const name of value) names.add(String(name))
    else if (value !== null && typeof value === 'object') {
      for (const under of Object.values(value)) {
        if (Array.isArray(under)) for (const name of under) names.add(String(name))
      }
    }
  }
  return names
}

/**
 * A declaration, exported or not.
 *
 * The package's own pattern with the `export` requirement taken out, which is the whole of
 * the difference: what it looks for is a name being declared, and whether anybody else can
 * import it says nothing about whether it is a copy.
 */
const DECLARED =
  /^\s*(?:export\s+)?(?:declare\s+)?(?:abstract\s+)?(?:const|let|var|function\*?|class|type|interface|enum)\s+([A-Za-z_$][\w$]*)/gm

/** The package's own escape hatch, honoured here so a deliberate collision is said once. */
const ALLOWED = /viglet-ds-allow-duplicate\s+([A-Za-z_$][\w$]*)/g

function everySource(at: string): string[] {
  return readdirSync(path.join(REPO, at), { withFileTypes: true }).flatMap((entry) => {
    const here = `${at}/${entry.name}`
    if (entry.isDirectory()) return everySource(here)
    return /[.]tsx?$/.test(entry.name) ? [here] : []
  })
}

function copies(): string[] {
  const names = published()
  const found: string[] = []
  for (const file of ROOTS.flatMap(everySource)) {
    const source = readFileSync(path.join(REPO, file), 'utf8')
    const excused = new Set([...source.matchAll(ALLOWED)].map((one) => one[1]))
    for (const match of source.matchAll(DECLARED)) {
      const name = match[1]
      if (name !== undefined && names.has(name) && !excused.has(name)) {
        found.push(`${file} declares ${name}`)
      }
    }
  }
  return found
}

describe('RG186: a name the design system publishes, declared here', () => {
  it('reads the package’s own manifest, which is what a clean answer rests on', () => {
    // The guard on the guard: a check reading nothing reports a clean tree in the same words
    // as a clean tree, which is the failure RG62 taught this repository.
    expect(published().size).toBeGreaterThan(100)
    expect(published().has('Label')).toBe(true)
    expect(ROOTS.flatMap(everySource).length).toBeGreaterThan(100)
  })

  it('finds none, exported or not', () => {
    expect(copies()).toEqual([])
  })
})
