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

### §RK1291 One rule, kept by one of two forms

The read states a rule and keeps it in one of its two forms. Asked for every line it
walks the open ones, on the argument that a shipped id has no brief left to start work
from and a paused one is a line `pick` can never offer — pricing either would be
measuring an answer nobody asks for.

Named, it prices whatever it is handed. `budget --brief` on a task that shipped two
commits ago answers 632 against a ceiling of 3300, and that number is about a different
shape: a shipped brief carries no allowances, no deps and no design, because the ship
deleted them. It is a figure with a unit and no meaning, printed under a header that
says how much room is left.

The rule is right and the form that breaks it is the one a person types. A caller naming
an id is usually naming one they are about to work on — and where they are not, the
answer they need is that this line has no brief to price, which `brief` itself already
says: it briefs a shipped id as `shipped` and quotes no cost for starting it.

So the named form asks the same question the unnamed one does, and answers the other
case as the absence it is. What it must not do is hand back a number that looks like
every other number in the table and is not comparable to any of them.

### §RK1292 A verdict wider than the reading behind it

The header states a verdict the ranking is not entitled to. `3300 allowed, 0 over` is
printed beside a listing that just said one line could not be measured — so the count of
what exceeds the ceiling is taken over the lines that answered, and reported as though
it were taken over the backlog.

That is RK1288's finding at the printer. The reading learnt to name what it could not
compose, on the argument that the widest is the bound and an unmeasured line is the
shape most likely to be it; the sentence above the listing kept counting as if nothing
had been left out. A reader who trusts `0 over` and stops there has been told the
ceiling holds by a report whose own next line says it does not know.

The gate does not have this problem, and the difference is instructive: there the
absence is `read.unpriced`, its own finding, and the exit code is 1 either way. Here one
string carries both the count and the confidence, and only the count was corrected.

What the header owes is the qualification, not a different number. `0 over, 1 unpriced`
is the same arithmetic with the claim narrowed to what it covers — and where nothing
went unmeasured it reads exactly as it does today, which is the property that keeps the
ordinary answer short.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
