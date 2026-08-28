// A page per finding code, generated from the table `explain` reads (RK1403).
//
// The gate names a code and `explain` says what the class is, what produces it and which doors
// close it — but only from an installed copy, so the reader who needs it most has the least: a
// person looking at a failed CI job, or at a hook that has just denied a write, in a
// repository they have not adopted. Pasted into a search engine those strings resolve to
// nothing, which is what a page per code fixes.
//
// Generated for the reason the verb pages are: a code added to the gate is documented in the
// commit that adds it, and one deleted stops being documented rather than becoming a page
// about a check nobody runs.
//
// The one half no read can derive is the **situation** — the ordinary act that put the reader
// there. That is written by hand, once per code, in src/data/situations.json, and stitched in
// here. Regenerating never edits a situation, and editing a situation never touches a page's
// derived half.
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const PAGES = join(HERE, "..", "src", "content", "docs", "findings");
const SITUATIONS = join(HERE, "..", "src", "data", "situations.json");

function ask(interpreter) {
  return execFileSync(interpreter, ["-m", "roadkeep.cli", "explain", "--json"], {
    cwd: ROOT,
    env: { ...process.env, PYTHONPATH: join(ROOT, "src"), PYTHONIOENCODING: "utf-8" },
    encoding: "utf-8",
    maxBuffer: 32 * 1024 * 1024,
  });
}

let raw;
let failure;
for (const interpreter of ["python", "python3"]) {
  try {
    raw = ask(interpreter);
    break;
  } catch (error) {
    failure = error;
  }
}

if (raw === undefined) {
  console.error("[findings] could not run `roadkeep explain --json` from " + ROOT);
  throw failure;
}

const codes = JSON.parse(raw);
if (!codes.length) {
  throw new Error("[findings] the gate declares no codes, which is never correct");
}

// A leading underscore is the file's own prose about itself, not a code. One convention and
// not a second file: the argument for how a situation is written belongs beside the situations.
const situations = Object.fromEntries(
  Object.entries(JSON.parse(readFileSync(SITUATIONS, "utf-8"))).filter(
    ([key]) => !key.startsWith("_"),
  ),
);

// Every page is rewritten from the table on every build, so the directory is emptied first:
// a page left behind by a code that was deleted is a page about a check nobody runs, and it
// would keep rendering.
if (existsSync(PAGES)) rmSync(PAGES, { recursive: true });

/** What a reader types to run one door, spelled the way this repository spells it. */
function commandOf(door) {
  const argv = door.argv.map((one) => (/\s/.test(one) ? JSON.stringify(one) : one));
  // A foreign door is somebody else's command — `git checkout` — and prefixing it with this
  // engine would name a subcommand roadkeep does not have.
  return door.argv[0] === "git" ? argv.join(" ") : `roadkeep ${argv.join(" ")}`;
}

/** How the finding closes, as a sentence rather than as the payload's one word. */
const KINDS = {
  compose: "You write the shorter or corrected text. Nothing can derive it for you.",
  decide: "Two or more doors are open and which one is right is a judgement about the work.",
  fix: "The mechanical pass reaches it: `roadkeep lint --fix` closes this one.",
  read: "A report rather than a repair — read the answer and decide whether anything is wrong.",
  run: "One command closes it, and it is derived rather than composed.",
  restore: "The content is gone and no verb of this tool brings it back; the store is the repository, so the command is git's.",
};

/** One harvested clause as a sentence. The causes are written as lead-ins to the doors under
 *  them — several end in a colon — so a stop appended blindly produces "a deletion:." */
function sentence(text) {
  const trimmed = text.trim().replace(/[:;,]$/, "");
  const opened = trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
  return /[.!?]$/.test(opened) ? opened : `${opened}.`;
}

function escape(text) {
  // The frontmatter is YAML and these strings are prose from the tool: a colon or a quote in
  // one would end the value early, so the whole of it is quoted and its quotes doubled.
  return `"${String(text).replace(/"/g, '\\"')}"`;
}

mkdirSync(PAGES, { recursive: true });

let described = 0;
for (const finding of codes) {
  const family = finding.code.split(".")[0];
  const directory = join(PAGES, family);
  mkdirSync(directory, { recursive: true });

  const situation = situations[finding.code];
  if (situation) described += 1;

  // Declared rather than derived from the filename: Astro slugifies a dot away, so
  // `block.emptied` became `/findings/block/blockemptied/` — a URL that does not carry the
  // string somebody pasted into a search engine, which is the whole reason these pages exist.
  // A hyphen keeps the two halves apart and reads back as the code.
  const slug = `findings/${family}/${finding.code.replace(/\./g, "-")}`;

  const lines = [
    "---",
    `title: ${finding.code}`,
    `slug: ${slug}`,
    `description: ${escape(finding.cause)}`,
    "---",
    "",
    situation ? `${situation}\n` : "",
    "## What it means",
    "",
    sentence(finding.cause),
    "",
    KINDS[finding.kind] ?? `Reported as \`${finding.kind}\`.`,
    "",
  ];

  if (finding.varies) {
    lines.push(
      `It is not the same finding on every project: ${finding.varies}`,
      "",
    );
  }

  if (finding.doors.length) {
    lines.push("## What closes it", "");
    for (const door of finding.doors) {
      lines.push(
        `- \`${commandOf(door)}\` — ${door.what}` + (door.writes ? "" : " *(reads only)*"),
      );
    }
    lines.push("");
  }

  // `decision` is what to weigh when several doors are open, and on this build it is the same
  // string as `cause` for every code that carries one. Rendered only where the two differ, so
  // the page never says one thing twice under two headings — which reads as though the second
  // were an answer to something the first did not cover.
  if (finding.decision && finding.decision.trim() !== finding.cause.trim()) {
    lines.push("## Choosing between them", "", sentence(finding.decision), "");
  }

  writeFileSync(join(directory, `${finding.code}.mdx`), lines.join("\n"), "utf-8");
}

// The situations are hand-written and the codes are not, so the two can drift apart in both
// directions. An orphan is caught by the suite; the shortfall is *reported* here, because a
// coverage number nobody prints is one nobody closes.
const orphans = Object.keys(situations).filter(
  (code) => !codes.some((finding) => finding.code === code),
);
if (orphans.length) {
  throw new Error(
    `[findings] situations.json describes codes this build does not have: ${orphans.join(", ")}`,
  );
}

console.log(
  `[findings] ${codes.length} page(s); ${described} carry a hand-written situation, ` +
    `${codes.length - described} do not`,
);
