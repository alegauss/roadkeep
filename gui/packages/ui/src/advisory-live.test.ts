import { existsSync, readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { BASE } from '@rk/core'
import { describe, expect, it } from 'vitest'

/**
 * RG61: an advisory that arrives with somebody else's package.
 *
 * `npm audit` reports `xlsx` at high severity — prototype pollution and a ReDoS — and it
 * reaches this repository as a transitive dependency of `@viglet/viglet-design-system`. The
 * package on npm is the unmaintained SheetJS build and no patched version is published
 * there, so there is nothing to upgrade to.
 *
 * What this file establishes is that the advisory is about the **install tree** and not
 * about the executable, and then holds that answer so it cannot quietly stop being true.
 * This app parses no spreadsheet, so nothing imports the code and the bundler leaves it out.
 *
 * The other half is `electron-builder.yml`, whose `files` is an allowlist of the three
 * packages' built output. `node_modules` is not in it, so an unimported dependency is not
 * merely unreferenced in the executable — it is not in it.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')
const BUNDLE_DIR = path.join(REPO, 'packages', 'ui', 'dist', 'assets')

/**
 * The version this answer was measured against.
 *
 * The wait-watcher the design asks for: the fix, if one is ever needed, is a release of
 * somebody else's package, and a wait nothing watches is a wait nobody re-reads. When this
 * moves, this file fails and the question above is asked again against the new tree.
 */
const MEASURED_AGAINST = '2026.3.9'

/** Strings the unmaintained build carries. Several, so a renamed export does not hide it. */
const MARKERS = ['xlsx', 'SheetJS', 'sheet_to_json', 'aoa_to_sheet', 'book_new']

function bundledScript(): string {
  // Whether there is a build at all, and whether it is older than the tree, is the live
  // run's own setup to refuse (RG96). What is left here is the directory this file reads.
  if (!existsSync(BUNDLE_DIR)) {
    throw new Error(`${BUNDLE_DIR} is not there, so there is no bundle to look in.`)
  }

  return readdirSync(BUNDLE_DIR)
    .filter((name) => name.endsWith('.js'))
    .map((name) => readFileSync(path.join(BUNDLE_DIR, name), 'utf8'))
    .join('\n')
}

describe('RG61: what the renderer actually ships', () => {
  it('reads a bundle that is this app, which is what makes the answer below mean anything', () => {
    // The control. A bundle that had not been built, or one read from the wrong place,
    // would contain none of the markers below for a reason that is not the good one.
    const bundle = bundledScript()

    expect(bundle.length).toBeGreaterThan(1000)
    expect(bundle).toContain(BASE['transport.absent'])
  })

  it.each(MARKERS)('carries no trace of %s', (marker) => {
    // Nothing imports it, so the bundler leaves it out. The day a design-system component
    // that does reach for it is used on a screen, this is what says so.
    expect(bundledScript()).not.toContain(marker)
  })
})

describe('RG61: what the executable would carry', () => {
  it('packages built output and no dependency tree at all', () => {
    // `files` is an allowlist. A `node_modules` entry here would put every installed
    // package into the installer, advisory or not — so its absence is the second and
    // stronger reason this advisory does not reach anybody who installs the app.
    const config = readFileSync(path.join(REPO, 'electron-builder.yml'), 'utf8')
    const listed = config
      .split('\n')
      .map((line) => /^\s+-\s+'?(!?[^'\s]+)'?\s*$/.exec(line)?.[1])
      .filter((entry): entry is string => entry !== undefined && entry.includes('/'))

    expect(listed.length).toBeGreaterThan(0)
    for (const entry of listed) {
      expect(entry, `${entry} is packaged and is not built output`).not.toContain('node_modules')
    }
  })
})

describe('RG61: the wait, watched', () => {
  it('was measured against the design system that is installed now', () => {
    // Not the declared range — the tree that is actually here. A caret range resolves to
    // whatever was published, and this answer is about the resolution and not the range.
    //
    // Read by path, because the package exports no `./package.json`: asking for it by
    // subpath throws `ERR_PACKAGE_PATH_NOT_EXPORTED`, the same wall RG93 records around the
    // compiler. A manifest under `node_modules` is always where its directory says.
    const installed = (
      JSON.parse(
        readFileSync(
          path.join(REPO, 'node_modules', '@viglet', 'viglet-design-system', 'package.json'),
          'utf8',
        ),
      ) as { version: string }
    ).version

    expect(
      installed,
      'the design system moved, so read RG61 again: whether `xlsx` still arrives with it,' +
        ' and whether it still stays out of the bundle. Update MEASURED_AGAINST when it does.',
    ).toBe(MEASURED_AGAINST)
  })

  it('still reaches this tree through the design system and not through anything here', () => {
    // If it ever stops being installed at all, the advisory is gone and this file can go
    // with it — which is a thing worth being told rather than left to be noticed.
    const ours = JSON.parse(
      readFileSync(path.join(REPO, 'packages', 'ui', 'package.json'), 'utf8'),
    ) as { dependencies: Record<string, string> }

    expect(Object.keys(ours.dependencies)).not.toContain('xlsx')
    expect(existsSync(path.join(REPO, 'node_modules', 'xlsx'))).toBe(true)
  })
})
