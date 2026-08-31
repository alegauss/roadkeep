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

### §RK1447 The half of install's answer only a terminal gets

RK1438 gave the write report five closing lines: which files stopped being
hand-editable, the verbs a day uses, the gate, the two reads that save a refusal, and
the check CI runs. They go to stdout. `Plan.payload` carries the surfaces, their states,
the launcher, the debt and the blocked parents — and nothing about what any of it
enables.

THE CALL WAS DELIBERATE AND MADE WITHOUT THE RULE IN VIEW. The reasoning was that a
machine reading a payload has the skill. Block C's criterion argues the other way and is
the older claim: both registers come off one record, *because a printer and a payload
builder agreeing by hand is how an agent comes to be told less than the person at the
terminal*.

THE CASE IS NOT HYPOTHETICAL. The caller most likely to run `install --json` is the one
wiring a project from a script or a session, which is exactly the reader RK1438 was
written for — and it is handed the file list and told nothing. The skill it supposedly
has is the surface the install just wired, on a turn that has not loaded it.

WHAT WOULD ANSWER IT is the same rows as a key, composed once. Whether that key is the
rendered lines or the facts behind them is the open half: rendered strings are what the
two registers share elsewhere, and a structured answer is what a script would rather
branch on.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1448 Six tests about one rule, held against every rule

RK1440 gave the gate one more note — a wired project whose engine is a modified checkout
— and nineteen tests went red in one run. None of them was about engines. Six read
`(note,) = report.notes` or `report.notes == ()` while meaning *exactly one
`deps.collective` note*, one read `report.notes[0]`, and the rest were the same shape
one file over.

THE ASSERTION IS WRONG IN BOTH DIRECTIONS. It fails on a note the test does not care
about, which is what happened; and it passes while a note the test *should* have seen is
absent, because a list of one is a list of one whatever is in it. Neither failure names
the rule under test, so the repair is mechanical and the reader learns nothing.

IT IS ALSO ENVIRONMENT-DEPENDENT NOW. That note fires on a checkout with uncommitted
work, so the suite's verdict began to depend on whether the tree was dirty while it ran
— a test whose result is a fact about the developer's working directory.

WHAT WOULD ANSWER IT is the join RK1441 established one subject over: notes and findings
are reported by **code**, the codes are enumerable from `remedying`, and an assertion
over the whole list of either is a claim about every rule the gate has. A sweep refusing
an unfiltered unpack would have caught all seven the first time, and costs nothing on
the ones that filter.

## Block I — The documentation area (what an adopter reads before there is a session to ask)
