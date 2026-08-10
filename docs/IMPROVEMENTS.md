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

### §RK470 The remedy that is complete on one file

RK420 promises a complete argv where one exists, with the id and the line already
substituted. On a project declaring two prose files it is not complete. Measured by
running `repair` over a copy of Turing:

    docs/STRATEGY.md:683  section.stale  XIV.2: T630 is in the changelog …
    FAILED  section drop XIV.2
    roadkeep: no §XIV.2 section in docs/IMPROVEMENTS.md

The finding names `docs/STRATEGY.md` and the remedy looked in the improvements file,
because `section drop` defaults to the role a project with one prose file has and the
table's argv never says which. `--role` is a flag the command already takes; the row
does not pass it.

Three rows are affected — `section.stale`, `section.unreachable` and `section.drop`'s
neighbours — and they are exactly the codes reported *about a prose file*, which is
where `_role_of` already answers: `id.duplicate` varies on it (RK420's own `varies`), so
the reader exists and the mechanism does too.

It is invisible on every project that declares one prose file, which is this repository
and most adopters, and certain on the ones that declare two — the same corpus RK340 and
RK346 were written for.

Open: whether the role belongs in every remedy that names an anchor, or only where the
project declares more than one file, since a `--role` on a single-file project is a word
that changes nothing.

### §RK471 The count that counts attempts

`repair` runs every finding whose remedy is a complete command and prints what it cannot
close. Run over a copy of Turing:

    ran     block merge AH
    FAILED  section drop XIV
    FAILED  section drop XIV.2
    3 repair(s) ran, 34 left for you

One ran. Two are printed `FAILED` three lines up, and the summary counts them as run.

The exit code is right — 1 while anything is left, which is RK422's contract and the
thing a script branches on — so what this costs is the reader, not the loop. But the
number is the line a person acts on, and it disagrees with the lines above it in the
same output: a caller who reads `3 ran` against `34 left` concludes the tree moved three
findings closer and it moved one.

The fix is arithmetic and the shape is already there — `FAILED` is printed per step, so
the counts are separable at the point they are decided.

What it must not become is a second exit code. Two failures are not a failure of
`repair`: the whole design of RK422 is that what it cannot close it *prints*, and a run
that closed one of three did exactly what it says it does.

Open: whether `left` should count the two that failed apart from the thirty-two nobody
tried, since one of those groups has been attempted and refused and the other has not.

## Block E — Adoption

## Block F — The plugin
