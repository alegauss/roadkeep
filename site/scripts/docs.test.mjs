// The documentation area, asserted against what the build produced.
//
// It is a second build with its own toolchain, joined to this one in three places, and each
// join fails silently rather than loudly:
//
//   the build order  `vite build` empties dist/, so the docs build runs after it or the whole
//                    area is missing from the deploy artefact — one directory nobody notices.
//   the base prefix  Astro rewrites the links it generates and not the ones written by hand,
//                    so an absolute href typed into a page 404s in production alone.
//   discovery        robots.txt and sitemap.xml come from ROUTE_META, which does not know
//                    these pages.
//
// These read dist/docs, so they run after `npm run build`, which is what CI does.
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const distDir = join(siteDir, "dist");
const docsDir = join(distDir, "docs");
const BASE = "/roadkeep/";

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

let pages;
before(() => {
  assert.ok(
    existsSync(docsDir),
    "dist/docs is missing, so run `npm run build` — which builds the docs area last, after "
      + "`vite build` has emptied dist/",
  );
  pages = walk(docsDir).filter((f) => f.endsWith(".html"));
});

const relative = (f) => f.replace(distDir, "").replace(/^[\\/]/, "").replace(/\\/g, "/");

test("the docs build reached the tree the deploy uploads", () => {
  // Not the directory's existence: the pages. An outDir pointed somewhere else leaves the
  // folder behind with the search index in it and no HTML.
  assert.ok(pages.length >= 2, `dist/docs holds ${pages.length} HTML file(s)`);
  assert.ok(existsSync(join(docsDir, "index.html")), "dist/docs/index.html missing");
});

test("robots names the docs sitemap, and the file it names was built", () => {
  // The prerender writes this line before the docs build has run, so it is a claim about a file
  // this side of the build has never seen. This is where it is held.
  const robots = readFileSync(join(distDir, "robots.txt"), "utf8");
  const named = [...robots.matchAll(/^Sitemap: (\S+)$/gm)].map((m) => m[1]);

  const docsSitemap = `https://alegauss.github.io${BASE}docs/sitemap-index.xml`;
  assert.ok(
    named.includes(docsSitemap),
    `robots.txt names ${named.join(", ")} and not the docs sitemap`,
  );
  assert.ok(
    existsSync(join(docsDir, "sitemap-index.xml")),
    "robots names a docs sitemap that is not in dist: the docs build did not run, or a later "
      + "`vite build` emptied dist/ after it did",
  );
});

test("every sitemap URL the docs area emits carries the base", () => {
  const index = readFileSync(join(docsDir, "sitemap-index.xml"), "utf8");
  const parts = [...index.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  assert.ok(parts.length > 0, "the docs sitemap index lists no sitemap");

  for (const part of parts) {
    const file = part.replace(`https://alegauss.github.io${BASE}docs/`, "");
    const xml = readFileSync(join(docsDir, file), "utf8");
    const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
    assert.ok(locs.length > 0, `${file} lists no URL`);
    for (const loc of locs) {
      assert.ok(
        loc.startsWith(`https://alegauss.github.io${BASE}docs/`),
        `${loc} does not carry ${BASE}docs/`,
      );
    }
  }
});

// The one that catches a hand-written link. Astro prefixes what it generates; a href or src
// typed into MDX is emitted verbatim, and locally the dev server serves it, so the first reader
// to find it is on the published site.
test("no absolute href or src in the docs escapes the base", () => {
  const escaped = [];
  for (const page of pages) {
    const html = readFileSync(page, "utf8");
    for (const [, attr, url] of html.matchAll(/\s(href|src)="(\/[^/"][^"]*)"/g)) {
      if (!url.startsWith(BASE)) escaped.push(`${relative(page)}: ${attr}="${url}"`);
    }
  }
  assert.deepEqual(
    escaped,
    [],
    "a root-absolute link that does not carry /roadkeep/ is served locally and 404s in "
      + "production, because GitHub Pages puts every path under the repository name",
  );
});

test("the search index was built and holds the pages", () => {
  // Pagefind is why this area needs no account and no service to be up: the index is a build
  // artefact, which is the only shape this project's non-goal against a server allows. An entry
  // file with no fragments is an index of nothing, which searches as an empty site.
  const entry = join(docsDir, "pagefind", "pagefind-entry.json");
  assert.ok(existsSync(entry), "dist/docs/pagefind/pagefind-entry.json missing");

  const fragments = existsSync(join(docsDir, "pagefind", "fragment"))
    ? readdirSync(join(docsDir, "pagefind", "fragment"))
    : [];
  assert.ok(fragments.length > 0, "the search index holds no page fragment");
});

test("every docs page has a plain-text twin beside it", () => {
  // The area's postbuild converts each page from the same render, and its own index names every
  // one. Asserted here as well because the two builds are separate: a docs build whose postbuild
  // did not run publishes pages an agent has to render HTML to read, which is the cost this
  // whole project exists to remove.
  const missing = pages
    .filter((p) => p.endsWith(`${"index"}.html`))
    .filter((p) => !existsSync(p.replace(/index\.html$/, "index.md")))
    .map(relative);
  assert.deepEqual(missing, [], "a docs page has no index.md twin");

  const llms = join(docsDir, "llms.txt");
  assert.ok(existsSync(llms), "the area's generated llms.txt index is missing");
});

test("the site's own llms.txt names the area's", () => {
  // An agent starting at the site root finds the pitch's twin and this index; without the line
  // naming the area it never learns those pages exist.
  const llms = readFileSync(join(distDir, "llms.txt"), "utf8");
  assert.ok(llms.includes("docs/llms.txt"), "site llms.txt does not name docs/llms.txt");
});

test("every docs page has a unique title and a canonical carrying the base", () => {
  const titles = new Set();
  for (const page of pages) {
    const html = readFileSync(page, "utf8");
    const title = html.match(/<title>([\s\S]*?)<\/title>/)?.[1];
    assert.ok(title, `${relative(page)} has no <title>`);
    assert.ok(!titles.has(title), `duplicate <title> in the docs: ${title}`);
    titles.add(title);

    const canonical = html.match(/<link rel="canonical" href="([^"]+)"/)?.[1];
    assert.ok(canonical, `${relative(page)} has no canonical`);
    assert.ok(
      canonical.startsWith(`https://alegauss.github.io${BASE}docs/`),
      `${relative(page)} is canonical at ${canonical}`,
    );
  }
});
