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

### §RK368 The correction a non-goal has no door for

RK367 changed one clause of a non-goal's reason and had to drop the bullet and write it
again, that being the only door. The lead is the address and `non-goal add` inserts
after the last one there, so a constraint that sat fifth of eight now sits eighth: a
reviewer reads a deletion and an addition where a word moved, and the order a reader
takes for the shape of the list changed for a reason no commit is about.

The ledger settled this one layer up. `record amend` exists so that a correction is not
a move — never drop-and-re-add, which shows a reviewer a deletion where a word changed —
and `section amend` is the same door for a design that would otherwise be write-once
until it shipped. The non-goal list is the third bullet grammar this tool owns and the
one that never got one.

The shape the other two settle: `non-goal amend <lead> --why …`, rewriting the reason in
place, filled to the same width, the bullet's position untouched. Not the lead, which is
the address — `drop` plus `add` is right there, and is what the skill already says a
changed lead takes. Which leaves whether that asymmetry needs stating in a refusal, or
follows from the argument closely enough to cost nothing.

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK376 The zero one shape further out than the counters reach

A fourteen-line `README.md` of ordinary prose and a roadmap holding one heading and no
tasks both report `0 line(s), 0 conform, 0 would change`. That is RK98's rule at the far
end of itself: `tabular` and `listed` were built so a backlog in a shape this format
cannot read stops answering the number an empty file answers, and a file that is not a
backlog in any shape walks past both of them.

The path in is a typo or a guess — `adopt README.md`, `adopt docs/ROADMAP` corrected to
the wrong sibling — and the reading is the most reassuring one the report can give: a
corpus already conforming, nothing to change, adopt away. It is the answer an estimate
exists to not give, arriving on the run where the caller is least able to check it.

The fact is already in hand and never stated. The estimate knows how many lines the file
has and how many of them it read in any shape at all — as an entry, a reject, a table
row, a plain bullet, a heading. Zero of everything against a file with bulk is a
different answer from zero against a file with none, and only the second means what the
headline currently says.

What it must not become is a judgement about whether the file *is* a backlog. Counting
what was read against what is there is a measurement; deciding somebody pointed at the
wrong file is the tool having an opinion (L4).

## Block F — The plugin

### §RK366 A shipped text whose wrap nothing holds

Measured on the file as it ships: 299 non-blank body lines, 223 of them (74%) between 85
and 96 characters, 24 over 110, the widest 283 — and six orphans under 30 mid-paragraph
(`not on PATH.`, `refusals, with`, `silence). On a`). One pattern produced all of it:
text appended to a line rather than the paragraph re-wrapped, which leaves the insert's
tail short and the line it landed on long.

Nothing renders differently and nothing costs more tokens, so the cost is **review**: a
diff of a 283-character line is a whole-paragraph diff, in the file every adopting
project loads on the turns that touch a governed file. A change somebody skimmed here is
a rule every agent reads.

The decision is which of three, and the third is legitimate. A width in `roadkeep.toml`
with a `lint` finding makes it configuration rather than convention (L6), and puts this
tool a step from a Markdown formatter it has no reason to be. A `--fix` repair is worse:
re-wrapping a paragraph is rewriting somebody's line, and only the *derived* is repaired
(RK16). Or nothing is held, the file is re-wrapped once by hand, and the cost stays with
the reader who has the diff.

What would decide it is whether an edit here was ever actually mis-reviewed, which `git
log -p` on this file can answer and this section cannot.
