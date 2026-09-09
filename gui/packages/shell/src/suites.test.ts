import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

/**
 * RG64: what keeps the split holding.
 *
 * Two suites are only worth having while the line between them is true. A test that starts
 * something, filed under a fast name, makes `npm test` slowly become the slow one again —
 * and nobody notices, because the number creeps.
 *
 * So the rule is a name and this is what enforces it: **a test file that reaches outside
 * the process is called `*-live.test.*`**. Read off the source rather than off a list here,
 * because a list is a second place the answer lives.
 *
 * This file is itself fast: it reads text and starts nothing.
 */
const REPO = path.resolve(import.meta.dirname, '..', '..', '..')

/** The three source roots, and the two names a test can have. */
const ROOTS = ['packages/core/src', 'packages/shell/src', 'packages/ui/src']

/**
 * What reaching outside the process looks like in source.
 *
 * Every one of these either spawns something or depends on a build having happened. They
 * are named rather than inferred, so adding a new way out is a deliberate edit here.
 */
const REACHES_OUT: readonly { readonly what: string; readonly found: RegExp }[] = [
  { what: 'a child process', found: /from 'node:child_process'/ },
  { what: 'the engine', found: /createProcessTransport/ },
  // RG78 moved the transport into one module, so most live files no longer name the thing
  // that builds one. Opening on the seam is the same reach: it hands back an engine.
  { what: 'the live seam', found: /from '\.\/live'/ },
  { what: 'Electron', found: /spawnElectron|startApp\(/ },
  { what: 'an HTTP handler', found: /serveEngine/ },
  { what: 'a built fixture', found: /buildFixture/ },
  { what: 'a fake agent', found: /fakeClaude/ },
  // Patterns and not substrings: `'dist'` also appears as a value in an ignore list, and a
  // test that names a directory it never walks into has not reached anywhere.
  { what: 'the built bundle', found: /path\.join\([^)]*'dist'/ },
]

/**
 * This file, which names every marker above and would otherwise report itself.
 *
 * The one exemption, and it is structural rather than a judgement: a list of what to look
 * for cannot be scanned by the thing looking for it.
 */
const THE_SCANNER = 'suites.test.ts'

function testFilesUnder(root: string): string[] {
  const directory = path.join(REPO, root)
  return readdirSync(directory)
    .filter((name) => name.includes('.test.') && name !== THE_SCANNER)
    .map((name) => path.join(root, name))
}

const EVERY_TEST = ROOTS.flatMap(testFilesUnder)

function isLive(file: string): boolean {
  return path.basename(file).includes('-live.test.')
}

function reachesOut(file: string): string[] {
  const source = readFileSync(path.join(REPO, file), 'utf8')
  return REACHES_OUT.filter((way) => way.found.test(source)).map((way) => way.what)
}

describe('RG64: the line between the two suites', () => {
  it('reads every test file there is, so what follows is about all of them', () => {
    expect(EVERY_TEST.length).toBeGreaterThan(80)
    expect(EVERY_TEST.filter(isLive).length).toBeGreaterThan(20)
    expect(EVERY_TEST.filter((file) => !isLive(file)).length).toBeGreaterThan(40)
  })

  it('has no fast test that starts something', () => {
    // The whole rule. A file listed here belongs in the live suite and its name says so
    // once it is renamed — which is the fix, not an exception added below.
    const misfiled = EVERY_TEST.filter((file) => !isLive(file))
      .map((file) => ({ file, why: reachesOut(file) }))
      .filter((found) => found.why.length > 0)
      .map((found) => `${found.file} uses ${found.why.join(', ')}`)

    expect(
      misfiled,
      'a test that reaches outside the process is named `*-live.test.*`, so that' +
        ' `npm test` keeps costing what a person will pay between edits',
    ).toEqual([])
  })

  it('has no live test that starts nothing, because that one is paying the gate for free', () => {
    // The other direction, and a weaker claim: a live-named file that reaches out through
    // something this list does not name is not a defect. What it catches is a file renamed
    // by habit rather than because it starts something.
    const overpaying = EVERY_TEST.filter(isLive).filter((file) => reachesOut(file).length === 0)

    expect(overpaying).toEqual([])
  })
})
