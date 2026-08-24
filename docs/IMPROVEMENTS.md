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

### §RK1320 RK1320

Measured on this repository, one call. `brief RK1311 --json` answers
`budget.fields.symptom.drafted = false` and `shipping.changed.fields.symptom.drafted =
true` about the same 93 characters, read off the same roadmap line, in the same payload.

`Share.drafted` says whether `taken` is prose the caller handed over to be measured
rather than prose the file holds (RK1190). It changes no arithmetic and every word of
the answer: *93 drafted* about a symptom nobody typed is a report about the wrong file,
and the caller cannot tell the two apart from the number.

`budget_of` derives it as `not open_line and bool(task.symptom)`, with the reasoning
that a symptom on a line the roadmap does not hold came from the caller - which is true
of the pre-`add` read the flag was written for. It is false of every shape added since:
`brief`'s `shipping` and `deciding` price a task read off the file under the ledger's
grammar, and RK1305's retirement does the same. `open_line` was a proxy for *the caller
composed this* and stopped being one the moment a second reason to pass False existed.

The fix is to say it rather than derive it: the caller that composed the prose is the
caller that knows, and `budget_of` already takes a `why` draft on exactly that argument.

Falsified if some caller passes `open_line=False` about prose it did compose and has no
other way to say so.

## Block D — The gate

### §RK1318 The address the gate never re-asks

Observed on a fresh tree, 2026-08-23. Two states reach it: `block drop` withdrawing a
label whose list stays (RK1316), and `renumber` spending the id a list is addressed to
(RK1317). `lint` calls both trees clean.

`_criteria` checks what a schema can check — shape, the two lengths, a lead stated twice
inside one list. `criteria._addressed` validates the address at the write, which is L1
and right; nothing re-asks once the address has stopped existing, and the write path
cannot, the block having been there when the bullet was written.

So the finding is at the heading and its subject is the address, one per region and not
per bullet: what is orphaned is the list. This stays the backstop the two writes above
make rare and never impossible — a hand edit, a textual merge, a tree governed before
either of them shipped.

The door is `criterion drop <lead>`, bare. The addressed form is refused, the address
being exactly what stopped existing, so a remedy spelling `--block` would name a command
that cannot run — which RK16 forbids. And an orphan the last drop leaves empty has no
door at all: the heading survives its bullets by design (RK1265), so `--fix` is what
takes that one, a heading addressed to nothing with nothing under it being derived dead
as a shipped task's queue entry is.

### §RK1322 RK1322

Measured on this repository, 2026-08-23: 47 of 148 Python files are CRLF in the working
copy and 101 are LF. `.gitattributes` pins what git stores (RK1132) and
`test_no_file_mixes_the_two_line_terminators` refuses a file holding both - so each file
is internally consistent and the tree is not.

The cost is paid by anything that appends. Three times in one session a heredoc added LF
to a CRLF test file and the invariant went red; each time the fix was rewriting the
whole file in the terminator it already had, which is a read nobody can make from the
file's name. The skill warns about heredocs into source (RK1091) for a different reason,
and this failure wears the same clothes.

git says so too, once per commit: `CRLF will be replaced by LF the next time Git touches
it`. A warning on every commit that touches a third of the source is one a reader learns
to skip, which is the state RK16 keeps findings out of.

Three shapes. A gate finding per file whose working copy disagrees with what
`.gitattributes` stores, which is the reading git already does and nobody surfaces; a
normalising pass in `--fix`, which is derived and therefore its kind of repair; or a
read that answers which terminator a path has, so an append asks instead of guessing.

Falsified if `core.autocrlf` explains the split, which would make it a checkout setting
and not a fact about the tree.

### §RK1323 RK1323

`agents.md` states it as a law: this repository's own `docs/` is the conformance
fixture, and `roadkeep lint` must pass on it, because the format is proven by the
artefact and not asserted in a README. A limit these lines cannot express is the wrong
limit rather than a set of wrong lines.

`[criteria]` is outside that proof. `criterion list` here answers *no [criteria] in this
project's roadkeep.toml, so what finishes a block is ungoverned*, so every `brief` this
project makes prints an empty `done_when` and RK1300's event - the criteria arriving
with the word `finished` - has never fired on the corpus it was built against. Two
blocks closed in this session and neither carried a list to print.

RK1313 sharpened it: `init` now writes the table empty into every new project, so the
shape a fresh adopter starts from is one the tool's own fixture does not have. That is
the asymmetry, and it is the one RK66 argued the other way round - a schema applied to
prose nobody wrote to it reports on adoption.

The work is not the declaration. It is writing what would finish each open block, which
is a judgement about the plan and not a config edit, and the reason this is a line
rather than a commit.

Falsified if the criteria a block would carry are already stated somewhere the gate
reads, which would make this a duplication rather than a gap.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1321 RK1321

Measured this session, twice. RK1305 added a seventh subject and `budget` reached 2,744
against a per-tool ceiling of 2,600 - overtaking `ship` at 2,466, the tool that number
was calibrated against. RK1310 then added a 65th verb and the whole surface reached
64,190 against 63,500. Both ceilings were re-argued rather than met, and both arguments
were about the same tool.

The ceiling is doing its job: `roadkeep.toml` says it is set close enough that a
description growing by a paragraph is a finding rather than a rounding, and it found
this. What it found is not a description that grew. `budget` answers about a line, a
section body, a non-goal, an every-turn file, the tool list, a session, a brief and a
retirement - eight questions under one name, where every other served tool answers one.
A per-tool limit is refused by the tool whose description somebody just edited (RK1059),
and this one is refused by whichever subject was added last, which is the property that
argument rejected for a total.

There is a seam. Four of the subjects price prose a write is measured against; three
price what a surface costs a session. `budget --tools`, `--session` and `--brief` share
a reader and share nothing with `--block`.

Falsified if splitting leaves either half still the largest tool, which would make this
a name and not a bundle.
