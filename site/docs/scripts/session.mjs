// What a session is handed, and what it costs before a call is made (RK1405).
//
// Half of this tool's surface is not a command line: a session gets a hook that denies an edit
// to a governed file, a skill saying which command to call instead, slash commands, an MCP
// server with tens of tools, and a launcher for the sessions where no plugin can be installed.
// The README covers installing all five. Nothing described what the session then receives.
//
// That reader's questions have numbers in them — what connecting costs, which tool is the
// expensive one, how much room is left under `[tools] session` — and every one of them is a
// read this tool already makes about itself. `cost --tools` prices the served schema by walking
// the parser, and `cost --session` adds the files that load on every turn.
//
// Both are asked of **this** repository, which is the honest sample: the figures a reader sees
// are the ones this project's own gate holds itself to.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const OUT = join(HERE, "..", "src", "data", "session.generated.json");

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
  console.error(`[session] could not run \`roadkeep ${argv.join(" ")} --json\` from ${ROOT}`);
  throw failure;
}

const tools = JSON.parse(ask(["cost", "--tools"]));
const session = JSON.parse(ask(["cost", "--session"]));

if (!tools.by_tool?.length) {
  throw new Error("[session] the surface prices no tools, which is never correct");
}
if (!session.each_turn?.files?.length) {
  // A project with no `[budgets]` has nothing loading every turn, and the page would say a
  // session pays nothing per turn — true of that project and false of the one being described.
  throw new Error("[session] nothing is budgeted per turn, so the per-turn half would read as zero");
}

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify({ tools, session }, null, 2) + "\n", "utf-8");

console.log(
  `[session] ${tools.tools} tool(s) at ${tools.characters} ${tools.unit} once, ` +
    `${session.each_turn.characters} every turn`,
);
