import { mkdirSync, mkdtempSync, utimesSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'

import { afterAll, describe, expect, it } from 'vitest'

import { BUILD_DIRECTORIES, SOURCE_ROOTS } from './built'
import { newestBuilt, newestSource, oldestBuilt, staleBundle } from './freshness'

import { removeTree } from './scratch'

/**
 * RG96: whether a bundle is the code the tree holds.
 *
 * Real directories with real timestamps, because that is what the rule reads. The times are
 * set rather than waited for: a test that slept a second to make one file newer than another
 * would be a second of every run spent on the clock.
 */
const scratch: string[] = []

function tree(): string {
  const home = mkdtempSync(path.join(tmpdir(), 'rk-fresh-'))
  scratch.push(home)
  return home
}

/** A file, at a chosen moment. Seconds since the epoch, which is what `utimes` takes. */
function fileAt(home: string, name: string, seconds: number): string {
  const full = path.join(home, name)
  mkdirSync(path.dirname(full), { recursive: true })
  writeFileSync(full, 'x', 'utf8')
  utimesSync(full, seconds, seconds)
  return full
}

afterAll(() => {
  for (const home of scratch) removeTree(home)
})

describe('RG96: which file is newest', () => {
  it('reads only what a build reads', () => {
    // A README or a lockfile changing does not make a bundle wrong, and a rule that said it
    // did would send somebody to rebuild for nothing.
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)
    fileAt(home, 'src/notes.md', 9000)

    expect(path.basename(newestSource([path.join(home, 'src')]).file)).toBe('a.ts')
  })

  it('never walks into output or into somebody else`s package', () => {
    // Output under a source root would make every build its own newest source, and the
    // check would then never fire.
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)
    fileAt(home, 'src/dist/old.ts', 9000)
    fileAt(home, 'src/node_modules/other/index.ts', 9000)

    expect(path.basename(newestSource([path.join(home, 'src')]).file)).toBe('a.ts')
  })

  it('never counts a test file, which no build reads', () => {
    // The common case, and the one that would have turned this off within a week: editing
    // a test is what somebody does immediately before running the live suite.
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)
    fileAt(home, 'src/a.test.ts', 9000)

    expect(path.basename(newestSource([path.join(home, 'src')]).file)).toBe('a.ts')
  })

  it('says nothing for a root that is not there, rather than failing', () => {
    expect(newestSource([path.join(tree(), 'never-made')]).at).toBe(0)
    expect(newestBuilt([path.join(tree(), 'never-made')]).at).toBe(0)
  })

  it('takes the newest across several roots', () => {
    const home = tree()
    fileAt(home, 'one/a.ts', 1000)
    fileAt(home, 'two/b.ts', 5000)

    const newest = newestSource([path.join(home, 'one'), path.join(home, 'two')])

    expect(path.basename(newest.file)).toBe('b.ts')
  })
})

describe('RG96: what the run is told', () => {
  it('names the command when there is no build at all', () => {
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)

    const said = staleBundle([path.join(home, 'src')], [path.join(home, 'out')])

    expect(said).toContain('npm run build')
    expect(said).toContain('no build')
  })

  it('names the file that was edited after the build', () => {
    // The whole value of the sentence: a reader who is told *which* file learns whether the
    // edit was theirs, which a bare "stale" does not tell them.
    const home = tree()
    fileAt(home, 'src/renderer.ts', 9000)
    fileAt(home, 'out/bundle.js', 1000)

    const said = staleBundle([path.join(home, 'src')], [path.join(home, 'out')])

    expect(said).toContain('renderer.ts')
    expect(said).toContain('npm run build')
  })

  it('says nothing when the build is newer, which is the ordinary case', () => {
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)
    fileAt(home, 'out/bundle.js', 5000)

    expect(staleBundle([path.join(home, 'src')], [path.join(home, 'out')])).toBe('')
  })

  it('says nothing when the two are the same moment', () => {
    // A build that finished in the same second as the edit that triggered it is the common
    // case on a fast machine, and failing it would make the check noise.
    const home = tree()
    fileAt(home, 'src/a.ts', 4000)
    fileAt(home, 'out/bundle.js', 4000)

    expect(staleBundle([path.join(home, 'src')], [path.join(home, 'out')])).toBe('')
  })
})

describe('RG96: the roots this repository declares', () => {
  it('names one source root per package plus the page they are mounted into', () => {
    // A package added to the build and not here is a package whose edits the check cannot
    // see, which is the failure this whole module is about, one level up.
    for (const name of ['core', 'shell', 'ui']) {
      expect(SOURCE_ROOTS.some((root) => root.includes(name))).toBe(true)
    }
    expect(SOURCE_ROOTS.some((root) => root.endsWith('index.html'))).toBe(true)
  })

  it('names the two directories a build writes and a test then reads', () => {
    expect(BUILD_DIRECTORIES).toHaveLength(2)
    for (const directory of BUILD_DIRECTORIES) expect(directory).toContain('dist')
  })
})

/**
 * RG222: the half of the build that was not rebuilt.
 *
 * `npm run shots` ran `build:app`, which writes the shell's bundle and leaves the renderer's,
 * and the guard took the *newest* file across both directories — so the shell's fresh bundle
 * answered for the renderer's old one and two runs photographed a header that had been fixed.
 * Nothing reported anything, which is the direction that costs.
 */
describe('RG222: a build is only as fresh as its oldest half', () => {
  it('answers with the directory that was not rebuilt', () => {
    const home = tree()
    fileAt(home, 'shell/main.js', 9000)
    fileAt(home, 'ui/index.js', 1000)

    // In milliseconds, which is what an mtime is; `fileAt` takes the seconds `utimes` does.
    const both = [path.join(home, 'shell'), path.join(home, 'ui')]
    expect(oldestBuilt(both).at).toBe(1000 * 1000)
    expect(newestBuilt(both).at).toBe(9000 * 1000)
  })

  it('refuses a run where one bundle is older than the source, whatever the other says', () => {
    // The defect exactly: the shell rebuilt, the renderer not, and a source edit between.
    const home = tree()
    fileAt(home, 'src/Shell.tsx', 5000)
    fileAt(home, 'shell/main.js', 9000)
    fileAt(home, 'ui/index.js', 1000)

    const said = staleBundle(
      [path.join(home, 'src')],
      [path.join(home, 'shell'), path.join(home, 'ui')],
    )

    expect(said).toContain('Shell.tsx')
    expect(said).toContain('npm run build')
  })

  it('says nothing once both halves are newer, which is what one build leaves', () => {
    const home = tree()
    fileAt(home, 'src/Shell.tsx', 5000)
    fileAt(home, 'shell/main.js', 9000)
    fileAt(home, 'ui/index.js', 9000)

    expect(
      staleBundle([path.join(home, 'src')], [path.join(home, 'shell'), path.join(home, 'ui')]),
    ).toBe('')
  })

  it('reads a missing half as no build at all, not as a fresh one', () => {
    const home = tree()
    fileAt(home, 'src/a.ts', 1000)
    fileAt(home, 'shell/main.js', 9000)

    const said = staleBundle(
      [path.join(home, 'src')],
      [path.join(home, 'shell'), path.join(home, 'never-made')],
    )

    expect(said).toContain('no build')
  })
})
