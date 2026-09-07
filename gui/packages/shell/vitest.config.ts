import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'shell',
    environment: 'node',
    // The main process itself cannot be asserted without a display. What can be, and is,
    // is the policy it applies: the rules under `navigation.ts` are pure functions for
    // exactly that reason.
    include: ['src/**/*.test.ts'],
  },
})
