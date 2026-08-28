// Prose this repository already owns, rendered rather than restated (RK1408).
//
// This project's whole thesis is against what a documentation area usually becomes. The six
// laws are written in `agents.md`, in the README and in `llms.txt`; a fourth copy here would
// be exactly the accretion the tool exists to refuse — and the copy nobody is looking at is
// the one that drifts.
//
// So a page that needs them **renders** them from where they live. Two sources, each with an
// owner:
//
//   * the laws, harvested out of `agents.md`, which is the file the gate holds a budget over
//     and therefore the one somebody actually maintains;
//   * the non-goals, asked of `roadkeep non-goal list`, which is the verb that owns them —
//     they are bullets in the roadmap, and a page holding its own version is stale from the
//     next write.
//
// Where a page needs framing no file carries, the framing goes in the page and the substance
// stays where it was. That is the line this script draws.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const OUT = join(HERE, "..", "src", "data", "owned.generated.json");

function ask(argv) {
  let failure;
  for (const interpreter of ["python", "python3"]) {
    try {
      return execFileSync(interpreter, ["-m", "roadkeep.cli", ...argv, "--json"], {
        cwd: ROOT,
        env: { ...process.env, PYTHONPATH: join(ROOT, "src"), PYTHONIOENCODING: "utf-8" },
        encoding: "utf-8",
        maxBuffer: 32 * 1024 * 1024,
      });
    } catch (error) {
      failure = error;
    }
  }
  console.error(`[owned] could not run \`roadkeep ${argv.join(" ")} --json\` from ${ROOT}`);
  throw failure;
}

// The laws, out of the table `agents.md` carries. Anchored on the `| L<n> |` shape rather than
// on a line number, so editing the prose above it moves nothing here — and a table that stops
// matching is an empty harvest, which fails below rather than publishing four laws as six.
const LAW = /^\|\s*(L\d)\s*\|\s*(.+?)\s*\|$/gm;
const agents = readFileSync(join(ROOT, "agents.md"), "utf-8");
const laws = [...agents.matchAll(LAW)].map(([, id, text]) => ({ id, text }));

if (laws.length !== 6) {
  throw new Error(
    `[owned] harvested ${laws.length} law(s) from agents.md, and this project has six — ` +
      "the table moved, and a page rendering the remainder would look complete",
  );
}

const scope = JSON.parse(ask(["non-goal", "list"]));
if (!scope.non_goals?.length) {
  throw new Error("[owned] the roadmap declares no non-goals, so a page would render nothing");
}
if (scope.non_goals_elided) {
  // The verb elides where a listing is bounded. A page showing some of them without saying so
  // reads as the whole list, which is the one way this could quietly mislead.
  throw new Error(`[owned] ${scope.non_goals_elided} non-goal(s) were elided by the read`);
}

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(
  OUT,
  JSON.stringify({ laws, non_goals: scope.non_goals, from: scope.file }, null, 2) + "\n",
  "utf-8",
);

console.log(`[owned] ${laws.length} law(s) from agents.md, ${scope.non_goals.length} non-goal(s) from ${scope.file}`);
