import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// GitHub Pages derives this from the repository name, so it is not a preference: the site is
// served at https://alegauss.github.io/roadkeep-gui/ and every canonical, asset path and
// sitemap entry carries the prefix. Renaming the repository moves every published URL at once.
export const BASE = '/roadkeep-gui/'

export default defineConfig({
  base: BASE,
  plugins: [react()],
  build: {
    // docs/ is roadkeep's, never a web root: the site builds to its own dist/.
    outDir: 'dist',
    emptyOutDir: true,
  },
})
