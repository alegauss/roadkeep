# roadkeep — Development Guide

**What this is.** A CLI that owns writes to a project's `ROADMAP.md`,
`CHANGELOG.md`, `IMPROVEMENTS.md` and `STRATEGY.md`, so the format is a schema at the
point of insertion instead of a convention an author is asked to remember. Shipped as
a Claude Code plugin, because the author to constrain is usually an agent.

**The problem it solves, measured.** In Viglet Shio: 92 roadmap lines averaging **142 words**
against a one-sentence rule, worst **1406 characters**; an `agents.md` that reached **186 KB**
absorbing the rationale of every shipped task. Six of the eight worst lines were written in the
session that then diagnosed it — the drift is invited by the process. Full measurement:
[docs/IMPROVEMENTS.md §0.1](docs/IMPROVEMENTS.md).

**The insight that decides every design question.** *The saving is the analysis, not the
characters.* A linter reports after the prose exists, when the tokens are spent and the
author is asked to delete work; a `maxLength` refuses before a sentence is composed to
fill it, turning an analytical act ("what would I cut?") into a procedural one ("call `add`").

## The six laws

Compressed; **[IMPROVEMENTS.md §0.3](docs/IMPROVEMENTS.md) is authoritative.** A change
that breaks one is wrong even if requested.

| # | Law |
|---|---|
| L1 | Schema enforced **where the text is created**; `lint` is only the backstop. |
| L2 | The **store is the repository** — Markdown, greppable, no database, no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical, or refuse the file. |
| L4 | The tool **never writes prose** — it validates and renders. |
| L5 | **Query instead of read** — every question is a command, so answering costs no context. |
| L6 | **Configuration, not convention** — prefix, paths, markers, limits are per-project. |

## Layout

```
docs/ROADMAP.md        active backlog, one line per task (RK<n>)
docs/CHANGELOG.md      shipped ledger, indexed by block
docs/IMPROVEMENTS.md   design rationale for UNSHIPPED sections only
agents.md, roadkeep.toml   this file, and this project's own configuration
src/roadkeep/   the package (src layout, importable via pytest pythonpath). Each module's
                own docstring is the authority on it — this is only where to look:
  schema document config ids                RK1-4  the format, the file, the config, the id
  authoring shipping markers sections       RK5-9/32/41  the write paths, all-or-nothing
  backlog counting picking showing graph    RK10-13/28-29/31/37/39-40  the query surface,
  briefing exporting history                         plus what git alone can answer
  linting fixing                            RK14-17  the gate, and the derived-only fixer
  adopting                                  RK18  `init` scaffolds, `adopt` estimates first
  guarding                                  RK22  the hook: deny the hand-edit, allow on error
  cli.py    one subparser per task, exit 0 / 1 gate / 2 usage, and RK38's event line
action.yml, .pre-commit-hooks.yaml, .github/   the gate's three surfaces (RK17)
hooks/, .claude-plugin/   the plugin's two (RK22), reasoned in tests/test_plugin.py
tests/          pytest; docs/ROADMAP.md is a fixture, not a mock
```

`Schema.render` is the only writer of the line format, `Schema.validate` the only reader of
the rules, and `Document` the only reader of a file — it keeps every source line verbatim
and **every mutator refuses the whole file** when a line it parsed would render back
differently. Never construct a task line with an f-string; before writing a command:

- Get documents from `Config.document(role)`, never by picking a schema at the call site:
  the changelog is `schema.as_ledger()` (✅, no deps, no pointer), not a second grammar.
- A rejected marker line becomes a `Reject` **with a reason** (`audit` prints them); a dep
  the parser cannot type still parses, so the line stays counted. That split is deliberate.

## This repo's own docs are the conformance fixture

`roadkeep lint` **must pass on `docs/`** — the format is proven by the artefact, not asserted
in a README. A limit that cannot express these lines is the wrong limit rather than a set of
wrong lines, so a schema change validates here first, under this repo's own `roadkeep.toml`.

Don't hand-check it: `… lint` **exits 1** on any violation, line that stopped round-tripping,
dep nothing satisfies, pointer resolving to nothing, section nothing points at, over-budget
every-turn file, or invisible codepoint — which it names as `file:line:column` instead of the
consequence, and then judges nothing else on that line (RK14/RK15/RK30/RK34). CI runs the same
command through the action this repo ships (RK17). `--fix` repairs only what is **derived**
(annotation, pointer, dep order, marker codepoint, whitespace) and leaves the editorial (RK16).

## Writing and shipping — call the command, never type the format

