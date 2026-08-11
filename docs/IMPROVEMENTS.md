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

### §RK1080 One question, answered in two files

`linting._in_halves` answers *do the two files say this id is a live partial*, and its
own docstring says the test is "the one `shipping._already_recorded` already applies at
the door `ship` refuses at". It does not apply it — it restates it. Both were
`open_line.task.status == PARTIAL or bool(recorded.task.part)`, in two modules, and
narrowing them to the qualifier alone took two edits in two tasks: RK1075 moved the verb
and RK1076 moved the gate, one decision arriving twice because nothing made it one.

They agreed for the whole time they were wrong, which is the property that makes this
worth closing rather than watching: a duplicate that drifts is loud, and a duplicate
that stays in step is a rule nobody can find the second copy of.

The direction is settled by import order. `linting` reads `shipping` already, `shipping`
does not read `linting`, and the question is the verb's — whether this line can be
closed — with the gate asking it to decide whether to report. So the predicate belongs
beside `_already_recorded` and the gate calls it.

What that costs is one function's worth of care about arguments: the gate holds an
`Entry` pair and the verb holds a `Config` it re-reads both files from, so the shared
form is the narrow one over two entries and the verb keeps the lookup. Worth checking
whether `_others_pointing` and `_orphans` are the same shape one relation over.

## Block C — Query

## Block D — The gate

### §RK1079 The axis the table names and does not sweep

`tests/test_doors.py` opens by saying the states are a roadmap marker crossed with what
the ledger holds *crossed with whether a deferred store carries it*, and then sweeps the
first two. The third is named in the sentence and absent from the table, which is the
shape RK496 already measured once: a survey that says what it covers and covers less.

What is outside is not small. `resume <id>` is a door no row exercises. A paused id the
roadmap **also** carries is a two-files contradiction with its own resolution. A project
that declares `deferred` after lines were already set aside, or removes the declaration
with a store on disk, is the adoption shape `[files]` makes reachable — and `defer`
refuses with a message about the missing key, which is a door for the *config* rather
than for a state.

The reason it stopped where it did is honest: every cell was built by writing two files,
and the store needs a third plus a `[files]` key, so the fixture is a different shape
rather than one more parameter. That is a reason to write the fixture, not a reason for
the closure to quantify over two axes while its own docstring claims three.

Worth deciding whether the third axis is the store or the *role set*: a project with a
strategy file and no improvements has states the pointer half of this model reaches, and
the same argument would put those in the table too.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
