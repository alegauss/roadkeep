import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
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
    include: ['src/**/*.test.tsx'],
    setupFiles: ['./src/test-setup.ts'],
  },
})
