import { defineConfig } from 'vitest/config'

/**
 * The half of `shell` that starts nothing (RG64).
 *
 * The main process itself cannot be asserted without a display. What can be, and is, is
 * the policy it applies: the rules under `navigation.ts` are pure functions for exactly
 * that reason, and they run in milliseconds.
 *
 * Everything that spawns is named `*-live.test.ts` and runs from `vitest.live.config.ts`,
 * which is where the timeout and the one-file-at-a-time setting those tests need now live.
 * The exclusion below is what keeps `npm test` fast; `suites.test.ts` is what keeps the
 * naming honest, because a live test filed under a fast name is how a split quietly stops
 * holding.
 */
export default defineConfig({
  test: {
    name: 'shell',
    environment: 'node',
    include: ['src/**/*.test.ts'],
    exclude: ['**/node_modules/**', '**/dist/**', 'src/**/*-live.test.ts'],
  },
})
