# roadkeep — Development Guide

**What this is.** A CLI that owns writes to a project's `ROADMAP.md`,
`CHANGELOG.md`, `IMPROVEMENTS.md` and `STRATEGY.md`, so the format is a schema at the
point of insertion instead of a convention an author is asked to remember. Shipped as
a Claude Code plugin, because the author to constrain is usually an agent.

**The problem it solves, measured.** In the Viglet Shio repository: 92 roadmap lines
averaging **142 words** against a one-sentence rule, worst **1406 characters**; an
`agents.md` that reached **186 KB** by absorbing the rationale of every shipped task.
Six of the eight worst lines were written in the session that then diagnosed the
problem — the drift is invited by the process, not caused by inattention. Full
measurement: [docs/IMPROVEMENTS.md §0.1](docs/IMPROVEMENTS.md).

**The insight that decides every design question.** *The saving is the analysis, not
the characters.* A linter reports after the prose exists, when the tokens are already
spent and the author is being asked to delete work. A `maxLength` refuses before a
sentence is composed to fill it — and turns an analytical act ("is this too long, what
would I cut?") into a procedural one ("call `add`").

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
agents.md              this file
roadkeep.toml          this project's own configuration — the tool reads it
src/roadkeep/          the package (src layout, importable via pytest pythonpath)
  schema.py            RK1 — Task, Dep, Schema, Violation; validate() and render()
  document.py          RK2 — Document.parse/render, Entry, Reject, RoundTripError
  config.py            RK3 — Config.discover/document; refuses an unknown key
tests/                 pytest; docs/ROADMAP.md is a fixture, not a mock
```

`Schema.render` is the only writer of the line format and `Schema.validate` the only
reader of the rules — a new command imports them rather than re-deriving either.
`Document` is the only reader of a file: it keeps every source line verbatim, and
**every mutator refuses the whole file** when any line it parsed would render back
differently. Three consequences worth knowing before writing a command:

- A file is read under a `Schema`; the changelog is `schema.as_ledger()` (✅, no deps,
  no pointer), not a second grammar. Get both from `Config.document(role)` rather than
  choosing a schema at the call site.
- A marker-bearing line the grammar rejects becomes a `Reject` **with a reason**, never
  a silent skip. A dep the schema dislikes (`Block P`) still parses, so the line stays
  counted and `lint` reports it — that split is deliberate.
- Never construct a task line with an f-string. `Schema.render` or nothing.

## This repo's own docs are the conformance fixture

`roadkeep lint` **must pass on `docs/`** — the format is proven by the artefact, not
asserted in a README. So when you change the schema, this repository is the first thing
that has to still validate, and a limit that cannot express these 26 lines is a wrong
limit rather than 26 wrong lines.

Current reading (RK14/RK15 exist to replace this by hand-verification): 28 tasks,
longest line **307** chars against a 320 cap, 28/28 `→ §x.y` pointers resolve, no
orphan improvements section. Since RK1 the suite asserts the first two against
`docs/ROADMAP.md` itself, so a schema change that cannot express this backlog fails the
tests rather than a review — and since RK3 it asserts them under this repository's own
`roadkeep.toml`, so "configuration, not convention" is not a claim about other people's
projects.

## Writing a task line — until `roadkeep add` exists

```
- <marker> **RK<n>** (deps: <RK<n>, … | —>) **<symptom>** — <one sentence> → §<x.y>
```

Markers: 📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress. ✅ appears only in
`CHANGELOG.md` and in a `(deps: RK1 ✅)` annotation.

Four rules, and they are the schema RK1 encodes:

1. **`symptom` states what does not work** — never a solution name. A line named after
   its fix cannot be falsified, so it never gets closed, only abandoned.
2. **`why` is one sentence.** A second sentence is the signal the content belongs in
   `IMPROVEMENTS.md`, which is what the pointer addresses.
3. **≤320 characters rendered** (`symptom` ≤120, `why` ≤200).
4. **Every `→ §x.y` must resolve** to a `### §x.y` heading in `IMPROVEMENTS.md`.

**Next id:** max across `docs/*.md` and this file. Ids are non-contiguous by design and
retired ids are never reused, so never infer one from a block's header range.

## Picking work

Lowest-numbered task whose `deps` are all shipped. Blocks are ordered by dependency,
not priority: **A** (model) → **B** (authoring) → **C** (query) → **D** (gate) →
**E** (adoption) → **F** (plugin). The guardrail does not exist until D, and is not
*inescapable* until F.

## Build and test

- **Python ≥3.11** (`tomllib` is stdlib from 3.11; 3.13.14 is installed here).
- **Zero runtime dependencies.** `argparse` + `tomllib`, not `click` + `pydantic`. A
  tool meant to run as `uvx roadkeep` in someone else's CI pays for every dependency,
  and the schema is 200 lines of validation, not a framework.
- `uv` is **not** installed on this machine — use `python -m pytest` from the repo root
  (`pythonpath = ["src"]` is in `pyproject.toml`, so no install step). `pytest` is the
  only dev dependency: `python -m pip install --user pytest`.
- Round-trip (L3) is a **property test over real files**, not an example test: the
  corpus is `docs/` here plus Shio's and Turing's roadmaps.

## Committing

**One task → one commit, and commit the instant a task is validated** — before
starting the next. The doc sync (`ROADMAP` → `CHANGELOG`, drop the `IMPROVEMENTS`
section) goes in the *same* commit as the code, so the docs never describe a state that
did not ship.

Use `run-commit.cmd -m "<conventional-commits title>"` from the repo root (it is on the
system PATH). **Always pass `-m`**, keep it ASCII: without it, a docs commit's prose
about already-shipped work gets misread as `feat: implement <feature>`.

A batch of ≥2 tasks is **not** permission to batch — run it under `/loop`, one task per
iteration, commit at the end of each.

## Non-goals are binding

[docs/ROADMAP.md](docs/ROADMAP.md) → "Non-goals". The one most likely to be violated by
a well-meaning suggestion: **no model and no prompts inside the tool.** It validates
and renders; it never writes the `symptom` or the rationale. A generator would
reintroduce precisely the drift this exists to stop.

## This file is scaffolding

It exists because the format cannot enforce itself until Block D, and cannot resist a
hand-edit until Block F. **RK23 replaces it with a skill** — trigger-loaded, shipped by
the plugin, identical across every project. When RK23 lands, everything above under
"Writing a task line" and "Picking work" is deleted from here, because a rule that
lives in two files is a rule two files can disagree about.

Budget: this file stays under **150 lines**. It is loaded every turn, so it is governed
by L5 before it governs anything else.
