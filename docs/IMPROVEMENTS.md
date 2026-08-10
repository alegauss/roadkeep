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

### §RK495 A directory is one path to the staging line and none to the loose list

Reproduced on a scratch project: a claim declaring `src/` printed `stage git add -- src/
…` and, three lines down, `loose src/a.py (no claim names it)`. One command, one file,
two answers — and the second is the one a caller acts on, because it is the analysis
`git add -A` cannot make and the reason a scope is declared at all (RK280).

The split is in `claiming.scope`. `loose` is a subtraction over names — `one for one in
changed if one not in named` — while `idle` beside it calls `_stages`, which already
reads a declared directory as covering what is under it, RK295 having found that
comparing one by name reads as a typo wherever a project scopes by folder. The fact is
known one attribute from where it is missing.

What it costs is the whole read: a caller declaring `src/` and `tests/` sees their own
work listed as somebody else's to decide about, and the honest answer to that report is
to declare every file by hand — the scope this verb exists to spare them. Worse on
`ship`, which makes the same read at the moment of committing (RK294) with no claim left
to correct it against.

What proves it: the same declaration answers `loose` empty, a file outside every
declared path still lands there, and `theirs` reads a directory the same way — a second
session's `src/` covering `src/a.py` is one question from the other side.

## Block C — Query

## Block D — The gate

### §RK496 A survey that covers less says nothing, and a green suite says it is fine

Measured on RK494, which added `src/roadkeep/verbs/` and its eight modules. Five
suite-wide surveys had to be found by hand. Two failed loudly and were the cheap ones: a
census keyed by `m.name` let `verbs/shipping.py` answer under `shipping.py`, counting
one file as another. **Three kept passing while covering nothing new** —
`test_remedying`'s two sweeps for a spelled command and `test_provenance`'s for a
hard-coded verb, each a `glob("*.py")` written when the package was flat.

The third state is the one that matters, because a red test is a message and a green one
that stopped looking is a claim. RK488 built those two sweeps precisely to say how many
spellings were left; after RK494 they answered about 43 of 51 files and said so nowhere.

So the surface is the package's own source, and what is missing is any statement of it:
each survey re-derives its file set inline, so there is no name to import and
`tests/test_invariants.py` has nowhere to record a row (RK491). A survey is a property
over a set, and this set is the one nothing declares.

What proves it: adding a module in a new directory turns a survey that would have missed
it red, the count each one covered is stated rather than implied, and `INVARIANTS`
carries the row.

## Block E — Adoption

## Block F — The plugin
