// The prerender, as the design system's `prerenderSite` (VDS215) runs it for every product site
// (RK1729): one render per route into the client build's template, the <head> patched by
// replace-or-throw so a drifted template fails the build, the Markdown twin beside each page,
// and the manifest and sitemap from the same route table — so a route that exists appears in
// each and a deleted one leaves all of them. It reads the SSR bundle `vite build --ssr` wrote,
// and the route metadata is the table routes.tsx has already asserted against the component map.
//
// What stays here is what the shared step cannot know: the twin converter, which is this
// page's own reading of its markup, and robots.txt, which names a second sitemap for the
// documentation area — a build this table will never list.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { lastAuthoredChange, prerenderSite } from "@viglet/viglet-design-system/vite";

import {
  render,
  renderStatic,
  ROUTE_META,
  canonicalUrl,
  outputDir,
  OG_IMAGE,
} from "../dist-server/entry-server.js";
import { htmlToMarkdown } from "./markdown.mjs";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const distDir = join(root, "dist");

// Not the build clock: a rebuild that changed nothing must not tell a crawler every page did.
// One date for the whole authored tree, because a date per route would need a second list.
const lastmod = lastAuthoredChange(root);

prerenderSite({
  distDir,
  routes: ROUTE_META,
  render,
  canonicalUrl,
  outputDir,
  ogImage: OG_IMAGE,
  // Converted from the same render as the page, so the twin cannot drift from it.
  twin: (path) => htmlToMarkdown(renderStatic(path)),
  // No build timestamp: the same input builds byte-identical output.
  manifest: { name: "roadkeep", base: "/roadkeep/", llms: "llms.txt" },
  sitemap: { lastmod },
  robots: false,
  log: (line) => console.log(line),
});

// Absolute, because that is what makes the sitemaps discoverable without a submission. The
// documentation area under /docs is a second build with a second sitemap, and naming it here is
// what makes both halves of one deploy crawlable from one file — a claim about a file this
// script has not seen, which `docs.test.mjs` holds against the built output.
writeFileSync(
  join(distDir, "robots.txt"),
  `User-agent: *\nAllow: /\n\nSitemap: ${canonicalUrl("/")}sitemap.xml\n`
    + `Sitemap: ${canonicalUrl("/")}docs/sitemap-index.xml\n`,
);

console.log(
  `prerender: ${ROUTE_META.length} route(s) + twins + manifest.json`
    + `, sitemap.xml (lastmod ${lastmod ?? "omitted"}) and robots.txt written to dist/`,
);
