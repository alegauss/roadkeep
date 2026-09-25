import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// A path of roadkeep's own Pages site since the app moved into its tree (RK1704): the site is
// served at https://alegauss.github.io/roadkeep/gui/ and every canonical, asset path and
// sitemap entry carries the prefix. roadkeep's site build copies dist/ to its dist/gui/.
export const BASE = '/roadkeep/gui/'

export default defineConfig({
  base: BASE,
  plugins: [react()],
  build: {
    // docs/ is roadkeep's, never a web root: the site builds to its own dist/.
    outDir: 'dist',
    emptyOutDir: true,
  },
})
