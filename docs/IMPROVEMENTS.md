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

### §RK1282 One value where the project wrote several

A table spelled with a placeholder is declared once per something the project names —
`[budgets."agents.md"]`, `[limits.changelog]` — and the shape publishes it under one
address. So the value it reports is one of however many the file carries, chosen by
whichever came last, and nothing beside it says there were others.

Measured here: this project budgets two files, and `config --table budgets.<path>`
answers `lines` as 12 and `bytes` as 800 — the second entry's numbers, presented exactly
like a key with one value. A reader takes that for the project's budget. The one it is
about declares 125 and 8400.

The fact was always ambiguous and the row is what made it look answered. Before, that
column said `declared` and nothing more, which was thin and true; now it is precise and
wrong, which is worse — a number a reader can act on and should not.

Three shapes are honest and one is not. Say how many addresses declared it, and let the
per-address answer stay `budget --file` and `govern`'s. Say nothing, going back to the
bare word for placeholder tables alone. Or key the row by the address the project wrote,
which is a listing whose length is the project's and not the build's — and which stops
the shape being *the shape*, since a caller asking what may be declared is not asking
what was.

What it must not keep doing is print one of several as though it were the one.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1280 The one file the guard allows, and what it could say

The guard's own sentence is that `roadkeep.toml` is not governed, "which a human edits
by hand on purpose". That was right when nothing else could write it, and half of it
stopped being true: four of its tables now have a verb that takes the reading first and
refuses a number this corpus already breaks.

So the two writers disagree about what is checkable. A `symptom = 90` typed in is
accepted and reported by the gate on the next run; the same number through the verb is
refused before it lands, naming the line that measures more. The first is the
arrangement this project exists to replace, and it is still the default.

**Denying it is the wrong answer** and the reason is in the shape of the file. A hook
sees a path, not a table: `[files]`, `[markers]`, `[refs]`, `[grammar]` and the rest
have no verb and are not going to get one, so a denial would make the config unwritable
in the sessions that need it most — including the one where `install` has not run yet.

What is missing is the notice. The guard already has the register for it: it allows, and
says what would have answered. An edit to this file is where a reader most needs to be
told that four of its numbers have a door, and the one sentence costs nothing on every
other turn — it fires on a path nobody touches twice a year.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
