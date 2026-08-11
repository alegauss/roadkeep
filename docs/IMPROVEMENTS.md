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

### §RK1069 The move the test was written before

RK1065's title sequenced this — *held by a test before it is a package* — and the test is
what shipped. `tests/test_kernel.py` names `schema.py` and `document.py`, the one runtime
call above them (`exporting.refreshes`, RK188) and the one annotation (`Config`, under
`TYPE_CHECKING`), and holds the backlog vocabulary they declare as a ceiling: 47 names and
17.

A ceiling with nowhere to fall is where that leaves it. Both modules sit beside the
thirty they are supposed to be under, so nothing about opening either file says which
half of the package it is, and the rule that they import nothing above them is a test
somebody has to know exists rather than a directory that makes the violation not
compile.

The move is `src/roadkeep/kernel/`, and its cost is entirely in addresses: about
twenty-two import lines in the package, the `("document.py", "_parsed")` keys in the
cache inventory, `tests/surface.py`'s census, the Layout index, and `test_kernel`
itself. No behaviour, and the round-trip property test over three corpora is what says
so.

Worth doing after the vocabulary comes down rather than before. A directory named for
the mechanism, holding two files that define `Task` and `Dep`, advertises a boundary it
does not have — and the rename that fixes that is the larger half of this work, touching
every caller of the two names rather than every importer of the two modules.

### §RK1072 The larger half, and the one with a meter on it

`tests/test_kernel.py` records what the two mechanism modules pronounce of this
backlog's vocabulary: 47 names in `schema.py` and 17 in `document.py`. The ceiling is
the deliverable RK1065 could make; bringing it down is the work it could not.

Not a rename. `Task` and `Dep` are the mechanism's own words for *a record* and *a
reference*, and swapping them for `Record` and `Reference` touches every caller in the
package to buy a synonym — the cost this project refuses when the win is a better name.
What is actually in the wrong file is narrower and moves without renaming anything:
`as_ledger`, `LEDGER_SHAPES`, `_ledger_slots`, `block_dep_pattern`, `_check_deps` and
their neighbours are *this backlog's rules* living in the two files that are supposed to
hold none. Each is a function whose callers already sit above.

The meter is what makes this incremental rather than a rewrite: every move drops the
count, the test refuses a rise, and there is no point at which the package is
half-migrated in a way anything can be wrong about — the import direction rule holds
throughout, because moving a rule *up* never creates an upward import.

Where it stops is a judgement, and the honest answer is when what is left reads as a
format library: a record, a reference, a file that round-trips, and no opinion about
what any of them mean.

## Block B — Authoring

## Block C — Query

### §RK1071 The citation reached the refusal and not the read

RK1067's argument is that an author standing over a limit should be one line from where
it was set, and it delivered that on the refusal: `limit is 150 (roadkeep.toml:10
[limits].why)`.

`budget` is the same author at the earlier moment. It exists precisely so the number
arrives *before* the prose does — that is the insight the whole tool is built on, the
saving being the analysis rather than the characters — and it prints `why 30 of 200
left` with no hint that 200 is this project's choice or this tool's default. So the fact
reaches the author on the path they take when they got it wrong and not on the path they
take when they are about to get it right.

`Schema.source_of` already composes the clause and `budget` already holds the schema, so
this is a print and not a mechanism. What needs deciding is the terminal's shape: the
read is a column of small numbers and a parenthesised address after each would drown it,
where one line under the table naming the file — and the two roles, since
`[limits.changelog]` differs — probably says it once.

The `--json` half is not a layout question and is simply missing: a payload that carried
the origin beside each figure would let the surface that serves this over MCP answer
*why is it 200* without a second call, which is the read that costs a turn.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