`python -m roadkeep.cli <add|status|ship|retire|record|section> --help` has the flags. What they
guarantee, so it costs you no thought: the id, the `→ §RK<n>` pointer, the status default and
every `(deps: … ✅)` annotation are **derived, never typed**; a refusal exits 2 naming the length
and the limit and writes nothing; ✅ never reaches the roadmap; `ship` makes its three edits
(ledger entry, roadmap line gone, `§<id>` deleted) plus the dependents' annotations, or none, and
`retire <id> [--superseded-by <id>] --reason "…"` is the same transaction, two more doors (RK32).
`record --block <x> --symptom "…" --why "…"` is the fourth — never planned, so the ledger entry
alone and the roadmap untouched (RK41). `section add <id> --title "…"` takes prose on **stdin**,
≤250 words, filled to 88 columns, under the task's block — a table or list is inserted exactly as
written. No write invents a block heading. Every write prints one `event <id> Block <x>
open|empty` line, the whole payload a hook gets (RK38). With the plugin there is no second
route: `Edit` on a governed file is denied, naming these, and `lint` gates the turn's end (RK22).

That leaves the two rules a schema cannot check:

1. **`symptom` states what does not work** — never a solution name: a line named after its fix
   cannot be falsified, so it never gets closed, only abandoned.
2. **`why` is one sentence.** A second sentence is the signal the content belongs in
   `IMPROVEMENTS.md`, which is what the pointer addresses.

Markers: 📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress; the ledger's are ✅ and 🗑,
neither legal in a roadmap. Limits: `symptom` ≤120, `why` ≤200, line ≤320, section ≤250 (L6).

**Ask, don't count** (all take `--json`): **`… brief [<id>]` starts a task in one call** — the
line, its rationale, deps resolved, the blocker chain, what it unblocks and the non-goals,
bounded to a tool result; with no id, `pick`'s own choice (RK29). Narrower: `… next-id` never
fills a gap; `… list|stats|audit [--block C]` counts and lists, naming every marker line
neither could read (RK10); `… show <id>` joins one line, its section and its paths (RK12);
`… deps <id>` walks the graph both ways (RK13/RK28/RK37); `… gaps` resolves an id in neither
file against the commit that removed it (RK32); `… origin <id> --why` (RK31). And **never
restate a count in prose**: `… export [--readme|--site|--json]` projects it (RK39/RK42).

## Picking work

`… brief [--block C]` picks and briefs in one call, printing why (RK11/RK29/RK40): 🛠 first, then
`priority` in `roadkeep.toml`, then the lowest ready id, never one blocked outside. **Scope it to
finish a block**: only "nothing is open in Block C" means finished — unscoped, the answer may be
another block's, and the block order is the headings' own (`… list`).

## Build and test

- **Python ≥3.11** (`tomllib` is stdlib there; 3.13.14 is installed here) and **zero runtime
  dependencies**: `argparse` + `tomllib`, never `click` + `pydantic` — a tool meant to run as
  `uvx roadkeep` in someone else's CI pays for every dependency it takes.
- `uv` is **not** installed here — `python -m pytest` from the repo root (`pythonpath =
  ["src"]` is set, so no install step). Only dev dependency: `pip install --user pytest`.
- Round-trip (L3) is a **property test over real files**: `docs/` plus Shio's and Turing's
  roadmaps, which supply the dep kinds worth keeping and skip where they are absent (CI).

## Committing

**One task → one commit, the instant it is validated.** What `ship` wrote goes in the *same*
commit as the code, so the docs never describe a state that did not ship, and a batch of ≥2
tasks is **not** permission to batch: `/loop`, one task per iteration. Use `run-commit.cmd -m
"<conventional-commits title>"` from the repo root, **`-m` always** and ASCII — without it a
docs commit's prose about shipped work is misread as `feat: implement <feature>`. It stages
everything, so a tree holding unrelated work wants the task's paths staged and
`python -m commitclerk -m …` instead.

## Non-goals are binding

[docs/ROADMAP.md](docs/ROADMAP.md) → "Non-goals", which `brief` prints with every task. The one a
suggestion keeps violating: **no model, no prompts** (L4) — a generator reintroduces this drift.

## This file is scaffolding

Enforcement has caught up — Block D gates the format, RK22 denies the hand-edit — but these
*rules* still load every turn. **RK23 replaces it with a skill**, trigger-loaded and identical
everywhere; the two sections above go with it, a rule in two files being one two files can
disagree about. L5 governs it first: its budget is `[budgets]` in `roadkeep.toml`, held by `lint`
and not by this sentence (RK30) — the arrangement that let Shio's reach the 186 KB above.
