import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { messageKeys } from '@rk/core'
import { describe, expect, it } from 'vitest'

/**
 * RG183: every key the catalogue declares is one a screen says.
 *
 * RG125 compares the two locales and reports a key one declares and the other misses.
 * Nothing compared either of them against the screens, so a key declared in both and said by
 * neither passed every gate: the pseudo-locale run walks the catalogue and asserts each key
 * answers, which a dead key does, and the duplicate check reads the bundles alone. That is
 * how `filing.id` and `filing.section` sat in both locales through a whole task.
 *
 * The cost is not the dead string. It is that the catalogue stops being the list of what the
 * app says, so reading it tells you about screens that do not exist.
 *
 * **The read is the sources.** Every key reaches a screen spelled out — `say('task.binds')`,
 * or a table mapping something to a `MessageKey` — so a scan of this package for that
 * spelling is the used set, and the catalogue less that set is the dead one. A key composed
 * at run time would be invisible to it: none is today, and this is the guard that keeps it
 * that way.
 *
 * It runs here rather than beside the locale comparison because the comparison is `core`'s
 * and `core` has no filesystem. What it reads is sources, which starts nothing — so it is a
 * fast test, the way `suites.test.ts` reads every test file and is one.
 */

/**
 * Every package's sources, not this one's alone.
 *
 * A key is spelled where something decides to say it, and that is not always a screen: the
 * tables in `core` that map a state to a sentence — a settings loss, an unreadable answer, a
 * narrowed listing — name their keys there, and the menu the shell builds names its own. A
 * scan of the renderer alone would report every one of those as dead.
 */
const SOURCES = [
  path.resolve(import.meta.dirname),
  path.resolve(import.meta.dirname, '..', '..', 'core', 'src'),
  path.resolve(import.meta.dirname, '..', '..', 'shell', 'src'),
]

/** Which files can say a key: every source, tests included — a test says them too. */
function everySource(at: string): string[] {
  return readdirSync(at, { withFileTypes: true }).flatMap((entry) => {
    const here = path.join(at, entry.name)
    if (entry.isDirectory()) return everySource(here)
    return /[.]tsx?$/.test(entry.name) ? [here] : []
  })
}

/**
 * Every key something says, which is not every key something spells.
 *
 * A key is spelled twice in this repository: once where the catalogue declares it, and once
 * wherever something decides to say it. The two are told apart by shape and not by file —
 * a declaration is the key followed by a colon, and a use is the key anywhere else:
 * `say('task.binds')`, `BASE['task.binds']`, or a table whose *value* is the key. The file
 * rule was tried first and is vacuous: excluding the catalogue also drops the tables inside
 * it that name keys, and including it makes every key look said. Measured both ways, by
 * planting a key nothing says.
 *
 * What this cannot see is a key built at run time, which is the shape this guard exists to
 * keep out: a key nothing spells is a key nothing can be shown to say.
 */
function spelled(): Set<string> {
  const said = new Set<string>()
  const declared = /^\s*['"][a-z][a-zA-Z]*(?:[.][a-zA-Z-]+)+['"]\s*:/
  const quoted = /['"]([a-z][a-zA-Z]*(?:[.][a-zA-Z-]+)+)['"]/g

  for (const file of SOURCES.flatMap(everySource)) {
    for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
      // A catalogue entry is a quoted key at the head of its own line with a colon after it.
      // A ternary — `over ? 'a.over' : 'a.under'` — also puts a colon after a key, which is
      // why the head of the line is what decides and not the colon alone.
      if (declared.test(line)) continue
      for (const match of line.matchAll(quoted)) {
        const key = match[1]
        if (key !== undefined) said.add(key)
      }
    }
  }
  return said
}

describe('RG183: the key nobody says', () => {
  it('has a screen for every key the catalogue declares', () => {
    const said = spelled()
    const dead = messageKeys().filter((key) => !said.has(key))

    // A key here is either a sentence nothing draws — delete it — or a screen that was
    // meant to draw it and does not, which is the more interesting half.
    expect(dead).toEqual([])
  })

  it('reads the sources it claims to, which is what a clean answer rests on', () => {
    // The guard on the guard: a scan pointed at nothing reports a clean catalogue in the
    // same words as a clean one, which is the failure RG62 taught this repository.
    const said = spelled()

    expect(SOURCES.flatMap(everySource).length).toBeGreaterThan(20)
    expect(said.has('task.binds')).toBe(true)
    expect(said.has('portfolio.title')).toBe(true)
  })
})
