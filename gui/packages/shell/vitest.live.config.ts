import { availableParallelism } from 'node:os'

import { defineConfig } from 'vitest/config'

/**
 * Files run at once: one per four cores, and never fewer than one (RG130).
 *
 * The starvation below was interpreters per core — twenty-odd on eight — so what bounds it
 * is cores, and a yes or a no would be wrong on one of the two kinds of machine this runs
 * on. A GitHub runner has two to four, which makes this one and the gate exactly as serial
 * as it was; the workstation it was measured on has twenty-eight.
 */
const FILES_AT_ONCE = Math.max(1, Math.floor(availableParallelism() / 4))

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
    // Bounded by cores, and it was one file at a time. Half of these build a fixture with a
    // dozen engine calls and then read it with several more, so running them all at once put
    // twenty-odd Python interpreters on a machine with eight cores — and the reads that lost
    // that race failed for being starved rather than for being wrong. Observed: the
    // portfolio row test passing alone and failing in a full run, twice.
    //
    // **What moved it is the suite reading the way the app does** (RG130). RG122 held the
    // app's engine and not this one, and the setting stayed. Since `live.ts` reads through a
    // held `roadkeep mcp` per root, the run makes 400 interpreter starts where it made 579
    // and takes 339 seconds serial where it took 433. With every file in flight on 28 cores
    // it took 72; bounded by `FILES_AT_ONCE` — seven there — it took 87, 87 and 88 in three
    // runs back to back, all green. The bound is the careful half of that: the ratio the
    // failure was about, kept, with the cores the machine has.
    maxWorkers: FILES_AT_ONCE,
    // A worker count of its own is a group of its own: Vitest refuses two projects in one
    // group that bound their workers differently. After the others, which are milliseconds
    // beside this, so the order costs nothing and the group runs on the cores it was sized for.
    sequence: { groupOrder: 1 },
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
    // Per file, and not global: the suite's reads hold an engine per root since RG130, and
    // whatever a file's fixtures did not give back is closed when that file ends.
    setupFiles: ['./src/live-setup.ts'],
  },
})
