// The Markdown twin, converted from the same render as the page.
//
// The copy lives in the content module but the *composition* lives in the JSX, so the twin is
// produced from the rendered HTML — never authored a second time from the data, which would
// re-declare the composition and let the two drift. This is the same argument the area next
// door makes in site/docs/scripts/twins.mjs, one build over.
//
// What a twin is for decides what it drops. The reader is an agent evaluating this tool, and
// what it is paying for is the read: navigation, decorative glyphs, step numbers and the call
// to action are chrome that costs it tokens and answers nothing. The nav and footer go by tag,
// the glyphs by class, and the ad slots and the closing buttons by their data-twin="omit".
import { parse } from "node-html-parser";

// Whole subtrees that never belong in a twin.
const SKIP_TAGS = new Set(["NAV", "FOOTER", "BUTTON", "SCRIPT", "STYLE", "NOSCRIPT"]);
// Decorative chrome dropped by class: the badge's pulse dot, the card emoji, the step numbers,
// the ✕/✓ marks beside a list item, the section kicker, the terminal window bar and the hero's
// own mark.
const SKIP_CLASSES = new Set(["dot", "ico", "n", "m", "x", "eyebrow", "term-bar", "hero-mark"]);
// Elements that carry a run of text, not a block — rendered inline, never recursed as blocks.
const INLINE_TAGS = new Set(["SPAN", "B", "STRONG", "I", "EM", "CODE", "KBD", "A", "BR"]);
const HEADING = { H1: "#", H2: "##", H3: "###", H4: "####", H5: "#####", H6: "######" };

