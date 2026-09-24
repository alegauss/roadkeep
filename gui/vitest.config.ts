import { defineConfig } from 'vitest/config'

// Five projects over three packages, and each brings its own environment: `core` and
// `shell` run in Node, `ui` runs in jsdom because it may never touch anything else.
//
// RG64 split them along one line: **does this test start something?** A file named
// `*-live.test.*` spawns a Python roadkeep, an Electron window or a node script, and costs
// seconds where the rest cost milliseconds. Those are gates; the rest is what somebody runs
// between edits, and paying for both on every run is how a suite stops being run.
//
//   npm test          the fast ones — no process, no display, no bundle on disk
//   npm run test:live everything that starts something, which needs python and a build
//   npm run test:all  both, which is what CI runs
//
// `core` has no live half: nothing pure spawns, and a project matching no file is a project
// that reports an error rather than a suite.
//
// **`fsModuleCache` is set in each project below and not here** (RG234). A project inherits
// almost nothing from this file — only run-wide settings like `reporters` apply — so the flag
// written once here reads as if it covered the suite while covering nothing: it left a 25 KB
// cache and three warm runs no faster than three cold ones. Moved into `core`'s own config it
// left 4.4 MB and took that project from 5.05s to 1.5s. The measurements are in RG234's entry.
export default defineConfig({
  test: {
    // RG232: `default` prints the run, and the second one keeps it — a JSON report per run
    // that went red, under `.vitest/failures/`, so a test that fails once in a hundred runs
    // leaves its message and its assertion behind instead of scrolling past. A green run
    // writes nothing. `packages/shell/src/failure-report.ts` says why it is shaped that way.
    reporters: ['default', './packages/shell/src/failure-report.ts'],
    projects: [
      'packages/core',
      'packages/shell/vitest.config.ts',
      'packages/shell/vitest.live.config.ts',
      'packages/ui/vite.config.ts',
      'packages/ui/vitest.live.config.ts',
      // RG213: the renderer's tests that need a layout, in headless Chromium. Live, because
      // they start a browser.
      'packages/ui/vitest.browser.config.ts',
    ],
  },
})
