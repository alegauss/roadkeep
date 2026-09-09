import { defineConfig } from 'vitest/config'

/**
 * The half of `shell` that starts something (RG64).
 *
 * A file named `*-live.test.ts` spawns: a real Python roadkeep, an Electron window, a node
 * script standing in for Claude Code. That costs seconds per call and needs `python` on
 * PATH plus the launcher this repository commits, so it is a gate rather than something to
 * run between edits — which is the whole of why it is a project of its own.
 *
 * The two settings below belong here and nowhere else. Both were bought by a real failure
 * and neither should slow down a suite that spawns nothing.
 */
export default defineConfig({
  test: {
    name: 'shell-live',
    environment: 'node',
    include: ['src/**/*-live.test.ts'],
    // A live call costs around two seconds and resolving an engine can take two of them.
    // Vitest's five-second default fails those for being slow rather than for being wrong.
    testTimeout: 60000,
    // One file at a time. Half of these build a fixture with a dozen engine calls and then
    // read it with several more, so running them in parallel puts twenty-odd Python
    // interpreters on a machine that has eight cores — and the reads that lose that race
    // fail for being starved rather than for being wrong. Observed: the portfolio row test
    // passing alone and failing in a full run, twice.
    fileParallelism: false,
    // Two things settled once and spent by every worker, both travelling as environment
    // variables because that is what crosses a fork.
    //
    //   fixture-cache  where a built fixture is kept for the rest of the run, so the same
    //                  shape is not scaffolded twenty-six times (RG68). Made here and
    //                  removed here: these are real governed projects, and the run that
    //                  made them is the run that owns them.
    //   live           what the engine said it was, asked once (RG84), so a rebuild
    //                  underneath the run is one answer at the start rather than
    //                  thirty-one files disagreeing about which program they read.
    //   built          that there is a build and that it is not older than the tree, so a
    //                  run whose subject is on disk is a run about this code (RG96).
    globalSetup: ['./src/built-setup.ts', './src/fixture-cache.ts', './src/live.ts'],
  },
})
