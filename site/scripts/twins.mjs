// A fetchable plain-text twin per page, converted from the same render (RK1410).
//
// `llms.txt` exists because a model reading this project should not have to render a landing
// page to learn what it is. An area published as HTML alone re-creates that problem one page
// at a time — and what a read costs an agent is this project's whole premise.
//
// **Converted from the built HTML, never authored a second time.** Most of these pages are
// half generated: a verb table comes off the parser, a finding page off the gate's own table,
// the walkthrough off a real run. A twin written from the Markdown source would carry the
// prose and none of that, and a twin written from the same JSON would re-declare the
// composition and let the two drift. One render, two outputs, so neither can disagree with
// the other.
//
// Runs as `postbuild`, because Astro empties its output directory before it writes.
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { parse } from "node-html-parser";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUILT = join(HERE, "..", "..", "docs", "guide");
const LLMS = join(HERE, "..", "..", "docs", "llms.txt");

//: Where a page's twin lives, relative to the page. One rule and not a table: an address a
//: caller has to look up is one a link handed to a session cannot be built from.
const TWIN = "index.md";

const HEADINGS = { h1: "#", h2: "##", h3: "###", h4: "####", h5: "#####", h6: "######" };
//: Chrome that is navigation rather than content. Starlight wraps the article in its own
//: shell, and a twin carrying the sidebar would be a hundred links per page.
const SKIP = new Set(["nav", "footer", "script", "style", "noscript", "button", "svg"]);

function text(node) {
  return node.text.replace(/\s+/g, " ").trim();
}

/** One element as Markdown. Blocks recurse; everything else is a run of text. */
function convert(node, out) {
  for (const child of node.childNodes) {
    const tag = child.rawTagName?.toLowerCase();
    if (!tag) {
      const run = child.text.replace(/\s+/g, " ");
      if (run.trim()) out.push(run.trim());
      continue;
    }
    if (SKIP.has(tag)) continue;

    if (HEADINGS[tag]) {
      out.push(`\n${HEADINGS[tag]} ${text(child)}\n`);
    } else if (tag === "p") {
      const run = text(child);
      if (run) out.push(`${run}\n`);
    } else if (tag === "pre") {
      out.push("```\n" + child.text.replace(/\s+$/, "") + "\n```\n");
    } else if (tag === "li") {
      const run = text(child);
      if (run) out.push(`- ${run}`);
    } else if (tag === "tr") {
      const cells = child.querySelectorAll("th, td").map((one) => text(one));
      if (!cells.length) continue;
      out.push(`| ${cells.join(" | ")} |`);
      // The separator a header row needs, emitted from the row that *is* the header rather
      // than from a count of rows seen: a table rendered without it is one paragraph in every
      // reader, and these tables are most of what a reference twin carries.
      if (child.querySelectorAll("th").length) {
        out.push(`| ${cells.map(() => "---").join(" | ")} |`);
      }
    } else if (tag === "dt") {
      out.push(`\n**${text(child)}**`);
    } else if (tag === "dd") {
      out.push(`${text(child)}\n`);
    } else {
      convert(child, out);
    }
  }
  return out;
}

function* pages(where) {
  for (const name of readdirSync(where)) {
    const path = join(where, name);
    if (statSync(path).isDirectory()) yield* pages(path);
    else if (name === "index.html") yield path;
  }
}

const written = [];
for (const path of pages(BUILT)) {
  const html = parse(readFileSync(path, "utf-8"));
  // Starlight's own wrapper for the page body. Anchored on its class rather than on a
  // position, so a theme upgrade that moves the article is an empty twin and a loud one below
  // rather than a file full of navigation.
  const article = html.querySelector(".sl-markdown-content");
  if (!article) continue;

  const title = html.querySelector("title")?.text?.split("|")[0]?.trim() ?? "";
  const body = convert(article, []).join("\n").replace(/\n{3,}/g, "\n\n").trim();
  const slug = relative(BUILT, dirname(path)).split(sep).join("/");
  writeFileSync(
    join(dirname(path), TWIN),
    `# ${title}\n\n${body}\n`,
    "utf-8",
  );
  written.push({ slug, title, words: body.split(/\s+/).filter(Boolean).length });
}

if (!written.length) {
  throw new Error(
    "[twins] no page carried `.sl-markdown-content` — the theme moved the article, and every " +
      "twin would have been navigation or nothing",
  );
}

// A twin with no body is worse than no twin: it resolves, it looks like an answer, and it says
// nothing. One empty page is a converter that stopped matching.
const empty = written.filter((one) => one.words < 20);
if (empty.length) {
  throw new Error(
    `[twins] ${empty.length} twin(s) came out empty: ${empty.map((one) => one.slug || "/").join(", ")}`,
  );
}

// The index. Generated rather than kept by hand, which is stronger than the check RK1410 asked
// for: a page cannot be added without an entry, because the entry is derived from the page.
const base = "https://alegauss.github.io/roadkeep/guide";
const index = [
  "# roadkeep — the documentation area",
  "",
  "> Every page here has a plain-text twin at its own address plus `index.md`, converted from",
  "> the same render as the page, so the two cannot disagree. This index is generated from what",
  "> the build produced.",
  "",
  "## Pages",
  "",
  ...written
    .sort((a, b) => a.slug.localeCompare(b.slug))
    .map((one) => `- [${one.title}](${base}/${one.slug ? `${one.slug}/` : ""}${TWIN})`),
  "",
];
writeFileSync(join(BUILT, "llms.txt"), index.join("\n"), "utf-8");

// And the hand-written one next door has to name it, or an agent that starts at the site root
// never learns these pages exist.
const llms = readFileSync(LLMS, "utf-8");
if (!llms.includes("guide/llms.txt")) {
  throw new Error(
    "[twins] docs/llms.txt does not name guide/llms.txt — an agent starting at the site root " +
      "would never find these pages",
  );
}

console.log(`[twins] ${written.length} twin(s) and an index naming every one`);
