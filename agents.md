# roadkeep — Development Guide

**What this is.** A CLI that owns writes to a project's `ROADMAP.md`,
`CHANGELOG.md`, `IMPROVEMENTS.md` and `STRATEGY.md`, so the format is a schema at the
point of insertion instead of a convention an author is asked to remember. Shipped as
a Claude Code plugin, because the author to constrain is usually an agent.

**The problem it solves, measured.** In Viglet Shio: 92 roadmap lines averaging **142
words** against a one-sentence rule, worst **1406 characters**; an `agents.md` that
reached **186 KB** absorbing the rationale of every shipped task. Six of the eight worst
lines were written in the session that then diagnosed the problem — the drift is invited
by the process. Full measurement: [docs/IMPROVEMENTS.md §0.1](docs/IMPROVEMENTS.md).

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
agents.md              this file
roadkeep.toml          this project's own configuration — the tool reads it
src/roadkeep/          the package (src layout, importable via pytest pythonpath)
  schema.py            RK1 — Task, Dep, Schema, Violation; validate() and render()
  document.py          RK2 — Document.parse/render, Entry, Reject, RoundTripError
  config.py            RK3 — Config.discover/document; refuses an unknown key
  ids.py               RK4 — scan/highest/next_id across every configured source
  authoring.py         RK5/RK7 — add(), set_status(); nothing written unless all of it
  shipping.py          RK6 — ship(): three edits, validated together, written last
  backlog.py           RK28/RK37 — resolve/readiness; four dep kinds, four answers
  history.py           RK31 — origin_of(): the shipping commit, derived from git
  cli.py               the command surface; one subparser per task, exit 0/1/2
tests/                 pytest; docs/ROADMAP.md is a fixture, not a mock
```

`Schema.render` is the only writer of the line format, `Schema.validate` the only reader of
the rules, and `Document` the only reader of a file — it keeps every source line verbatim
and **every mutator refuses the whole file** when a line it parsed would render back
differently. Never construct a task line with an f-string; before writing a command:

- Get documents from `Config.document(role)`, never by choosing a schema at the call
  site: the changelog is `schema.as_ledger()` (✅, no deps, no pointer), not a second
  grammar.
- A marker-bearing line the grammar rejects becomes a `Reject` **with a reason**, never
  a silent skip; a dep the parser cannot type still parses, so the line stays counted
  and `lint` reports it. That split is deliberate.

## This repo's own docs are the conformance fixture

`roadkeep lint` **must pass on `docs/`** — the format is proven by the artefact, not
asserted in a README. A limit that cannot express these lines is the wrong limit rather
than a set of wrong lines, so this repository is the first thing a schema change must
still validate — under its own `roadkeep.toml`, which is what makes L6 a fact here.

Current reading (RK14/RK15 replace this hand-verification): 25 tasks, longest line
**305** chars against a 320 cap, 25/25 pointers resolve, no orphan section.

## Writing and shipping — call the command, never type the format

```
python -m roadkeep.cli add --block B --symptom "<what does not work>" \
  --why "<one sentence.>" [--dep "RK5 ✅"] [--status 💭] [--id RK9] [--json]
```

The id, the pointer and the marker are derived; the block must already have a heading. A
refusal exits 2 with the length and the limit and writes nothing, leaving you the two
rules a schema cannot check:

1. **`symptom` states what does not work** — never a solution name. A line named after
   its fix cannot be falsified, so it never gets closed, only abandoned.
2. **`why` is one sentence.** A second sentence is the signal the content belongs in
   `IMPROVEMENTS.md`, which is what the pointer addresses.

Enforced for you: ≤320 rendered (`symptom` ≤120, `why` ≤200); the marker from 📋 designed
· 💭 idea · ⏳ partial · 🛠 in-progress (✅ only in `CHANGELOG.md` and in a `(deps: RK1 ✅)`
annotation); `→ §RK<n>` derived from the id (RK27), unless `ref_scheme = "outline"`.

**Shipping is `… ship <id> [--why "<the outcome.>"]`** — ledger entry, roadmap line gone,
`§<id>` deleted, all three validated before one is written; the stale dep annotations it
*reports* are yours to edit until RK8.

**Ask, don't count** (all take `--json`): `python -m roadkeep.cli next-id` for the next id
— never fill a gap, a retired id is never reused; `… deps <id>` types each dep (a task, a
`Block X`, a range, or outside work — the last, and a block no heading declares, is
*unresolvable*, never "pending": RK28/RK37); `… origin <id> --why` for the reasoning (RK31).

## Picking work

Lowest-numbered task whose `deps` are all shipped. Blocks are ordered by dependency, not
priority: **A** (model) → **B** (authoring) → **C** (query) → **D** (gate) → **E**
(adoption) → **F** (plugin). No guardrail before D, and none an agent cannot route around
before F.

## Build and test

- **Python ≥3.11** (`tomllib` is stdlib from 3.11; 3.13.14 is installed here).
- **Zero runtime dependencies.** `argparse` + `tomllib`, not `click` + `pydantic`: a tool
  meant to run as `uvx roadkeep` in someone else's CI pays for every dependency.
- `uv` is **not** installed here — `python -m pytest` from the repo root (`pythonpath =
  ["src"]` is set, so no install step). Only dev dependency: `pip install --user pytest`.
- Round-trip (L3) is a **property test over real files**: `docs/` plus Shio's and
  Turing's roadmaps, which also supply the dep kinds and the odd cases worth keeping.

## Committing

**One task → one commit, and commit the instant a task is validated** — before starting
the next. What `ship` wrote goes in the *same* commit as the code, so the docs never
describe a state that did not ship, and a batch of ≥2 tasks is **not** permission to
batch: `/loop`, one task per iteration.

Use `run-commit.cmd -m "<conventional-commits title>"` from the repo root (it is on the
system PATH). **Always pass `-m`**, keep it ASCII: without it, a docs commit's prose
about already-shipped work gets misread as `feat: implement <feature>`. It stages
everything, so stage the task's own paths and call `python -m commitclerk -m …` when the
tree carries unrelated work.

## Non-goals are binding

[docs/ROADMAP.md](docs/ROADMAP.md) → "Non-goals". The one most likely to be violated by
a well-meaning suggestion: **no model and no prompts inside the tool.** It never writes
the `symptom` or the rationale — a generator would reintroduce exactly the drift this
exists to stop.

## This file is scaffolding

It exists because the format cannot enforce itself until Block D and cannot resist a
hand-edit until Block F. **RK23 replaces it with a skill** — trigger-loaded, shipped by
the plugin, identical everywhere. When it lands, "Writing a task line" and "Picking work"
are deleted from here: a rule living in two files is a rule two files can disagree about.

Budget: **under 150 lines** — loaded every turn, so L5 governs it first of all.
