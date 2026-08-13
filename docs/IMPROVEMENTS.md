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

### §RK1120 The file whose diff names two tasks

RK1117 taught a departure to report a governed file it wrote and does not explain, and
it is bounded by its own reading: `written` asks whether the **file's** diff names this
id, so a file this task both wrote and is named in stays accounted for whatever else is
in it.

The roadmap is that file on every ship. Measured here, shipping RK1112 while another
session had filed RK1116: `docs/IMPROVEMENTS.md` is now reported, and `docs/ROADMAP.md`
is not — this task's marker write is in the same diff, so the added `RK1116` line rides
inside the staging line the report prints and nothing says a second id is in it.

```
$ git diff HEAD -U0 -- docs/ROADMAP.md
-- 📋 **RK1112** …          this task's own marker
+- 🛠 **RK1112** …
+- 📋 **RK1116** …          somebody else's line
```

The machinery to read it is already here and used one command over. `lint --since HEAD`
parses both revisions of a governed file to answer `block.emptied` (RK269), and a
`Document` gives entries by id — so *which ids gained or lost a line since HEAD* is a
comparison of two parses rather than a diff heuristic. An annotation refresh (RK8)
changes a dependent's deps field and is not a line gained or lost, which is exactly the
false positive a diff-level reading of "other ids appear" would produce.

What to say is one line beside the staging: which ids in this file's change are not this
task's, and that staging the file takes them. Not a refusal — a tree somebody else is
working in is not this command's to block, and the answer needed is which hunk to leave
out.

### §RK1121 The next step that is never the next step

Every `ship` that takes the last open line out of a block prints a second line naming
the door for the heading:

```
  event    RK1119  Block E  finished
           its last open line just left — `block drop E` withdraws the heading, where this
           project drops one
```

Measured in this repository across one session: **nine ships, six of those hints — D, B,
F, B, C, E — and no block has ever been dropped.** The seven headings here are the
structure of the backlog and outlive every line filed under them; a block that empties
is a block whose work is finished, not a heading anybody wants withdrawn.

The clause `where this project drops one` is the hedge that says the sentence knows
this, and a hedge is not the fix: it costs a reader the same attention on every run, and
the answer to "is this the next step" is a fact about the project rather than about the
ship. That is what `[blocks]` exists to declare and this is the one thing it does not: a
project whose blocks are permanent says so once, and the hint is then silence rather
than a line six ships out of nine have to be read past.

The other half of the same reading is `block.emptied`, the gate's own note (RK269) — a
transition worth recording, and not a suggestion to act. So the declaration turns the
*hint* off and leaves the note where it is: what emptied is history and what to do about
it is the project's, which is the split every other configurable rule here keeps.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
