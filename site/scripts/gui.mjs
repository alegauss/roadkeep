// The desktop reader's site, placed at dist/gui/ (RK1704).
//
// gui/site/ is its own Vite build with its own base, `/roadkeep/gui/`, so what it writes is
// already addressed to where this copies it: one Pages deploy serves the pitch, the
// documentation area and the reader's pages, from one tree. Last in the chain for the
// documentation area's reason — `vite build` empties dist/, so anything placed earlier is
// deleted by the step after it.
//
// Copied rather than built into place: the reader's build writes to its own dist/ and its
// tests read that output there, so pointing it at this one would move what they assert on.
import { cpSync, existsSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUILT = join(HERE, "..", "..", "gui", "site", "dist");
const PLACED = join(HERE, "..", "dist", "gui");

if (!existsSync(join(BUILT, "index.html"))) {
  console.error(`gui: ${BUILT} holds no built site — run the reader's build first`);
  process.exit(1);
}
rmSync(PLACED, { recursive: true, force: true });
cpSync(BUILT, PLACED, { recursive: true });
console.log(`gui: the reader's site copied to ${PLACED}`);
