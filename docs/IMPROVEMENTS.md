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

## Block E — Adoption

## Block F — The plugin

### §RK1368 The note that fires for the safe direction only

Observed while shipping RK1367. `govern tools.session 63900` was called over MCP and
answered `reading.worst: 63594` — the surface as it stood two verbs earlier. The live
reading was 63,856, that session having added a served flag and rewritten a tool
description. Nothing in the answer said so.

The apparatus for this exists and is written entirely for refusals: the note opens
"about this process and not about the refusal above", the payload is built as an error,
and RK267 narrowed the module list so a refusal names only what decided it. Every one of
those is right about a refusal.

A write is the other direction and the worse one. A refusal read against stale code
costs a re-run; a number *accepted* against stale code is committed — and here
`govern`'s own guard, that a limit the corpus already breaks is refused, was applied to
a corpus that had moved, so re-declaring the old ceiling would have passed the verb and
been refused by `lint` on the very next call.

RK267 is the constraint on the fix rather than an objection to it: the note may not hand
the relevance question back. What decided a write is the same question already answered
for a refusal, so the reach is the modules that decided it and the shape is the sentence
that exists.

Falsified when a served write answers with a figure the code on disk would not produce
and says nothing.

### §RK1369 Withheld on purpose and withheld by omission read alike

RK1367 added `--instead` to `govern` and it did not reach the served tool. Nothing said
so: `lint` was clean and the suite passed, and the absence surfaced only because `cost
--tools govern` was run to price a description and its field list had five rows where
the parser has six.

The tuple in `serving.py` is right to be hand-kept. `--fix`, `--prune` and `--porcelain`
are withheld on arguments written beside them, and a rule that served every flag would
put `lint --fix` on the surface RK16 keeps it off. So the finding is not that the list
is manual — it is that the two halves are never read against each other, so a flag
withheld by decision and one withheld because nobody was looking are one state to a
reader.

What closes it is a read and not a gate, for that same reason: which flags a served
verb's parser carries that no `Tool` names, per verb, with the argument's own `help`
beside it — then "was this deliberate?" is answered by a sentence somebody wrote, or by
its absence.

A crude reflection over the parsers counts eighteen such flags across nine verbs and
over-counts the conditional ones. That is itself the argument: the number nobody can
state without writing a script is the number this read exists to give.

Falsified when a served verb's parser carries a flag no read here names.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
