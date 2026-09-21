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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

### §RK1690 The verdict one person leaves on an entry

`ship --checked <lead>` (RK1460) is the shipping session saying it verified a criterion
it declared. That is not a person using the thing, and nothing else in the ledger is
either: an entry records what landed and is silent about whether anybody ever looked.

**One continuation line, in the grammar that is already there.** `carried` writes
`checked **<lead>** <why>` and `carries` recognises it. This adds one derived word
beside it, indented by two exactly as that one is: `validated **worked** Reopened the
task three times and the answer was there at once.`

The address is the verdict, out of a closed set — `worked`, `failed`, `nothing to see` —
refused at input (L1). The sentence is the caller's own; nothing here composes prose
(L4). The third verdict keeps the list honest: a refactor has nothing a person can open,
and saying so is somebody's act, not a heuristic this tool would guess.

**No date and no author.** `attesting` already argues it for claims — the identity
behind a write lives outside the repository, and the commit is where it belongs — and
`weight` derives from the commit rather than storing one. `origin <id>` resolves it.

**The last verdict wins and the line is rewritten** (RK7). Nothing a failure found is
lost by that: it is a line of its own.

Done when an entry carries a verdict, a second `validate` replaces it rather than adding
one, and a token outside the set is refused.

### §RK1691 The list of what nobody has looked at

A verdict nobody can enumerate is a verdict nobody writes. `unvalidated` is the read
that makes the state actionable, and it is `unclosed`'s mirror in shape and in
temperament: a report and never a gate, since whether work needs a person is a judgement
this tool has no model for.

**What it answers.** Every ledger entry at or after where validation starts that carries
no `validated` line, in block order, with the id, the symptom and the commit `origin`
resolves for it. `--block` narrows it and `--json` is what a client reads.

**And `stats` carries the two counts**, validated and not, because a caller drawing
twenty backlogs wants the figure without the list — the same reason that verb already
carries open and recorded.

Not a lint finding, and the distinction matters more here than it looks. An unvalidated
entry is the ordinary state of work that shipped an hour ago; a gate that fired on every
ship is a gate somebody switches off, and it would take the honest findings with it.

Done when a fixture ledger holding one verdict and two without answers with the two, and
the counts agree with the list.

### §RK1692 Where looking starts

This repository has 1163 shipped entries and roadkeep-gui 283. A project that adopts
validation and finds its whole history in the list has been handed a backlog nobody will
start — the adoption gate that gets bypassed instead of adopted, which is the argument
`[criteria]` and `[non_goals]` are both opt-in for.

**Declared means governed.** A `[validation]` table turns the state on, and its `from`
key names the first ledger entry that enters the list: everything before it is history
and answers nothing. A project that declares the table and no `from` starts at its next
ship, which is the reading that needs no id chosen.

A ledger id and not a date. The ledger is ordered by the ships that wrote it, a date
would be a second ordering to keep true, and RK1690 already refuses to store one.
Refused on an id the ledger does not carry, as every other declared address is.

Nothing migrates. An entry before the start is not *validated* and not *unvalidated* —
it is outside the question, which is the third state `attesting` needed for the same
reason.

Done when a project with no table has no list, one declaring `from` lists only what
followed it, and an id the ledger lacks is refused at config read.

### §RK1693 The recogniser and the gate

RK1507 put `carries` beside `carried` because a writer and a reader of one shape drift
silently and in the direction that costs. Widening the writer without the reader is that
failure exactly: an entry holding a verdict would read as hand-wrapped to
`_derived_tail`, `record amend` would go back to demanding `--lines`, and nothing would
be red.

**So the pair moves together**, and the round-trip test that already sends a composed
line back through `carries` gains the second word.

**Three findings**, each the format being wrong rather than the work being unfinished:

- `validation.verdict` — a token outside the declared set.
- `validation.repeated` — two verdicts on one entry, which is RK1690's rewrite having failed.
- `validation.open` — a verdict under a line still open in the roadmap, which nothing has shipped.

None of them is *unvalidated*. That is a state, and RK1691 says why it is not a
violation.

Done when a hand-written verdict of each shape is reported with its code, and an entry
holding a legal one round-trips through `record amend` with no `--lines`.

### §RK1694 What a failure is owed

A validation that failed found a defect, and this tool has exactly one thing for a
defect: an open line. Leaving the verdict and the line as two commands is how the second
one gets forgotten, which is the argument `ship`'s three edits are one transaction for.

**`--files <symptom>` writes both**, as `--decides` writes a decision into the fourth
file: the verdict lands on the ledger entry, the open line lands under the same block,
and the caller's `--saw` sentence becomes its why. Nothing composes prose — the symptom
is the caller's too.

**Only with `failed`.** A `worked` that filed a line would be filing work nobody found,
and a `nothing to see` has nothing to report. Refused on either, naming the verdict that
takes it.

This is also what makes RK1690's rewrite-in-place safe. A verdict is overwritten by the
next one, but a failure that filed a line left a record no rewrite touches, and that
line ships into the ledger as its own entry.

Done when a failed validation with `--files` leaves the verdict and a new open line
under the same block, or leaves neither, and the other two verdicts refuse the flag.
