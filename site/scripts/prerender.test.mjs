// The route pair, the twin per route, the sitemap and the social card, asserted against the
// built output. These read dist/, so they run after `npm run build`, which is what CI does.
// A claim that has gone false (a route with no file, a duplicate title, a twin that leaked the
// nav or the call to action, a card that is not 1200x630) fails here rather than staying
// invisible until somebody reads the page against the tool.
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const distDir = join(siteDir, "dist");

let manifest;
before(() => {
  const mf = join(distDir, "manifest.json");
  assert.ok(existsSync(mf), "dist/manifest.json is missing, so run `npm run build` first");
  manifest = JSON.parse(readFileSync(mf, "utf8"));
});

// One route, and that is the claim rather than an omission: the pitch is one scroll, and
// everything that wanted a second page went to the documentation area under /docs, which is a
// build with a sidebar and a search index rather than a route here.
const EXPECTED = ["/"];

test("every expected route is in the manifest", () => {
  const paths = manifest.routes.map((r) => r.path);
  for (const p of EXPECTED) assert.ok(paths.includes(p), `route ${p} missing from manifest`);
});

test("each route has its HTML and Markdown file at the stated size", () => {
  for (const r of manifest.routes) {
    const html = join(distDir, r.html);
    const md = join(distDir, r.markdown);
    assert.ok(existsSync(html), `${r.html} missing`);
    assert.ok(existsSync(md), `${r.markdown} missing`);
    assert.equal(statSync(html).size, r.htmlBytes, `${r.html} size drifted from manifest`);
    assert.equal(statSync(md).size, r.markdownBytes, `${r.markdown} size drifted from manifest`);
  }
});

test("each page has a unique title, its canonical, and an og:image", () => {
  const titles = new Set();
  for (const r of manifest.routes) {
    const html = readFileSync(join(distDir, r.html), "utf8");
    const title = html.match(/<title>([\s\S]*?)<\/title>/)?.[1];
    assert.ok(title, `${r.html} has no <title>`);
    assert.ok(!titles.has(title), `duplicate <title>: ${title}`);
    titles.add(title);
    assert.ok(html.includes(`<link rel="canonical" href="${r.url}"`), `${r.html} canonical wrong`);
    assert.ok(html.includes('property="og:image"'), `${r.html} has no og:image`);
  }
});

// The nav is anchors into this page, so a link written as a bare "#section" whose element was
// renamed is a link that silently does nothing: the browser sets the hash, finds no element of
// that id, and stays where it is. There is no router to rescue it. Every anchor is read and not
// the nav's alone, because the same mistake anywhere on the page has the same silence.
test("every in-page anchor has the element it names, on the page that carries it", () => {
  for (const r of manifest.routes) {
    const html = readFileSync(join(distDir, r.html), "utf8");
    const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));
    const targets = [...html.matchAll(/href="#([^"]*)"/g)].map((m) => m[1]);
    const dangling = targets.filter((t) => !ids.has(t));
    assert.deepEqual(
      dangling,
      [],
      `${r.html} links to #${dangling.join(", #")}, which is not on that page`,
    );
  }
});

test("no twin leaks the nav, the footer, an ad slot or a call to action", () => {
  // Strings that exist only in a subtree the converter is meant to drop whole. One of them in
  // a twin means the drop stopped matching, and what leaked with it is every link beside it.
  const banned = [
    "★ GitHub",
    "★ View on GitHub",
    "★ Star it on GitHub",
    "Not affiliated with",
    "Sponsored by",
  ];
  for (const r of manifest.routes) {
    const md = readFileSync(join(distDir, r.markdown), "utf8");
    assert.ok(md.trim().length > 0, `${r.markdown} is empty`);
    for (const b of banned) {
      assert.ok(!md.includes(b), `${r.markdown} leaked "${b}"`);
    }
  }
});

test("the twin carries the argument the page is for, not only its headings", () => {
  // A twin that resolved, looked like an answer and said nothing is the failure worth catching:
  // these five are the page's claim — the ledger, the measurement it started from, the law an
  // agent has to know, the verb it will call and the exit code that is the contract.
  const md = readFileSync(join(distDir, "index.md"), "utf8");
  for (const claim of ["What a turn needs", "186", "L4", "roadkeep add", "exit"]) {
    assert.ok(md.includes(claim), `the landing twin is missing "${claim}"`);
  }
  // The ledger is a grid of divs, so a converter that stopped matching it leaves six rows of
  // shattered fragments rather than a table. The pipe is what says it is still a table.
  assert.match(md, /^\| What a turn needs \|/m, "the context ledger is no longer a table");
});

