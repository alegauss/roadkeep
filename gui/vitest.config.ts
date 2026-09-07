import { defineConfig } from 'vitest/config'

// One command for the whole repository, and each package brings its own environment:
// `core` runs in Node because it may never touch a DOM, and `ui` runs in jsdom because
// it may never touch anything else. Both are headless, which is what lets the suite run
// in CI and over SSH. `shell` has no project yet — it is Electron's main process, and
// what is worth asserting about it needs the transport that RG48 puts under a test.
export default defineConfig({
  test: {
    projects: ['packages/core', 'packages/ui'],
  },
})
