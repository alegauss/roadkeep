import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

/**
 * One directory the live suite keeps its built fixtures in, for the length of one run.
 *
 * A fixture is scaffolded by the real write verbs — ten or so interpreter starts at a
 * second and a half each — and twenty-six of them are built per run across twenty-four
 * files. Most are the same project: twelve distinct shapes answer all twenty-six asks. So
 * the first ask for a shape builds it and every later one copies the directory, which is
 * milliseconds (RG68).
 *
 * **Scoped to the run and never longer.** A cache that outlived the run would be the thing
 * the design warns about: a contract passing green against a project the engine answering
 * today did not build. Keying that on a version is not enough here — this repository's own
 * engine is a modified working tree, and its revision does not move when somebody saves a
 * file. Building once per run is the reading that cannot be stale, and it is where nearly
 * all of the saving is anyway: the twenty-fifth build of one shape is the expensive one,
 * not the second run of the suite.
 *
 * The path travels to the workers as an environment variable because that is what crosses
 * a fork. Absent — a single file run straight from `vitest`, or `globalSetup` not having
 * run — every fixture is built from scratch, which is the behaviour this replaces and the
 * right thing to fall back to.
 */

export const CACHE_VAR = 'RK_FIXTURE_CACHE'

/** Where built fixtures are kept this run, or the empty string for no cache at all. */
export function cacheDirectory(): string {
  return process.env[CACHE_VAR] ?? ''
}

/**
 * Vitest's `globalSetup` for the live project: make the directory, and take it away again.
 *
 * The teardown matters more than the setup. These are real governed projects under the
 * system temp directory, and a run that left twelve of them behind would be a suite that
 * fills a disk one afternoon at a time.
 */
export function setup(): void {
  process.env[CACHE_VAR] = mkdtempSync(path.join(tmpdir(), 'rk-fixtures-'))
}

export function teardown(): void {
  const held = cacheDirectory()
  if (held === '') return
  rmSync(held, { recursive: true, force: true })
  delete process.env[CACHE_VAR]
}
