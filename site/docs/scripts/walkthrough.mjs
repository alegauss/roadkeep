// The adoption walkthrough, as a run rather than a description (RK1406).
//
// Adoption is the path with the most friction and the least prose. What decides one is not the
// command list — the README already gives that — it is what the first commands *print* on files
// that were already there, and especially what they refuse.
//
// Output pasted into prose is fiction with a shelf life, so none of this is pasted.
// `scripts/walkthrough.py` builds a throwaway repository with a genuinely drifted roadmap in
// it, runs the adoption in order and emits every command with the output it actually produced.
// A refusal whose wording changed fails this build instead of misleading a reader, and
// `tests/test_walkthrough.py` executes the same script.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const OUT = join(HERE, "..", "src", "data", "walkthrough.generated.json");

function ask(interpreter) {
  return execFileSync(interpreter, [join(ROOT, "scripts", "walkthrough.py")], {
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
  console.error("[walkthrough] could not run scripts/walkthrough.py from " + ROOT);
  throw failure;
}

const steps = JSON.parse(raw);
if (!steps.length) {
  throw new Error("[walkthrough] the run produced no steps, which is never correct");
}

// The refusals are the half that matters — being refused on a file that has always been there
// is where an adoption stops — so a run where nothing was refused is one that stopped
// demonstrating the thing it exists for.
const refused = steps.filter((step) => step.exit_code === 2).length;
if (refused === 0) {
  throw new Error("[walkthrough] nothing was refused, so the page shows a path nobody is on");
}

// This machine must not reach the page. `walkthrough.py` redacts its temporary directory, and
// this is the assertion that it did: a leaked path publishes somebody's username and makes
// every build differ from the last for a reason that is not about the tool.
const leaked = steps.filter((step) =>
  /[A-Za-z]:\|\/(home|Users)\//.test(step.stdout + step.stderr + JSON.stringify(step.wrote)),
);
if (leaked.length) {
  throw new Error(
    `[walkthrough] an absolute path reached the output: ${leaked[0].command || "(an edit)"}`,
  );
}

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(steps, null, 2) + "\n", "utf-8");

console.log(`[walkthrough] ${steps.length} step(s), ${refused} of them refusals`);
