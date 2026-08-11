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

### §RK1085 A read per pair over documents the run already holds

`_carried` walks `PAIRS` and calls `config.document(pair.second)` inside the loop. Today
that is one extra read — the ledger is already loaded and passed in, the store is not —
and with a fourth carrier it is two. The parse itself is cached by bytes (`_parsed`), so
the cost is small and the shape is the argument: a check that reaches for a file the run
has already opened is one that will reach for the next one too.

`lint` loads the governed documents at the top of `_examine` and hands them down;
`_carried` takes `roadmap` that way and then goes back to the config for its partner.
`Backlog.load` is the reader that already holds all three, and it is what `_deps` and
`_queued` are given. So the seam exists and this check is on the other side of it.

Worth doing with RK1084 rather than before it: that task adds the third pair, which is
the first time the loop reads two partners rather than one, and a refactor of a
one-iteration loop is a refactor nobody can measure. Together it is one edit with a
number on it.

What not to do is thread a fourth argument. The signature already takes `config` and a
document; the shape that scales is the one `_deps` has — a `Backlog` in, roles read off
it — and that is a change to what the function is handed rather than to how many things
it is.

## Block D — The gate

### §RK1084 The third pair, named and not read

`referring.PAIRS` declares three pairs of governed files that can hold a line for one id
and the gate reads two. The third — changelog against the deferred store — carries a
`because` instead of a code, and the honest reason is that nobody has met it: RK118
orders a departure's writes so the ledger goes first, and a crash between them leaves
exactly this.

What stopped RK1082 from writing the rule is that the repair is not obvious. `resume`
places an open line, and placing one for work the ledger records as gone is the
contradiction again with the files swapped. Removing the store entry silently is a write
no verb makes, and one that deletes the only record that the work was ever paused.

Two candidates, and picking is the task. `record drop`-shaped: a verb that removes the
store's copy and says what it removed, which gives the finding a door. Or
`retire`-shaped: the store entry becomes a departure of its own, on the argument that a
pause ending in a shipment is history the store should not keep.

The measurement that would decide it is whether an adopting corpus has this state. Shio
and Turing both declare a store; a count there is one command and turns a design
argument into a reading. RK1077's point is that a state found by enumeration is cheaper
than one found by the project that reaches it, and this is where that pays off.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