function decode(s) {
  return s
    .replace(/&#x([0-9a-fA-F]+);/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(parseInt(d, 10)))
    .replace(/&nbsp;/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

const collapse = (s) => s.replace(/\s+/g, " ");
const classList = (node) => {
  const c = node.getAttribute?.("class");
  return c ? c.split(/\s+/) : [];
};

function skipped(node) {
  if (SKIP_TAGS.has(node.rawTagName?.toUpperCase())) return true;
  if (node.getAttribute?.("data-twin") === "omit") return true;
  return classList(node).some((c) => SKIP_CLASSES.has(c));
}

// Every text node under a subtree, tags dropped and entities decoded.
function plainText(node) {
  if (node.nodeType === 3) return decode(node.rawText);
  if (node.nodeType !== 1) return "";
  return node.childNodes.map(plainText).join("");
}

// The raw text of a subtree with markup left in place (no decode). node-html-parser keeps a
// <pre>'s whole content as a single raw text node — colour spans and all — so the fence is
// cleaned by stripping the tags out of this and only then decoding entities. Ordering matters:
// an escaped `&lt;` in the content must survive the tag strip and decode after it.
function rawTextAll(node) {
  if (node.nodeType === 3) return node.rawText;
  if (node.nodeType !== 1) return "";
  return node.childNodes.map(rawTextAll).join("");
}

function fenced(text) {
  const body = text.replace(/^\n+/, "").replace(/\n+$/, "");
  return "```\n" + body + "\n```";
}

function fencedFrom(node) {
  return fenced(decode(rawTextAll(node).replace(/<[^>]+>/g, "")));
}

// --- inline: a run with **bold**, *italic*, `code` and [links] ---
function inline(node) {
  if (node.nodeType === 3) return collapse(decode(node.rawText));
  if (node.nodeType !== 1) return "";
  if (skipped(node)) return "";
  const tag = node.rawTagName.toUpperCase();
  const kids = () => node.childNodes.map(inline).join("");
  switch (tag) {
    case "CODE":
    case "KBD":
      return "`" + collapse(plainText(node)) + "`";
    case "B":
    case "STRONG": {
      const t = kids().trim();
      return t ? `**${t}**` : "";
    }
    case "I":
    case "EM": {
      const t = kids().trim();
      // a lone decorative glyph carries nothing in a flat file
      if (!t || (t.length <= 2 && !/[a-z0-9]/i.test(t))) return "";
      return `*${t}*`;
    }
    case "BR":
      return " ";
    case "A": {
      const href = node.getAttribute("href") || "";
      const text = kids().trim();
      if (!text) return "";
      return href && !href.startsWith("#") ? `[${text}](${href})` : text;
    }
    case "SVG":
      return "";
    default:
      return kids();
  }
}

const inlineTrim = (node) => collapse(node.childNodes.map(inline).join("")).trim();

function cellsOf(tr) {
  return tr.childNodes.filter(
    (n) => n.nodeType === 1 && ["TH", "TD"].includes(n.rawTagName.toUpperCase()),
  );
}

// A GitHub-flavoured markdown table, so the twin of a matrix is machine-readable.
function tableToMarkdown(table) {
  const headTr = table.querySelector("thead tr") ?? table.querySelector("tr");
  const headers = headTr ? cellsOf(headTr).map((c) => inlineTrim(c) || " ") : [];
  const ncol = headers.length;
  if (ncol === 0) return "";
  const lines = [`| ${headers.join(" | ")} |`, `| ${headers.map(() => "---").join(" | ")} |`];
  const bodyRows = table.querySelectorAll("tbody tr");
  const rows = bodyRows.length ? bodyRows : table.querySelectorAll("tr").slice(1);
  for (const tr of rows) {
    const row = cellsOf(tr).map((c) => inlineTrim(c) || " ");
    while (row.length < ncol) row.push("");
    lines.push(`| ${row.join(" | ")} |`);
  }
  return lines.join("\n");
}

/**
 * The context ledger as a table.
 *
 * It is a grid of divs and not a `<table>`, because the three columns collapse to one on a
 * phone and a table cannot be re-flowed that way. Recursed as blocks it would shatter into one
 * paragraph per cell with nothing saying which column each came from — which is the whole
 * content of the section — so it is converted here instead.
 */
function ledgerToMarkdown(ledger) {
  const rows = ledger.querySelectorAll(".lrow");
  if (!rows.length) return "";
  const cells = (row) =>
    row.childNodes
      .filter((n) => n.nodeType === 1)
      .map((c) => inlineTrim(c) || " ");
  const head = cells(rows[0]);
  const lines = [`| ${head.join(" | ")} |`, `| ${head.map(() => "---").join(" | ")} |`];
  for (const row of rows.slice(1)) lines.push(`| ${cells(row).join(" | ")} |`);
  return lines.join("\n");
}

/** One measurement: the file, the figure and the rule that file declared about itself. */
function readingToMarkdown(reading) {
  const part = (selector) => {
    const found = reading.querySelector(selector);
    return found ? inlineTrim(found) : "";
  };
  const figure = collapse(part(".num"));
  return `- **${part(".file")}** — ${figure}, ${part(".unit")}. ${part(".rule")}`;
}

function blocks(node, out) {
  for (const child of node.childNodes) {
    if (child.nodeType === 3) {
      const t = collapse(decode(child.rawText)).trim();
      if (t) out.push(t);
      continue;
    }
    if (child.nodeType !== 1 || skipped(child)) continue;
    const tag = child.rawTagName.toUpperCase();
    const cls = classList(child);

    if (cls.includes("ledger")) {
      const md = ledgerToMarkdown(child);
      if (md) out.push(md);
    } else if (cls.includes("reading")) {
      out.push(readingToMarkdown(child));
    } else if (cls.includes("law")) {
      const id = child.querySelector(".id");
      const body = child.querySelector("p");
      out.push(`- **${id ? inlineTrim(id) : ""}** ${body ? inlineTrim(body) : ""}`.trim());
    } else if (cls.includes("nogoal")) {
      const body = child.querySelector("p");
      if (body) out.push(`- ${inlineTrim(body)}`);
    } else if (cls.includes("side-head")) {
      // The tag and the label are two runs sitting side by side, and glued together by an
      // inline collapse they read as one sentence that says neither.
      const tag = child.querySelector(".tag");
      const label = collapse(
        child.childNodes.filter((n) => n !== tag).map(inline).join(""),
      ).trim();
      out.push(`### ${tag ? `${inlineTrim(tag)} — ` : ""}${label}`);
    } else if (cls.includes("kicker")) {
      // A card's kicker names the axis the card is about. Italic rather than a line of its own
      // in plain text, because bare text above a heading reads as a paragraph that lost one.
      const t = inlineTrim(child);
      if (t) out.push(`_${t}_`);
    } else if (cls.includes("copyline")) {
      const command = child.querySelector("[data-copy]");
      if (command) out.push(fenced(collapse(plainText(command)).trim()));
    } else if (cls.includes("term")) {
      const pre = child.querySelector("pre");
      if (pre) out.push(fencedFrom(pre));
    } else if (tag === "PRE") {
      out.push(fencedFrom(child));
    } else if (tag === "TABLE") {
      const md = tableToMarkdown(child);
      if (md) out.push(md);
    } else if (tag === "BLOCKQUOTE") {
      const t = inlineTrim(child);
      if (t) out.push(`> ${t}`);
    } else if (HEADING[tag]) {
      const t = inlineTrim(child);
      if (t) out.push(`${HEADING[tag]} ${t}`);
    } else if (tag === "P") {
      const t = inlineTrim(child);
      if (t) out.push(t);
    } else if (tag === "UL" || tag === "OL") {
      const items = child
        .querySelectorAll(":scope > li")
        .map((li) => inlineTrim(li))
        .filter(Boolean)
        .map((t) => `- ${t}`);
      if (items.length) out.push(items.join("\n"));
    } else if (tag === "SVG") {
      const label = child.getAttribute("aria-label");
      if (label) out.push(`> _Figure: ${collapse(label).trim()}_`);
    } else if (INLINE_TAGS.has(tag)) {
      // A link that wraps blocks is a card, not a run: collapsing it inline would glue a
      // heading to the paragraph under it.
      const wrapsBlocks = child.childNodes.some(
        (n) => n.nodeType === 1 && !INLINE_TAGS.has(n.rawTagName.toUpperCase()),
      );
      if (tag === "A" && wrapsBlocks) {
        blocks(child, out);
        continue;
      }
      // an inline element sitting at block level (a chip, a kicker) is one line, not a tree to
      // recurse and shatter into a paragraph per text node
      const t = inlineTrim(child);
      if (t) out.push(t);
    } else {
      blocks(child, out);
    }
  }
}

export function htmlToMarkdown(html, { title } = {}) {
  const root = parse(html, { comment: false });
  const out = [];
  blocks(root, out);
  const cleaned = out.filter((b) => b.trim().length > 0);
  const body = cleaned.join("\n\n");
  return (title ? `# ${title}\n\n` : "") + body + "\n";
}
