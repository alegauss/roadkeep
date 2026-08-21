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

### §RK1300 The criteria arrive when the block empties

RK1265 put the definition of done somewhere a ship cannot delete it, and RK1265's own
reasoning says when to read it: before a block's last open line ships. The trouble is
that nobody knows a line is the last one until the ship answers. So in practice the
reading happens after, and only because a sentence in a project's own skill file says to
make it.

Measured on winwright, twice in one sitting. Block A emptied at WW7 and Block B at WW15;
both ships answered `finished` with the standing sentence and the count, and neither
carried the three criteria that decide whether the word is true. Both readings then cost
a `criterion list` call, and both were made only because that project's
shipping-discipline skill remembers to say so - which is a rule carried by prose, in one
project, and therefore a rule the next adopter does not have.

The fix is where RK408 and RK1164 already put things: the event. When a ship flips a
block's stage to `finished`, that block's criteria go in the payload beside the
standing, each with its `why`. Nothing is enforced by this and nothing could be -
whether the work satisfies a criterion is a judgement (L4) - but the list arrives at the
one moment it is owed, in front of the person deciding whether to open the next block.
On the empty stage it is silent: a heading declared before its lines has nothing to have
satisfied.

## Block C — Query

### §RK1298 One budget and its deltas, not two tables

Measured on winwright, a greenfield adopter with 106 open lines: `brief WW1` answered
with a `budget` object and a `shipping` object whose rows are the same rows. They differ
in six values - the marker, `open_line`, `structure`, `ref`, `prose`, and one field's
`drafted` flag - and everything else repeats: both `section` sub-objects are
byte-identical, and both carry a full row per prose field with the same limit, aim,
taken, unit and source. The second copy is the first with the shipped marker swapped in,
which is arithmetic the caller could do and never asked for.

That is worth a line because RK1286 gave this read a ceiling for exactly one reason: it
is the answer that replaces reading the file, so what it spends is what the agent has
left for the task itself. A table paid for twice is the largest thing in that payload
which is not information, and it grows with every field a project declares a limit on.

What it should answer instead is one budget plus the deltas the ship would apply - the
six values above, named - rather than a second table a reader has to diff against the
first to find out that five of its rows say nothing new. The figures stay reachable;
what goes is the repetition.

## Block D — The gate

### §RK1299 One row per fact, not one per line

Measured on winwright the moment its first block finished. `lint --json` on a clean
tree: 25,823 characters, 0 problems, 42 notes. Every note is `deps.collective`, and
between them they state six facts - Block A names 2 open tasks, Block C 8, Block D 10,
Block E 14, Block G 7, Block K 19. A line depending on three blocks contributes three
rows, and eleven lines depending on Block G contribute the same sentence eleven times.
Each row also carries a `remedy` object whose `what` is the same 78 characters every
time, and whose `argv` differs only in the id.

The text form of the same run is 5,149 characters, so the payload a tool result actually
reads is five times the one a terminal gets, for a verdict of `clean`. RK1286 gave
`brief` a ceiling because it is the read that replaces reading the file; the gate runs
at the end of every turn, which is more often, and has none.

RK1165 already settled the shape of the answer for `gaps`: a run of rows saying one
thing becomes one row with its count. Here that is one row per block naming the
expansion once, with the lines that depend on it listed, and the remedy prose stated
once for the class rather than per row.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
