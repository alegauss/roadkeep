import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG234: where the transform cache is declared, and where declaring it does nothing.
 *
 * `fsModuleCache` keeps transformed modules in `node_modules/.vitest-cache` between runs.
 * It is a project setting, and a project inherits almost nothing from the root config — so
 * the flag written once at the root reads exactly like a suite-wide switch while being
 * none: it left a 25 KB cache and warm runs no faster than cold ones, against 12 MB and a
 * measurable win once each project declared it.
 *
 * That is the whole reason this is a test and not a comment. Both halves are invisible: a
 * project added to the root config without the flag re-transforms its graph on every run
 * and nothing says so, and a flag put back at the root looks like the fix and is not.
 *
 * Read off the config text, which is what `suites.test.ts` does for the other rule the
 * suite's shape carries. This file is fast: it reads text and starts nothing.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** The three `npm test` runs, each with the config file that configures it. */
const FAST = [
  { project: 'core', config: 'packages/core/vitest.config.ts' },
  { project: 'shell', config: 'packages/shell/vitest.config.ts' },
  // The renderer's is a Vite config, and `vitest.live.config.ts` spreads its `test` block.
  { project: 'ui', config: 'packages/ui/vite.config.ts' },
]

const ON = /fsModuleCache:\s*true/

function read(relative: string): string {
  return readFileSync(path.join(REPO, relative), 'utf8')
}

describe('RG234: the transform cache is declared per project', () => {
  it.each(FAST)('$project keeps its transforms between runs', ({ config }) => {
    expect(ON.test(read(config)), `${config} does not set fsModuleCache`).toBe(true)
  })

  it('and the root config does not, because a project would not inherit it', () => {
    const root = read('vitest.config.ts')
    expect(ON.test(root)).toBe(false)
    // The measurement that settled it, kept where somebody about to "fix" this would look.
    expect(root).toMatch(/RG234/)
  })
})
