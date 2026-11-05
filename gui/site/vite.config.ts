import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { siteThemeScript } from '@viglet/viglet-design-system/site'
import { THEME_KEY } from './src/lib/site-content.ts'

// A path of roadkeep's own Pages site since the app moved into its tree (RK1704): the site is
// served at https://alegauss.github.io/roadkeep/gui/ and every canonical, asset path and
// sitemap entry carries the prefix. roadkeep's site build copies dist/ to its dist/gui/.
export const BASE = '/roadkeep/gui/'

// The pre-paint theme script comes from the design system rather than being typed into
// index.html, so the page and the toggle cannot disagree about the rule (RK1714). Replace or
// throw, like the prerender: a template that lost its anchor would ship a flash of the wrong
// theme.
function themeScript(): Plugin {
  const anchor = '<!--theme-script-->'
  return {
    name: 'theme-script',
    transformIndexHtml(html) {
      if (!html.includes(anchor)) throw new Error(`index.html lost its ${anchor} anchor`)
      return html.replace(anchor, () => `<script>${siteThemeScript(THEME_KEY)}</script>`)
    },
  }
}

export default defineConfig({
  base: BASE,
  plugins: [react(), themeScript()],
  build: {
    // docs/ is roadkeep's, never a web root: the site builds to its own dist/.
    outDir: 'dist',
    emptyOutDir: true,
  },
})
