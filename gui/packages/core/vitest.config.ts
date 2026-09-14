import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    name: 'core',
    environment: 'node',
    include: ['src/**/*.test.ts'],
    // Transformed modules kept in `node_modules/.vitest-cache` between runs (RG234). Per
    // project because the root config's copy reaches none of them; `../../vitest.config.ts`
    // says what that cost and what this bought.
    fsModuleCache: true,
  },
})
