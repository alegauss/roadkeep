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

### §RK1435 The refusal is where a preventive verb is discoverable

A session used this tool for a whole day and learned its verbs almost entirely from
refusals. That is a biased sample: a refusal teaches the verb whose ABSENCE caused a
visible failure, and teaches nothing about a verb whose whole purpose is that the
failure never happens.

TWENTY REFUSALS TAUGHT NOTHING. `section add` rejected a body twenty times with an
excellent diagnosis - the word count, the limit, the overage, the per-paragraph
breakdown, and the judgement that a section this long is two sections. It never said
that `budget --body-file` measures the same draft and refuses without writing. The
session found `budget` on its last day, from `--help`, after paying twenty round trips
for it.

THE PATTERN ALREADY EXISTS AND WORKS. A successful `add` prints "or pass `--section
"<its title>"` to `add` next time: both halves in one transaction, under the same
limits". That sentence taught the same session something it then used. The teaching line
is already the house style; it is applied on one path and not the other.

WHAT WOULD ANSWER IT is a line on the refusals whose cause a read-only verb can predict:
body.too-long, why.too-long, symptom.too-long and their neighbours naming `budget`. One
sentence, on the path a caller is already reading because their write just failed.

The general form is worth stating once: where a refusal has a preventive verb, the
refusal is where that verb is discoverable, and nowhere else is as reliable.

### §RK1436 The absence of a flag read as a design statement

A line's symptom turned out to be false - it claimed a file was the last caller of
something, and a linker showed it was not. The session ran `amend --help`, saw `--why`,
`--dep` and `--requires`, and concluded the symptom was the line's address and could not
be corrected.

IT THEN WROTE THAT CONCLUSION DOWN. A rationale section acquired a paragraph explaining
that a symptom is an address, that amend cannot reach it, and that the correction
therefore belongs in the why. All of it reasonable, all of it wrong: `restate` exists,
its summary is "correct one open line's symptom, keeping its id", and running it printed
exactly the right thing - "kept the id, the deps and the section: the work never
changed" and "claim: the premise this line asserted turned out to be false".

THE ABSENCE OF A FLAG IS READ AS A DESIGN STATEMENT, and here it genuinely is one - the
symptom is not amend's to change, and that is correct. What is missing is the other half
of the sentence. A usage listing the fields a verb owns says nothing about where the
others live, and a caller who respects the boundary infers the field is fixed.

WHAT WOULD ANSWER IT is naming the owner where the boundary is drawn: `amend` mentioning
`restate` for a symptom, and the same wherever a verb deliberately declines a field
another verb holds. One clause, on the surface the caller is already reading.

## Block C — Query

### §RK1439 The line seven other tasks were filed against

Observed in the pportal port, on PP33 - delete curl and json-c from the C core. It has
been the answer to `pick` for many sessions running, and no session has worked it. What
each one did instead is in the ledger: PP544, PP563, PP564, PP565, PP566, PP573 and
PP584 all say "PP33" in their own sentences, all shipped, and PP33 is still open. Seven
children, one parent, and `pick` offered the parent every time.

RK1297 answered the neighbouring case. A line needing a console or a runner reads as
ready, so `[requirements]` was declared and `pick` learned to skip it. This is the same
sentence with a different absence: nothing is missing, the line is simply larger than a
session, and the caller finds that out by reading its criteria and then filing a child.
The dep graph cannot say so, correctly - a child does not exist yet when the parent is
offered.

The evidence is already in the files. A shipped entry naming an open id is a fact `refs`
can see, so "seven entries against this line and it is still open" is a query and not a
new field. No verb asks it, so what would have told the eighth session what the previous
seven learned is spread over seven ledger sentences nobody reads in order.

Not a marker. `⏳` says a line is part-done and says nothing about who has been paying
for it.

## Block D — The gate

## Block E — Adoption

### §RK1438 The output an adopter actually reads

`install` prints what it wrote: the server, the guard, the skill, the workflow, each
marked written or unchanged, with the launcher's path substituted. It is an accurate
report of files. It says nothing about what those files now let a session do.

FOR AN AGENT THAT OUTPUT IS OFTEN THE FIRST CONTACT, and the first refusal is the
second. The skill is the third, arrives on a later turn, and is long enough that it is
skimmed - RK1424 measured it and RK1437 argues about its cadence. The two surfaces a
session reliably READS are the ones that say least about the tool's shape.

WHAT A FIRST CONTACT NEEDS IS SMALL. Which files are now the tool's and not to be
hand-edited; the handful of verbs a day actually uses - `brief` or `pick` to start,
`add` and `ship` to move, `lint` as the gate; and the two that answer without writing,
`budget` before a refusal and `show` instead of opening the file. Six lines, at the end
of a command an adopter runs once and reads.

IT IS ALSO WHERE `install --check` BELONGS IN A SENTENCE: the same output could say that
this is the command a CI job or a pre-commit hook runs to keep the copied skill in step,
which is a fact currently discoverable only from `--help`.

The suggestion is deliberately not more documentation. It is putting the smallest useful
part of it where somebody is already looking.

## Block F — The plugin

### §RK1437 A reference loaded as an orientation

The skill `install` writes names all 44 verbs. Coverage is not the problem: a session
had every one of them in context from its first turn, used about fourteen, and missed
the two that would have saved it most - `budget`, which measures a draft without writing
it, and `restate`, which corrects a symptom.

THE TOOL ALREADY MEASURES WHY. `cost --skill` reports 65832 code units on every turn
that loads it, and 42791 of those in one section. That is a reference being loaded as an
orientation, on every turn, and a reference of that density is skimmed. What the session
retained instead came from refusals - which teaches only the verbs whose absence fails
loudly, and never the ones whose whole purpose is that nothing fails.

THE VERBS IT NEVER FOUND ARE THE READS. Of the fourteen it used, nearly all were writes
or gates. `budget`, `cost`, `explain`, `show`, `audit`, `unclosed`, `gaps` and `writes`
went untouched for a day - and those are the ones that reduce friction rather than
record it.

WHAT WOULD ANSWER IT is layering rather than cutting, and the argument is only about
cadence: an orientation small enough to be read on first contact - what the tool owns,
the verbs of the daily loop, and where the rest is - with the reference reachable when a
turn needs it.

Whether that is two files, a section order, or something the plugin loads on demand is
this project's call and not an adopter's.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
