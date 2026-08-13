# roadkeep — Design rationale

> Rationale for **unshipped** sections only. Status markers live in
> [ROADMAP.md](ROADMAP.md); shipped work is described in
> [CHANGELOG.md](CHANGELOG.md) and `git log`. When a section ships, delete it here.

## §0 — Why this exists

### §0.1 The measured problem

Three files in the Viglet Shio repository declare a format and none enforces it:

| Artefact | Rule | Reading |
|---|---|---|
| `docs/ROADMAP.md` | one sentence per task | 92 active lines, **142 words** average, worst **1406 characters** (7× the best) |
| `agents.md` | index only, resident every turn | grew to **186 KB (~46k tokens)** before it was split |
| `docs/IMPROVEMENTS.md` | rationale for *unshipped* work | accreted shipped implementation reports; the sibling project's reached **539 KB** |

The pattern is identical in all three: an author with the whole design in working
memory writes it where the reader will be, and the reader is a file that gets loaded
every turn. Shio measured this in SH341 and found **six of the eight worst lines were
written in the session that then diagnosed the problem** — so this is a drift the
process invites, not a lapse of attention. An instruction to be terse does not survive
the moment its author knows more than the line allows.

### §0.2 Why the fix is a write path, not a linter

A linter reports after the prose exists, and by then the cost is already paid: the
tokens were spent generating it, and the author is being asked to delete work. A field
with `maxLength: 200` refuses at the point of insertion, before a sentence is composed
to fill it. Same rule, two orders of magnitude cheaper — and it converts an analytical
act ("is this line too long, and what would I cut?") into a procedural one ("call
`add`"). **The saving is the analysis, not the characters.**

### §0.3 The six laws

| # | Law |
|---|---|
| L1 | **The format is a schema, enforced where the text is created** — `add` refuses; `lint` is the backstop for what bypassed it. |
| L2 | **The store is the repository** — Markdown, greppable, diffable, no database and no service. |
| L3 | **Round-trip or don't write** — parse → render → byte-identical, or the tool may not own the file. |
| L4 | **The tool never writes prose** — it validates and renders. A generator would reintroduce the drift. |
| L5 | **Query instead of read** — every question a maintainer asks the file is a command, so answering it costs no context. |
| L6 | **Configuration, not convention** — prefix, paths, markers and limits are declared per project. |

L5 is the one that pays for the rest. `pick` replaces loading 558 lines to find one
task; `stats` replaces a grep whose misses are silent; `show` replaces joining two
files by hand. Those three are most of what an agent currently spends a roadmap
session doing.

### §0.4 The limits, measured against a live corpus

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced — the
reading RK20 took:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the
other 89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the
control, and it shows compliance is available. The difference is that "what does not
work" is one clause by construction and a `why` has no natural end, which is L1 stated
as a measurement: the field whose scope is unbounded is the one that needs the bound at
the write path.

And the migration is smaller than that task assumed. **74 of the 78 pointers resolve,
and none dangle**; 67 of the 70 over-length lines point at a section that already exists
and makes the same argument — compared line-against-section on SH295 and SH309, the
`why` is a recompression of the paragraph, same examples and all. The rationale is not
homeless. The line is a second copy of it, so the edit is compression against a text
already written, not authorship.

## Block A — The model

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1159 The environment nobody can reproduce

Four tasks this session were defects the suite could not see and CI could: RK1153
(fixture git calls taking the machine's identity), RK1154 (an assertion that fails once
the console script exists), RK1155 (isolation a plugin cache invalidates), RK1158 (a
call newer than the floor).

They are one difference, not four: CI installs the package (`pip install ".[dev]"`) and
runs it on a machine that has no git identity, no plugin cache, and — for one of two
jobs — the floor interpreter. Nothing here runs the suite that way, and nothing says
how.

Three of the four differences are reproducible on **this** interpreter, which is what
makes this worth a command rather than a wish:

* **installed, not on the path** — `pip install` into a throwaway venv makes `invocation()` the
  console script, which is the whole of RK1154;
* **no ambient git** — an empty `HOME`/`GIT_CONFIG_*`, which is RK1153's environment;
* **no caches** — `XDG_CACHE_HOME` and `CLAUDE_CONFIG_DIR` inside the temp tree, RK1155's.

The fourth needs the floor interpreter, and this machine has one Python. So the command
runs what it can and **says which difference it could not apply**, rather than reporting
a clean run that covered three of four — the rule `adopt`'s scope line already keeps.

What needs deciding: whether it lives in `scripts/` beside the two a developer already
runs, or as a marker the suite honours, which would put the environment inside pytest
rather than around it.

### §RK1160 A capture delivered to another backlog has no way to say so

RK1139 counted captures and RK1141 gave each one the id it was filed as, so a reworded
symptom no longer left a row nothing could clear. Both resolve that id against **the
capturing project's own backlog** — `stats` reads the ids in this project's roadmap and
ledger, and clears the row only when the stamp is one of them.

A capture of a defect *in this tool* has one correct destination: this backlog, never
the project that hit it, which is what `report --to OWNER/REPO` says. So the stamp names
an id that project does not hold, the row never clears, and the two ways to silence it
are a stamp from the wrong repository or deleting the evidence.

Measured in the Viglet Turing corpus, which held one capture whose defect shipped here
as RK1128:

    stamped RK1128 (where it was really filed)  ->  captures 1  1 unfiled
    stamped T954   (a local id, the control)    ->  no captures row at all

The control is what makes it a defect rather than a nag: the mechanism works, and it
works only for the destination that is wrong for this tool's own captures.

`add --capture PATH` is the same assumption on the write side — it files the line and
stamps the file in one project, which is right for a defect in *that* project's code and
unavailable for one in this tool's. What is missing is a stamp that records delivery
elsewhere: an id qualified by the repository that holds it, resolved as filed without
being looked up locally.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
