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

### §RK1281 The claim a decision inherits, and the limit it meets

`ship --decides` composes the decision from the task's own claim and the author's
sentence, which is right: a decision is *about* the problem the line stated, and
restating it would be the second sentence RK142 refuses to inherit one file over.

What that inherits is the claim's **length**, measured against a limit the caller cannot
reach. A project declaring `[limits.decisions] symptom = 40` refuses a ship whose
roadmap symptom is 54, over a field no flag on that call writes — and the message offers
the remedy every symptom overrun gets: put the remainder in the improvements section.
That section is being deleted by this ship. The only door left is `restate`, which
rewrites the roadmap's claim to satisfy the decisions file, and the roadmap line is the
one thing here that was already correct.

Reproduced on a scaffold, not supposed. It costs the whole transaction: the ledger entry
and the deletion are refused with it, so a project that tightened that one limit has a
`--decides` it cannot use and a `ship` that works only without it.

Two ends and only one is the tool's. `brief` prices the ledger sentence and now the
decision's `why`, and it never priced this — so the refusal arrives at the write with no
read that could have said it. Whether the claim is *shortened* for that file, or the
limit is refused at declaration, or the read simply names it, is the decision this
task's design has to make.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1283 One reading per call, on the path that is hot

The barrier reads the project once per allowed write and now reads it twice. `guard`
walks the paths a payload names and asks `governed` for each, which finds the config and
loads it; where nothing is governed it answers `None`, and `advise` then discovers the
same config and walks the same paths again.

The second read lands on the **hot** path and the first does not. A refusal is rare; an
allowed write is every `Edit` a session makes here, and this hook runs before each. What
the barrier has always been careful about is what an allowed call costs — the argument
for a closed tool list, and for `_mentioned` deciding by substring rather than parsing.

Measured as a shape rather than in milliseconds, which is the honest claim here: one
`find_config` walk up the tree plus one `tomllib` parse, per write, for a sentence that
fires on one path. The parse is the part that is not free.

The reading exists and is thrown away. `governed` already resolved the config for each
target and `guard` discarded it on the way to `None`, so what is missing is a shape that
carries it out — the same thing `Whereabouts` is one module over, and the same repair.

What must not change is the order: the advice fires only where the refusal did not, and
a call that produced both would be two messages about one write.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
