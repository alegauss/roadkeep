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

### §RK1003 The refusal RK1002 wrote has no code on the other side

Reproduced immediately after RK1002 shipped: a design edited by hand to name an
unclaimed id leaves `lint` clean, while `next-id` warns about it inside another
command's output, hedged, and nothing has to act on the warning.

That is RK497 read backwards. Every task in that family closed a gap where the gate held
a rule and the door did not; this is the first where the door holds one and the gate
does not, and it was opened by the fix rather than found in the old code.

Why it is worth a code rather than left to the door. L1 says the write is where a rule
is enforced and `lint` is only the backstop — *only*, not *never*. The backstop covers
text this tool did not write, which is precisely an adopted backlog, a hand edit and a
textual merge: the three ways a design gets an id in it without passing a door.

The finding is decidable from what the gate already reads — the ids each governed file
carries as a line, and the same scanner the deriver uses. It is not a repair, which of
two ids an author meant being the judgement L4 forbids, so it names the same two ways
out the refusal does.

What proves it: a hand-edited design naming an unclaimed id exits 1, the same file with
the example spelled outside the prefix is clean, and the remedy table carries a row for
the code.

### §RK1004 The other direction of the same register

RK498 enumerated every code the gate emits and said whether a write refuses it, and it
paid: the estimate of two open was five. Nothing enumerates the converse — which
refusals a *door* makes that the gate can also report — and the first hole in it was
opened by RK1002 within the hour, not found in old code.

Measured before proposing: the write path raises 35 codes and 25 are also codes the gate
emits, name for name. The remaining ten are not ten holes. Most are a section's own
shape, and the gate reports those under its own vocabulary — a body past its budget is
`section.too-long`, an anchor the scheme cannot read is `ref.format` — so the register's
rows are a *mapping* and not a boolean, and building it is exactly the judgement RK498's
`gate` rows are: stated, not measured.

What makes it worth its own line rather than a wider RK498. That register's probe drives
a write and asks what the gate then says; this one has to start from a **file already in
the state**, which is a different fixture and a different question — one is about a door
and one is about text this tool did not write.

What proves it: every write-side code has a row naming the gate code that covers it or
saying nothing does, the ten above are classified, and a code raised tomorrow with no
row is red.

## Block E — Adoption

## Block F — The plugin
