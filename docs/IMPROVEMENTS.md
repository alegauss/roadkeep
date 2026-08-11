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

### §RK1102 Ask the parser, never the line

Twice now a predicate has guessed from a governed file's text what `Document` already
answers, and both were green until the one day they were not.

RK1090 asked whether a project has a queue by counting entries, so any empty-queue day
reported this repository as queue-less; the fact was the heading, and `queueing.opened`
answers it. RK1098 asked whether the backlog has an open line by looking for `- ` at the
start of a line — and the roadmap's non-goals are bullets, so the fixture that exists
for an emptied backlog answered "populated" on exactly the state it defends.
`document.entries` answers it.

Both were written by somebody holding the parser in the same process. That is what makes
it worth a rule rather than two fixes: the shape is cheap to write, reads as obviously
correct, and fails only against a file arrangement the author was not picturing — which
is every arrangement a corpus has and this repository does not.

The rule to state is one sentence, and where it goes is the question: `agents.md` is at
123 of 125 lines, the skill governs the write path rather than the test suite, and a
check that finds this shape mechanically would have to read test source.

## Block B — Authoring

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK1101 Which directory a path argument is relative to

`-C` says it is "where to start looking for roadkeep.toml", and every path argument
still resolves against the process's own working directory. The two are consistent only
until both directories hold a file with the same name.

Measured while writing RK1100's tests: `main(["-C", str(tmp), "adopt", "ROADMAP.md"])`
exited 2 naming `D:/Git/alegauss/roadkeep/ROADMAP.md` — the repository's file, under the
temporary project's config. That is the loud half. The quiet half is a project that
*does* have the file: the estimate is then a real measurement of the caller's backlog
reported under someone else's prefix, markers and limits, and nothing in the output says
which tree it read.

Two answers, and the choice is the whole task. Resolving relative paths against the
config root makes `-C` a project selector and matches how every other argument behaves
once discovered. Leaving it and *naming the tree* in the report is smaller and keeps
shell completion honest. Worth checking which other verbs take a path — `claim --path`,
`adopt --with`, `install` — and whether any already resolves the other way, because two
rules would be worse than either.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
