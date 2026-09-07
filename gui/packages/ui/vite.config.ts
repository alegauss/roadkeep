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
    setupFiles: ['./src/test-setup.ts'],
  },
})
