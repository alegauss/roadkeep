import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'shell',
    environment: 'node',
    // The main process itself cannot be asserted without a display. What can be, and is,
    // is the policy it applies: the rules under `navigation.ts` are pure functions for
    // exactly that reason.
    include: ['src/**/*.test.ts'],
    // Some tests here start a real Python roadkeep, which costs around two seconds per
    // call, and resolving an engine can take two of them. Vitest's five-second default
    // fails those for being slow rather than for being wrong. RG64 is the line that
    // separates these from the fast suite instead of raising a number.
    testTimeout: 30000,
  },
})
