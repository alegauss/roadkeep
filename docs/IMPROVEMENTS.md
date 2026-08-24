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

### §RK1332 The address said twice on one line

Measured on this repository's own ledger: 48 of 48 entries carrying a design clause
spell `design §RK<n>` where `<n>` is the id the line already opens with in bold. Under
`ref_scheme = "id"` the anchor and the id are one string, so 8 of those characters are
the tool writing an address it has just written.

382 characters across the corpus is not the argument; the sentence they are spent in is.
RK1330 measured that one 200-character sentence carries an outcome, a supersession note
and a recording clause, that the note is the half which gives way, and that at the
outcome's own aim it never fits. The ship closing it had 23 characters left over, and 8
is a third of them.

Under an outline the anchor is not the id - a section address names something the line
does not - so the clause has to keep it there. The saving is conditional on the scheme,
which is where the configuration already decides every other spelling.

Falsified if a reader loses the address under a scheme where it differs from the id,
which would make this a rendering rule that cannot be made conditional.

### §RK1331 The number that cannot be retried at

The refusal names a field and a number, and the number is measured on something else.
`RecordingCrowded` computes the room as the limit less what the recording clause spends,
which leaves what the *composition before it* may take - outcome plus supersession note
plus the brackets around them. It then reports that figure as what "the outcome" has.

Measured on the ship that closed RK1330: the message offered 126, a `--why` of exactly
126 composes 239 against a limit of 182, and the refusal prints 126 again. The advice is
a fixed point that never converges, which is worse than no number: an author retrying at
the figure printed has no reason to doubt it, and the second refusal looks like the tool
ignoring the edit rather than like the figure meaning something other than it said.

Either the number is attributed to the composition it actually measures, or it is
reduced to what the named field may take. The second is what the message promises and
what a caller can act on without arithmetic.

Falsified if the pair can reach this class with no note in it, in which case the outcome
really is the whole of what was measured and only the wording is at fault.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
