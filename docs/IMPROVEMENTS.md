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

### §RK1363 A decision's body needs an address the outline can spell

RK1361 gave the decisions role prose and proved it on this repository, which numbers its
anchors by id: `section add RK1361 --role decisions` works because `§RK1361` *is* an
address. Under `ref_scheme = "outline"` it is not. Measured on a throwaway outline
project: the same call is refused `anchor.format` — "not an <x.y> outline anchor" — and
the remedy printed under it opens a block that already exists and then files a **new
task**, which is the wrong staircase entirely. So the two live corpora, Shio and Turing,
are the projects this feature cannot be used on.

Two things are missing and they are one decision. The record has to name its body, which
under an outline is a field and never derived — the same `--ref` `add` takes, on the
ship that files the decision. And the address has to come from somewhere: `anchors
--role decisions` answers with the next free top level out of the numbering the
*improvements* file shares, so a decisions body claims an address its sibling would
otherwise spend. Whether that is a `[refs]` namespace declared for the role or one
numbering both files agree on is the question this task settles; what is not open is
that a body no outline project can write is a store two corpora have no door into.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1364 The session ceiling outlived the total it was argued against

RK1360 made publication a question about the project: this checkout is sent 64 tools and
63,594 units where the package has 66. `[tools] session = 64,700` was argued eight times
against the other number — a total no single project ever spent — and it is now a
ceiling whose subject moved underneath it.

The reading is what makes this decidable rather than a matter of taste. `govern
tools.session` measures one site, and that site is *this* checkout, so the declared
number is 1,106 above a figure that will differ per adopter: a project declaring every
role pays for `defer`, `resume` and `supersede` on top, and one declaring three roles
pays less than this one. So the number answers neither question — it is not the widest
project's bound and it is not this project's.

What has to be decided is which of the two the key means, and the answer is visible in
what refuses: `lint` runs in *a* checkout and refuses *its* surface, so the ceiling is
per project and the number is re-taken from the reading here. The other half is the
comment stacked above it, which argues from the package total and is now the record of a
question that was settled differently — `govern --because` is the door that replaces it.
