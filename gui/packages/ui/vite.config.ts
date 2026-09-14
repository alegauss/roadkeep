import path from 'node:path'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // The alias `components.json` points shadcn's generator at, so a component it writes
    // resolves the same way here as it does in the sibling consoles.
    alias: { '@': path.resolve(import.meta.dirname, 'src') },
  },
  // Relative, because the packaged app loads this bundle over `file://` and an
  // absolute base resolves to the drive root there rather than to the app.
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  test: {
    name: 'ui',
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    // RG64: two of these read the built bundle or run the design system's gate in a child
    // process. They are named `*-live.test.*` and run from `vitest.live.config.ts`, so that
    // `npm test` costs nothing a person would not want to pay between edits.
    // RG213: and the ones that need a layout run in Chromium from `vitest.browser.config.ts`.
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      'src/**/*-live.test.{ts,tsx}',
      'src/**/*.browser.test.{ts,tsx}',
    ],
    setupFiles: ['./src/test-setup.ts'],
    // Above the five seconds `test-setup.ts` gives a `findBy*`, and for that reason (RG232):
    // vitest's own default is five, so a wait that used its whole budget would be cut off by
    // the test timing out — which reports *test timed out* and throws away the message naming
    // what never appeared. A ceiling nothing reaches on a green run.
    testTimeout: 15_000,
  },
})
