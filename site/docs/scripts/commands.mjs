// The command surface, taken from the tool rather than typed into a page (RK1402).
//
// `roadkeep commands --json` emits the parser as data — every verb, its arguments, their
// defaults and the sentence the parser already carries — so this asks the checkout it is
// building from and writes the answer where a component can render it. A reference page built
// this way cannot describe a flag that was removed, and it gains one in the commit that adds
// it.
//
// It runs as `prebuild`, so `npm run build` and `npm run dev` both start from a current
// answer and nobody has to remember a step.
//
// The generated file is git-ignored. A committed copy is the failure this exists to remove:
// the build would quietly fall back to it and publish a reference nobody can see is stale.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const OUT = join(HERE, "..", "src", "data", "commands.generated.json");

// The package is not installed in this checkout — `agents.md` says to read every command as
// `PYTHONPATH=src python -m roadkeep.cli`, and this is that, from the repository root so the
// verb finds `roadkeep.toml`. Both spellings of the interpreter are tried because Windows
// ships `python` and most CI images ship `python3`.
function ask(interpreter) {
  return execFileSync(interpreter, ["-m", "roadkeep.cli", "commands", "--json"], {
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
  // Loud, and never a fallback to whatever was there before. A build that cannot ask the tool
  // has nothing true to say about its flags, and a page rendered from a stale file is worse
  // than no page: it reads exactly like a current one.
  console.error(
    "[commands] could not run `python -m roadkeep.cli commands --json` from " + ROOT,
  );
  throw failure;
}

const payload = JSON.parse(raw);
if (!payload.commands?.length) {
  throw new Error("[commands] the tool answered with no commands, which is never correct");
}

mkdirSync(dirname(OUT), { recursive: true });
// Pretty-printed and newline-terminated so a diff of the generated file is readable when
// somebody is working out why a table changed.
writeFileSync(OUT, JSON.stringify(payload, null, 2) + "\n", "utf-8");
console.log(
  `[commands] ${payload.commands.length} command(s) from roadkeep ${payload.version}`,
);
