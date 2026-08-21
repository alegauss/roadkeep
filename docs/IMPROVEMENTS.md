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

### §RK1289 A total reconstructed from two counts

`elided` is the count of open lines the bounded reading did not ask for, and the note
adds it to the ones it priced to say how many there are. That sum is the backlog only
while every line it asked for answered.

A line that would not compose is asked for and not priced. It leaves the ranking and it
was never elided, so the denominator loses it: four wanted of ten open with one refusing
prints "3 of 9". The number a reader takes for the size of their backlog is short by
exactly the lines the report is most concerned about, which is the population RK1288
added a finding for one paragraph earlier.

Two counts and one subtraction, arranged so that neither is wrong on its own and the sum
is. `elided` answers *what the bound left out* and is right; the note asks *how big is
this backlog*, which is a third fact and one the reading already holds — it walked every
open id to compute the bound in the first place.

So the total is carried rather than reconstructed. What the note says then is three
numbers that add up: priced, refused, and not asked for — and the reader is not left
subtracting one report from another to find out whether the shortfall was a refusal.

## Block D — The gate

### §RK1290 A note with no threshold

The note fires whenever the bounded reading left anything out, which on any real backlog
is every run. A project that declared a ceiling and holds twenty open lines prints it on
every commit, every turn's end, and every CI job — a sentence that never changes, under
a report that is otherwise clean.

RK16 already settled this shape one note over. `_collective` expands a `Block X` dep
only where it names **two or more** open tasks, because at one there is no surprise to
report and a note per token is output nobody reads. The threshold is the whole design of
that note, and this one shipped without one.

What makes it worse than noise is what noise does to a report: a reader who sees the
same line under every clean run stops reading the notes, and the next one that matters
arrives under a heading they have learnt to skip. A gate is read exactly as carefully as
its quietest run trains somebody to read it.

The fact is still worth stating and the question is when. It is news the first time a
backlog outgrows what the gate prices, and news again where the shortfall is large
enough that the ceiling is effectively unheld — and it is not news on the run after
that. Which of those two the threshold is written against is the design's to decide.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
