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

### §RK1068 The one invariant a declaration adds

This is the cost a declared grammar does not remove, and it is worth naming before the
trade is made. Several hardcoded invariants become one: a grammar given as data can be a
grammar that cannot read back what it writes, and the failure surfaces at the wrong end.
The round-trip guard refuses the whole file, correctly and by law — so a separator
declared one character too loose presents as every line in the corpus being
non-canonical, and the report blames a hundred lines for the one line of config that
broke them.

The check is small and belongs to the gate: for every record the corpus holds, rendering
what was parsed reproduces the source bytes, and parsing that rendering is stable. Which
is this repository's own conformance rule — the docs are the fixture, and a limit that
cannot express these lines is the wrong limit rather than a set of wrong lines — moving
from a development convention to something the tool runs against itself. An adopting
project gets it against its own files, which is where a hand-written grammar is actually
dangerous.

It stays code, necessarily: a declaration cannot carry the check of declarations without
becoming the interpreter that design refused. And it pairs with the finding that cites a
rule's origin, because with both the report reads as one defect at one config line
instead of a corpus that stopped conforming. The trade is still good; it is not free.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1067 A finding names the rule's source, not only its number

Every code this gate reports resolves to a door and prints it under the line — a
complete argv where one exists, the two doors where the choice is the author's, a marked
blank where the field is prose only they can write. The finding whose remedy is
*changing the rule* is the one with no such door: a `why` reported over its limit names
the number and leaves the author to find where the number was set, which in an adopting
project is a file they have never opened.

So the diagnostic carries the rule's origin beside the value — `why exceeds 200 (schema:
roadkeep.toml:34 [limits].why)` — and two things fall out. A wrong limit stops being a
defect in this package and becomes a config line somebody reviews, which is the argument
for a limit being configuration at all, finally reaching the reader who is standing over
one. And a limit the project never declared has no line, so the answer says it is this
tool's default rather than inventing a citation; that distinction is exactly the fact
the author needs, one of the two numbers being one they chose.

It ships alone. Nothing here waits on a declared grammar: the config already records
which keys a project set, and the validator already knows which limit it applied. Worth
taking first for that reason — the smallest of these, and the one an adopting project
feels.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