test("the twin names the documentation area, which no nav or button of its own can", () => {
  // The nav entry and both calls to action live in subtrees the converter drops whole, so a
  // page whose only links to the area were those would leave a reader that is not a browser
  // finishing it without learning the area exists. The pointer is a sentence for that reason,
  // and this is what keeps it one.
  const md = readFileSync(join(distDir, "index.md"), "utf8");
  assert.match(
    md,
    /\[[^\]]+\]\(\/roadkeep\/docs\/\)/,
    "the landing twin carries no link to /roadkeep/docs/",
  );
});

test("every transcript on the page reached the twin as a fence", () => {
  // The transcripts are the page's evidence: a reader who cannot see what the commands print is
  // being asked to take the argument on trust. Six terminals plus the two panes of the
  // hand-edited comparison and the three copy lines, so the count is a floor and not an
  // equality — what is being caught is a converter that dropped them, not one that gained a
  // fence.
  const md = readFileSync(join(distDir, "index.md"), "utf8");
  const fences = (md.match(/^```$/gm) ?? []).length;
  assert.ok(fences >= 20, `the twin carries ${fences} fence markers, so transcripts went missing`);
  assert.equal(fences % 2, 0, "an unclosed fence: every block opens and closes");
});

test("the sitemap lists every route exactly once, and nothing else", () => {
  const xml = readFileSync(join(distDir, "sitemap.xml"), "utf8");
  const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);

  // Exactly once and in both directions: a route missing from the sitemap is one a crawler
  // finds only if something links inward, and a URL with no route is an address that 404s.
  assert.equal(locs.length, manifest.routes.length, "sitemap URL count differs from the routes");
  assert.equal(new Set(locs).size, locs.length, "the sitemap lists a URL twice");
  for (const r of manifest.routes) {
    assert.ok(locs.includes(r.url), `sitemap missing ${r.url}`);
  }
});

test("every sitemap URL carries the base prefix", () => {
  // The prefix GitHub Pages derives from the repository name. A sitemap that lost it would
  // publish addresses nothing serves.
  const xml = readFileSync(join(distDir, "sitemap.xml"), "utf8");
  for (const [, loc] of xml.matchAll(/<loc>([^<]+)<\/loc>/g)) {
    assert.ok(
      loc.startsWith(`https://alegauss.github.io${manifest.base}`),
      `${loc} does not carry ${manifest.base}`,
    );
  }
});

test("the sitemap states no lastmod it cannot derive, and never the build clock", () => {
  const xml = readFileSync(join(distDir, "sitemap.xml"), "utf8");
  const stamps = [...xml.matchAll(/<lastmod>([^<]+)<\/lastmod>/g)].map((m) => m[1]);
  for (const s of stamps) {
    assert.match(s, /^\d{4}-\d{2}-\d{2}$/, `lastmod ${s} is not a plain date`);
  }

  // Either every URL carries one or none does: a sitemap where some routes look fresher for
  // want of a source, rather than for having changed, is the misleading half.
  assert.ok(
    stamps.length === 0 || stamps.length === manifest.routes.length,
    "lastmod is on some routes and not others",
  );
});

test("robots allows everything and names a sitemap that was written", () => {
  const robots = readFileSync(join(distDir, "robots.txt"), "utf8");
  assert.match(robots, /^User-agent: \*$/m);
  assert.match(robots, /^Allow: \/$/m);

  const named = robots.match(/^Sitemap: (\S+)$/m);
  assert.ok(named, "robots.txt names no sitemap");

  // Absolute, and the file it names is the one beside it: a Sitemap: line pointing at nothing
  // is worse than no line, because it is a claim a crawler acts on.
  const url = named[1];
  assert.ok(url.startsWith("https://"), "the Sitemap: line is not absolute");
  assert.equal(url, `https://alegauss.github.io${manifest.base}sitemap.xml`);
  assert.ok(existsSync(join(distDir, "sitemap.xml")), "robots names a sitemap that is not there");
});

test("the social card is a 1200x630 PNG", () => {
  // The one the meta names. `roadkeep-social.png` beside it is 1280x640, which is what GitHub
  // wants for a repository preview and not the ratio Open Graph crops from — both ship, and
  // this asserts the one a platform actually fetches.
  const png = join(distDir, "assets", "og.png");
  assert.ok(existsSync(png), "dist/assets/og.png missing");
  const buf = readFileSync(png);
  assert.equal(buf.toString("ascii", 1, 4), "PNG", "og.png is not a PNG");
  assert.equal(buf.readUInt32BE(16), 1200, "og.png width");
  assert.equal(buf.readUInt32BE(20), 630, "og.png height");
});
