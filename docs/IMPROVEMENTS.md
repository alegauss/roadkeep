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

### §RK1075 Closing a line the ledger already recorded

Shio filed three capture reports on one state and closed it with a hand edit. A line
stands at the partial marker while the ledger entry for its id carries no qualifier: the
line says a half landed, the entry says the whole did. `ship` refuses, the door in its
message suppressed because the closure path deliberately does not take a partial
(RK1045); `retire` refuses through the same transaction; `defer` refuses because a pause
is between open and terminal; and the gate is silent by design (RK121).

RK1046 opened one exit — `record amend <id> --part "…"` is permitted while the roadmap
still carries a live partial, after which `ship <id>` completes the entry in place. It
works, and the third report was captured against a build that already had it. That is
the measurement: an exit no refusal names is an exit nobody finds, and what the author
reached for instead was the editor.

It is also the wrong shape. The qualifier is a claim about the delivery — which half
landed — and here nothing landed in halves, so the only repair asks an author to write a
false sentence into history in order to open a door. This task is the direct one:
closing a line whose entry already records the work should not pass through the ledger
at all, and every refusal standing in front of it — shipping.py's on both doors,
deferring.py's — names it.

### §RK1077 Every state a file can reach owes a door

The barrier denies every hand edit to a governed file, and that trade is only honest
while the verb surface is complete. It has not been. RK65: a line could be created and
removed but never corrected. RK123: a rationale no verb could amend. RK141: a block
heading only a hand edit could write. RK143: an entry filed under the wrong block.
RK403: a heading declared twice. RK1046: a partial line beside an unqualified entry.
Each was found by the project that walked into it, and each cost a capture report, a
session or a hand edit before it was named — which is the same defect six times, not six
defects.

Coverage is testable, because the states are enumerable from the model rather than from
imagination: a marker, crossed with what the ledger holds for that id, crossed with
whether the pointer resolves and whether the deferred store carries it. What is missing
is the table pairing each reachable state with the verb that leaves it, held by a test
the way tests/surface.py holds the module census, so a state with no door fails here
rather than in someone's adoption.

A cell deliberately left empty is a declaration and not a hole; the point is that it is
written down, and that a new marker, a new store or a new role adds rows nobody can
leave blank by accident.

## Block C — Query

## Block D — The gate

### §RK1076 The contradiction the gate reads as a partial

`_in_halves` in src/roadkeep/linting.py answers one question: do the two files *say*
this id is a live partial, rather than contradict each other? A partial marker on the
open line is enough on its own, and RK121 made that deliberate — a corpus that adopted
the format writes the marker and no qualifier, Shio carried seven such ids, and a
finding whose only avoidance is a syntax error teaches the syntax error.

That argument held while the state had no repair. It stopped holding at RK1046: a
finding here now names a command instead of asking for a deletion, which is the line a
report may cross. Silence costs more than the noise would. `pick` offers the line
forever, `repair` cannot reach what `lint` never reports, and the author's only evidence
that anything is wrong is a refusal from whichever verb they happened to try — three of
which refuse in the same words.

What the gate has to separate is the corpus that never used the qualifier from the file
that contradicts itself, where the entry claims the whole delivery and the line claims a
half. The second is the one to report, with the door that closes it under the line, so
the finding is one `repair` spends rather than one an author reads.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
