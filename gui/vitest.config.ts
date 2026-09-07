import { defineConfig } from 'vitest/config'

// One command for the whole repository, and each package brings its own environment:
// `core` and `shell` run in Node, `ui` runs in jsdom because it may never touch anything
// else. All three are headless, which is what lets the suite run in CI and over SSH —
// nothing here starts Electron, and what `shell` asserts is the policy its main process
// applies rather than the process itself.
export default defineConfig({
  test: {
    projects: ['packages/core', 'packages/shell', 'packages/ui'],
  },
})
