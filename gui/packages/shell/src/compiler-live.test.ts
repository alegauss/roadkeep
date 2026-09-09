import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { compilerLauncher } from './compiler'

/**
 * RG93: the path into somebody else's package, resolved for real.
 *
 * The dev loop spawns TypeScript's launcher by a path assembled from where its manifest
 * resolves, because the package exports no subpath that reaches it. That works and is
 * unowned: a release that renames or relocates the file breaks `npm run dev`, and the
 * report is somebody's morning rather than a red run.
 *
 * So this resolves the same path the dev loop resolves and starts it. Live, because it
 * spawns — and worth the second it costs, since the alternative assertion is a person
 * remembering to run the dev loop after every upgrade.
 */

describe('RG93: the compiler the dev loop runs', () => {
  it('resolves to a file that is there', () => {
    const launcher = compilerLauncher()

    expect(path.isAbsolute(launcher)).toBe(true)
    expect(existsSync(launcher)).toBe(true)
  })

  it('starts, and says which TypeScript it is', () => {
    // Existence is not enough: a file that is there and no longer a launcher fails the dev
    // run the same way. `--version` is the cheapest thing that proves it still runs.
    const said = execFileSync(process.execPath, [compilerLauncher(), '--version'], {
      encoding: 'utf8',
    })

    expect(said).toMatch(/Version \d+\.\d+/)
  })

  it('is reached by a path and not by a subpath the package exports', () => {
    // The reason this module exists. If TypeScript ever publishes the launcher, this fails
    // and the answer is to delete the assembly rather than to keep it beside a supported
    // import — which is a thing nobody would notice on their own.
    expect(() => import.meta.resolve('typescript/bin/tsc')).toThrow(/not defined by "exports"/)
  })
})
