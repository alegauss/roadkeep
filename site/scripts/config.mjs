// What `roadkeep.toml` may declare, taken from the read that owns it (RK1404).
//
// `config` answers every question about that file — each table, key, TOML type and default,
// the sentence its source already carries, whether this project declared it, and what this
// build *fixes* and no project may set. It answers from an installed copy on a configured
// tree, which is exactly what a reader writing their first one does not have.
//
// So the page is that read rendered, and nothing here restates it: the keys come off the
// frozensets the parser refuses by, the sentence off the `#:` comment already above each one,
// and the default off a default project — the same code the parser runs.
//
// Asked **of this repository**, which is deliberate. Its own `docs/` are the format's
// conformance fixture and `lint` passes on them, so this is the one configuration that is
// provably valid — which makes the `declared`/`set` half of every row a worked example rather
// than an aside, and one nobody transcribed.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..");
const OUT = join(HERE, "..", "src", "data", "config.generated.json");

function ask(interpreter) {
  return execFileSync(interpreter, ["-m", "roadkeep.cli", "config", "--json"], {
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
  console.error("[config] could not run `roadkeep config --json` from " + ROOT);
  throw failure;
}

const payload = JSON.parse(raw);
if (!payload.keys?.length) {
  throw new Error("[config] the tool answered with no keys, which is never correct");
}
if (!payload.source) {
  // The worked example is this repository's own file. Answered against a tree with no config,
  // every `declared` would be false and the page would quietly become a list of defaults.
  throw new Error("[config] answered against a tree with no roadkeep.toml, so nothing is shown as declared");
}

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(payload, null, 2) + "\n", "utf-8");

const tables = new Set(payload.keys.map((one) => one.table));
console.log(
  `[config] ${payload.keys.length} key(s) in ${tables.size} table(s) from roadkeep ` +
    `${payload.version}, read against ${payload.source}`,
);
