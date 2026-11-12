// The prerender, as the design system's `prerenderSite` (VDS215) runs it for every product site
// (RK1729): one render per route into the client build's template, the <head> patched by
// replace-or-throw so a drifted template fails the build, the Markdown twin beside each page,
// and the manifest, sitemap and robots.txt from the same route table — so a route that exists
// appears in each and a deleted one leaves all of them. It reads the SSR bundle `vite build --ssr`
// wrote, and the route metadata is the table routes.tsx has already asserted against the
// component map.
//
// What stays here is what the shared step cannot know: the twin converter, which is this page's
// own reading of its markup, and the `rel="alternate"` link to that twin, which the step writes
// through `headTags` (VDS243) — the hook whose absence kept this script hand-written.
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { lastAuthoredChange, prerenderSite } from '@viglet/viglet-design-system/vite'

import {
  render,
  renderStatic,
  ROUTE_META,
  canonicalUrl,
  outputDir,
  OG_IMAGE,
  BASE,
} from '../dist-server/entry-server.js'
import { htmlToMarkdown } from './markdown.mjs'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const distDir = join(root, 'dist')

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// Not the build clock: a rebuild that changed nothing must not tell a crawler every page did.
// The authored tree is named, because this site's sources sit beside generated ones.
const lastmod = lastAuthoredChange(root, ['src', 'public', 'index.html'])

prerenderSite({
  distDir,
  routes: ROUTE_META,
  render,
  canonicalUrl,
  outputDir,
  ogImage: OG_IMAGE,
  // Each page names its Markdown twin, so an agent reading the HTML finds the flat file.
  headTags: (_route, canonical) => [
    `<link rel="alternate" type="text/markdown" href="${escapeHtml(canonical)}index.md" />`,
  ],
  // Converted from the same render as the page, so the twin cannot drift from it.
  twin: (path) => htmlToMarkdown(renderStatic(path)),
  // No build timestamp: the same input builds byte-identical output.
  manifest: { name: 'roadkeep-gui', base: BASE, llms: 'llms.txt' },
  sitemap: { lastmod },
  robots: true,
  log: (line) => console.log(line),
})

console.log(
  `prerender: ${ROUTE_META.length} route(s) + twins + manifest.json` +
    `, sitemap.xml (lastmod ${lastmod ?? 'omitted'}) and robots.txt written to dist/`,
)
