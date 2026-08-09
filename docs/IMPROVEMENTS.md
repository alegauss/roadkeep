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

### §RK441 The duplicate check's figure is unreproducible, and the fact under it is stronger

Three copies state it — the `delivered` help, the guard's denial table and the shipped
skill — and each argues the same right decision from it, that a duplicate cannot be
refused. The decision holds; the number does not. Re-measured on this ledger, BM25 over
the 426 shipped symptoms ranks the true partner of all four `superseded by` pairs at #1,
#2, #1 and #1 inside its own block, and #1 to #3 across the whole file.

What actually fails is the score, not the rank. Two of the four true pairs score below
the 13th percentile of the top-1 score a proposal with no duplicate produces, so a
threshold catching all four flags 419 of 426. That is the fact the refusal rests on, and
it is the stronger one, because it holds however good the ranking gets: relative order
inside one query carries signal, the absolute score carries none, and a gate is
therefore impossible rather than merely unreliable.

A figure nobody can reproduce is worse than no figure where three copies publish it and
one of them ships to every adopting project. Whether the original was measured against a
different query, a different pool or a different field is unknown and now unrecoverable
— which is the second half of the defect, a number stated without its method.

### §RK442 The pre-add read is the last query that answers by printing the file

`delivered` is one of the two reads before an `add`, and the one query left that answers
by printing the file: `delivered B` is 103 lines and 9,773 bytes spent to decide one
question, which is L5 unapplied to its own verb. `--near` ranks that block's entries by
the sentence about to be proposed and prints the few nearest. Measured on the four
`superseded by` pairs this ledger records, the true partner lands at #1, #2, #1 and #1
inside its block — five lines instead of a hundred, at the same recall.

Three constraints are the design. It never refuses and never warns: RK441 measures that
the score separates nothing, so the absence of a threshold is a known result rather than
caution, and the ordering is printed for a reader to use. It stores no index — BM25
rebuilt per call costs 0.23 ms over these 426 entries and 0.73 ms over Turing's 892, so
a second store would buy nothing and cost L2. And it takes no dependency: the ranking is
some fifty lines of stdlib, where Lucene is a JVM and every Python index is a wheel.

The no-model non-goal is not reached. Nothing here writes prose or judges meaning; it
orders lines that already exist by word overlap, and the answer is unchanged in kind —
the author still reads it and still decides.

## Block D — The gate

### §RK439 The heading inside the region is not a second address for it

Shio's ledger nests eight `### Block K follow-ups` sub-headings under their own `##
Block K` parent, and `declaring` counts every heading whose label matches whatever its
level, so each one is read as a second declaration of K. `lint` fires `block.repeated`
at all eight, every write through `place` refuses, and `ship` cannot file into the block
at all — two field captures from that project are this one refusal, hit twice.

Neither remedy the finding names fits the shape. `block drop` wants a region holding
nothing and these hold entries; `block merge` folds the sub-headings away, deleting an
organisation the author chose. The third road, renaming so only the `##` declares the
label, was measured there: 91 entries moved to `block.missing` and the rename was
reverted.

That measurement is the argument the rule is missing. RK391 refuses two headings that
are two addresses for one label — the state where a write cannot know which region it
files under. A heading *inside* another heading's subtree is not that state: its
position already says which region owns it, so the entries beneath it are the parent's
and the ambiguity never arises. The distinction is one `subtree_end` already draws, and
`declaring` is where both ends read it, so it is one expression and not a special case
per caller.

Open: whether a nested heading may name a *different* label than the one whose subtree
it sits in, which is a genuine second address and should stay refused.

## Block E — Adoption

## Block F — The plugin

### §RK443 The verdict that agrees with a run nobody made

RK440 gave the capture the annotation: a re-run that exited 2 never reached the verb, so
the output under it is evidence about the command and not about the symptom. The capture
says so in the report and on the reporting session's own stderr.

`replay` is the other end and does not. Its verdict is the recorded exit code turning up
again, and a usage refusal satisfies that by construction — the same argv earns the same
refusal every time. So the command a maintainer runs to decide whether a field report is
still live answers `still reproduces` about a run that proved nothing, and the corpus
gate agrees. The annotation reaches the reader who took the capture and not the one who
triages it.

Nothing here is a new fact to record. Every capture already carries `exit`, so the shape
is derivable at replay time from what the reports already on disk hold — including the
two Shio filed before RK440 existed, which is the whole population this is about.

Open is where the answer belongs. `Replay` already holds two reasons not to trust a
verdict — `unstaged` and `drifted` — both stated beside the sentence rather than folded
into `reproduces`, because a boolean meaning three things is one nobody can gate on.
Whether the corpus gate should refuse such an entry is a separate judgement.

### §RK444 The only unconditional message points at the wrong engine

RK82 gave the session its resident line and decided on purpose that it would not repeat
the write path, a rule in two places being two places that can disagree. That holds.
What it did not separate is the rule from the route: the notice already publishes one —
`invocation()` — for the read verbs it names, on projects where `install` wired
`.mcp.json` and pre-approved the server. So the only message every adopting session
receives points at the shell on exactly the projects that have the tools.

The consequence is the shape of the door. The deny is already right, listing this
session's tools first and the shell second, under the prefix RK333 taught it to read —
but it fires only on a hand-edit. The agent that behaves, never touching the file and
reaching for a command instead, is the one that never sees the list. The skill carries
the same instruction and loads on a trigger, one sentence among two hundred and fifty.

What changes is one clause: where the tools are served the route named is the served
prefix, and where they are not it stays the invocation. `served` is already a field here
and already carries the `mcp__plugin_<plugin>_roadkeep__` form, so nothing new is read.
The write path stays the skill's — this states which engine answers, which is the same
kind of fact as which files are governed.
