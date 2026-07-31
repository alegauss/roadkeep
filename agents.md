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
  authoring shipping markers sections       RK5-9/32/41/67  the write paths, all-or-nothing
  scoping                                   RK70  the non-goal, the bullet that is no task
  backlog counting picking showing graph    RK10-13/28-29/31/37/39-40  the query surface,
  briefing exporting history                         plus what git alone can answer
  linting fixing                            RK14-17  the gate, and the derived-only fixer
  adopting                                  RK18  `init` scaffolds, `adopt` estimates first
  guarding serving                          RK22/24  the hook, and the tools over stdio
  cli.py    one subparser per task, exit 0 / 1 gate / 2 usage, and RK38's event line
action.yml, .pre-commit-hooks.yaml, .github/   the gate's three surfaces (RK17)
hooks/, skills/, commands/, .mcp.json, .claude-plugin/   the plugin's five, and how it is
                installed (RK22-26); reasoned in tests/test_{plugin,skill,serving,commands}.py
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

## The write path is a skill, not a preamble

[skills/roadkeep/SKILL.md](skills/roadkeep/SKILL.md) is the authority on which command to call,
what it derives, the two rules a schema cannot check, the query surface and how work is picked
— loaded when a governed file is in play and costing nothing on the turns that touch none
(RK23). It ships in the plugin, so it is the same text in every adopting project; **nothing
here repeats it**, a rule in two files being one two files can disagree about. This project's
numbers are `roadkeep.toml`, and the package is not installed here, so every command in it
reads `PYTHONPATH=src python -m roadkeep.cli <…>` from the repo root.

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

Enforcement has caught up — Block D gates the format, RK22 denies the hand-edit, RK23 moved the
write path into the skill — so what still loads every turn is only what a turn touching no
governed file needs: the laws, where the code is, and how to build and commit it. L5 governs
what is left: its budget is `[budgets]` in `roadkeep.toml`, held by `lint` and not by this
sentence (RK30) — the arrangement that let Shio's reach the 186 KB above.
