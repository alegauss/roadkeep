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

## Block E — Adoption

## Block F — The plugin

### §RK1237 What the guard in front of the write costs

RK1235 put a guard in front of every governed write and never measured it. RK1192 did
the opposite for its own per-turn check — 0.07 ms unwired, 0.86 ms wired, against a 43
ms floor — and stated the numbers in the docstring, which is the standard this fell
short of.

What the guard reaches is not small. Past `[install] pinned` it calls `engines`, which
calls `engine()`, which runs **three git subprocesses**: `ls-files`, `rev-parse` and
`status --porcelain`. Cached per process — and a CLI write *is* a process, so a project
that pinned pays all three on every `add`, `ship` and `amend`. The MCP server is the
other case and the better one: it is long-lived, so the cache holds.

The measurement decides the shape rather than the other way round. If it is
milliseconds, the docstring gets its numbers and nothing else changes. If it is not, the
narrowing is already visible: the verdict this guard acts on is `behind`, which is
decided by the version and then by the sha — and `status --porcelain` only separates
`unpinnable`, a state this guard treats as agreement. A reading that stopped before it
would drop a third of the cost and answer the same question.

What not to do is cache it in the store: a copy's revision is exactly the fact that
changes under you, and a stale answer would refuse writes from the copy that is now
correct.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1236 The argument that spent the budget

`budget --tools` ranks the served tools and prints the room each has left, which answers
*which tool is over*. Twice in one block that was not the question being asked.

Measured here both times. RK1190 put `budget` at 2637 against 2600 and RK1233 put `ship` at
2659. In both the tool was named by the finding itself, and what was missing was **which of
its arguments spent the bytes**. Both times the answer came from a throwaway script that
imported `descriptor`, serialised each property and sorted by length; both times it found
one `--help` string carrying four fifths of the overrun beside five already terse.

Without it the repair is a reader guessing at their own prose. The first attempt
shortened the argument just added, which was the smallest of the six, and the ceiling
was still crossed; the one that worked shortened a sentence written three tasks earlier.

So `--tools` grows a form taking a tool: the same ranking one level down, over one
`inputSchema`'s properties plus the description, in the units the ceiling counts.
Nothing new is measured — `descriptor` builds exactly what is published.

To settle: whether the tool is a flag or `--tools`' own value, since `budget --tools
ship` reads as a filter and is what a caller reaches for. And whether a row names the
argument or the `help=` string it came from — an address a reader can open is what made
RK1192 actionable.
