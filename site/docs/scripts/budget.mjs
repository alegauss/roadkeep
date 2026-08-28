// The area's budget, held by something that refuses (RK1409).
//
// `budget.mjs` declares the numbers and argues them; this counts and says no. It runs in
// `prebuild`, so a page written over the ceiling fails before it is ever rendered — which is
// the whole point, and the difference between this and a linter that asks an author to delete
// work they have already done.
//
// Two things are counted apart, because two things are being bounded:
//
//   * **prose an author wrote** — what the budget is over;
//   * **what the build wrote** — generated pages and the components inside a hand-written one.
//     A verb table is as long as the parser makes it, and cutting it would be editing a schema
//     to fit a budget.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { GENERATED, PAGES, WORDS } from "../budget.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, "..", "src", "content", "docs");

function* walk(where) {
  for (const name of readdirSync(where)) {
    const path = join(where, name);
    if (statSync(path).isDirectory()) yield* walk(path);
    else if (name.endsWith(".mdx") || name.endsWith(".md")) yield path;
  }
}

/** The words an author wrote: frontmatter, imports, fenced code and components taken out. */
function prose(text) {
  let body = text.startsWith("---") ? text.split("---").slice(2).join("---") : text;
  body = body
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/^import .*$/gm, " ")
    // A component's output is the build's, not the author's — including the ones that render
    // a whole page's worth of table.
    .replace(/<[^>]+>/g, " ");
  return body.split(/\s+/).filter(Boolean).length;
}

/** What a page has left after code, components and inline code are taken out — where a typed
 *  number would be a *claim* rather than an example. */
function claims(text) {
  let body = text.startsWith("---") ? text.split("---").slice(2).join("---") : text;
  return body
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/^import .*$/gm, " ")
    .replace(/<[^>]+>/g, " ")
    // A link's **target** is an address and not a sentence: `#L42` and a version in a URL are
    // not counts somebody stated. Its *text* is left in on purpose — that is prose a reader
    // sees, so a figure written as a link label is the same claim as writing it plainly.
    .replace(/\]\([^)]*\)/g, "] ");
}

//: A run of two or more digits left in prose. Every real figure in this area is *rendered* —
//: the tool counts its own tools, keys, codes and pages — so a number typed into a sentence is
//: either a count that will go stale or one another file already owns. One digit is left
//: alone: "six laws" and "two halves" are prose, not measurements.
const TYPED = /\b\d{2,}\b/g;

const over = [];
const stated = [];
let generated = 0;
let counted = 0;
const rows = [];

for (const path of walk(DOCS)) {
  const name = relative(DOCS, path).split(sep).join("/");
  if (GENERATED.some((one) => name.startsWith(`${one}/`))) {
    generated += 1;
    continue;
  }
  const text = readFileSync(path, "utf-8");
  const words = prose(text);
  const limit = PAGES[name] ?? WORDS;
  counted += 1;
  rows.push({ name, words, limit });
  if (words > limit) over.push({ name, words, limit });

  const typed = [...claims(text).matchAll(TYPED)].map((one) => one[0]);
  if (typed.length) stated.push({ name, typed: [...new Set(typed)] });
}

// Loud about what it did *not* bound, for the reason every other number in this project is
// stated: a count that silently skipped a directory reads exactly like one that covered it.
console.log(
  `[budget] ${counted} page(s) counted against ${WORDS} words ` +
    `(${Object.keys(PAGES).length} with their own number), ${generated} generated and not counted`,
);

if (stated.length) {
  const said = stated
    .map((one) => `  ${one.name}: ${one.typed.join(", ")}`)
    .join("\n");
  throw new Error(
    `[budget] ${stated.length} page(s) state a count in prose:\n${said}\n` +
      "  Every figure in this area is rendered from the tool or from the file that owns it, so\n" +
      "  a number typed into a sentence is one that goes stale with nothing reporting it.\n" +
      "  Render it, or say it without the number.",
  );
}

if (over.length) {
  const said = over
    .map((one) => `  ${one.name}: ${one.words} words, ${one.limit} allowed — cut ${one.words - one.limit}`)
    .join("\n");
  throw new Error(
    `[budget] ${over.length} page(s) over the area's budget:\n${said}\n` +
      "  The number is in site/budget.mjs with the argument above it. Raising it is a decision,\n" +
      "  and one whose first act is a finding is a number somebody lowers and raises again.",
  );
}

// And the other direction, which is what makes the figure worth printing: the widest page, so
// the next person to declare a number reads what this corpus is rather than re-deriving it.
const widest = rows.sort((a, b) => b.words - a.words)[0];
if (widest) {
  console.log(`[budget] widest is ${widest.name} at ${widest.words} of ${widest.limit}`);
}
