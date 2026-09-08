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
export default defineConfig({
  test: {
    projects: [
      'packages/core',
      'packages/shell/vitest.config.ts',
      'packages/shell/vitest.live.config.ts',
      'packages/ui/vite.config.ts',
      'packages/ui/vitest.live.config.ts',
    ],
  },
})
