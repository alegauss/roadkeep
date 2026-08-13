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

### §RK1126 The paragraph that carries no id

`written` credits a path where its diff **names this id**, read off `git diff HEAD -U0`
— so what accounts for a rationale file is a *heading* being written, `### §RK2 …`
carrying the id in an added line. A `section amend <id> --body` rewrites the paragraph
under that heading and touches no line carrying the id at all.

Measured while writing RK1125's tests, which is how it was found — the fixture amended a
body and the reading came back:

```
Scope(mine=('src/a.py',), theirs=(), loose=('IMPROVEMENTS.md',), …)
  loose    IMPROVEMENTS.md  (no claim names it)
```

The file this task had just edited, reported as a change no claim accounts for. That is
RK1117's sentence pointed at the author's own work, and it is the failure RK342 named
from the other side: every dirty governed file handed to whoever asks was wrong, and so
is every one withheld — the author declares the path by hand to silence it, and the
scope then carries paths that were never the work.

The reading that decides it already exists one command over. `lint --since` parses the
file as it was so a removal is attributed to the section that **held** it (RK36), and
`changed_lines` gives the line numbers. A prose file is this id's where its changed
lines fall inside the span of a section this id owns — `sections.owners` being the
reader of that ownership, including the outline case where the id lives in the heading's
title rather than in its anchor.

### §RK1127 The subtree that is not a stranger

`designs_since` labels each section by the id its heading names, or by its anchor where
it names none, and `sharing` then subtracts the id being committed. Under the id scheme
a subsection's anchor is `§RK2.1`, which is not the string `RK2` — so this task's own
subtree survives the subtraction and is reported as another session's design.

Measured in a scratch repository, one subsection appended to the section being shipped:

```
$ designs_since(config, "HEAD", "improvements")
frozenset({'RK2.1'})
$ … - {"RK2"}
{'RK2.1'}
```

So the report a departure prints would name `RK2.1` as work this commit is carrying for
somebody else, on the ordinary shape RK1112's own docstring describes: *a `§<id>.1` is a
section with an anchor of its own, amended by naming it*. A reader who trusts one false
`shared` line stops reading the true ones, which is the whole cost of the rule it
belongs to.

The comparison is the wrong one and the right one is already written. `sections` reads
an address **segment by segment and never as a string prefix** — the care `_extends`
takes so `§0.1` is not read as extending `§0.10`, and `descending` is the reader that
answers which anchors are one address's own subtree.

Which leaves a question the fix has to answer rather than inherit: a subsection of
*another* task's design is that task's, so the exclusion is "extends this id" and not
"starts with it", and an outline's `XVI.12.3` is nobody's id at all until its title says
so.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
