// The desktop reader's pages, asserted against what the build produced (RK1704).
//
// gui/site/ is a third build, joined to this one in two places, and both fail silently:
//
//   the build order  `vite build` empties dist/, so the reader's copy runs last or its pages
//                    are missing from the deploy artefact.
//   the base prefix  the reader's build writes every canonical and asset path under its own
//                    base, so a base that drifted from where this copies it is a site whose
//                    every link 404s in production alone.
//
// These read dist/gui, so they run after `npm run build`, which is what CI does.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const siteDir = join(dirname(fileURLToPath(import.meta.url)), "..");
const placed = join(siteDir, "dist", "gui");

test("the reader's site is in the deploy artefact", () => {
  assert.ok(existsSync(join(placed, "index.html")), "dist/gui/index.html is missing");
});

test("its pages are addressed to where they are served", () => {
  const html = readFileSync(join(placed, "index.html"), "utf8");
  assert.match(html, /rel="canonical" href="https:\/\/alegauss\.github\.io\/roadkeep\/gui\/"/);
  assert.ok(!html.includes("/roadkeep-gui/"), "a path still names the retired base");
});
