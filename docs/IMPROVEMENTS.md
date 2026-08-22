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

### §RK1302 The door a partial leaves unnamed

Measured on quickshell. QS3 delivered a corpus and a harness; its remainder was two
consumers needing a parser and a renderer, neither written. `ship --part` recorded that
and left the line at ⏳, which is right. The next `pick` handed QS3 straight back, from
the in-progress tier and ahead of everything, and would on every call until two other
tasks ship.

The remedy is one command, `amend <id> --dep <the work the remainder waits on>`, and
after it `pick` moved on. Nothing said so. The partial's answer reports the entry, the
marker and the remainder, and stops exactly where the caller needs the next sentence:
what the line is now waiting for.

That is worth closing here rather than in a habit: this is the one ship that
deliberately leaves work open, and the state it leaves is the one the ranking trusts
most. A caller who does not know the remedy re-picks the same line, works around it with
an id typed by hand, and the file keeps saying in progress while nothing is.

Two shapes fit. The narrow one: `--part` names the door in its answer, the way every
other refusal here names a complete argv. The wider one: `--part --dep <id>` amends the
group in the same transaction, since the moment the remainder is described is the moment
its blockers are known.

Falsified when a `--part` whose remainder waits on unshipped work leaves the caller to
discover `amend --dep` by being handed the line twice.

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

### §RK1301 The count is the answer, and the roster is the file again

Measured on quickshell, a fresh eighty-one-line backlog: `brief` with no id chose the
first task and answered an `unblocks` object carrying the count, the total, and then
seventy-nine ids spelled out in one list. `claim` returns the same payload, so a session
that briefs a line and then takes it pays for that roster twice before it has opened a
file.

RK13 gave the walk its count because the count is the information: it ranks a line
against every other one, and a caller reads it once. The roster answers a different
question, `deps` already answers that one, and the case where the list is longest is
exactly the case where it is least informative - a task early in the graph unblocks
essentially the whole backlog, so the ids restate the file the read exists to replace.

RK29 bounded this answer to fit a tool result and RK1286 gave it a ceiling; this field
honours neither, spending in proportion to the backlog rather than to the task. The
non-goals list in the same payload shows the fix - it elides past a cap and reports
`non_goals_elided` beside what it kept - so the same treatment leaves the count whole,
keeps a handful of ids, and sends a caller who wants the rest to `deps`.

Falsified when a brief on the earliest line of an eighty-line backlog still spells more
ids than the cap, or when the count stops being derived from the whole walk.

### §RK1303 The three budget blocks, and the two that say the same thing

A `brief` answers with three budget blocks: `budget`, the line as it stands; `shipping`,
the line as the ledger would hold it; and `deciding`, the line as a decision record
would. Measured on quickshell's QS8, the three came to some sixty per cent of the
payload, and `shipping` and `deciding` were byte-identical — same fields, same limits,
same numbers.

That identity is not a coincidence of one line. Both are the same closed line: no deps,
no pointer, the shipped marker. They differ only where a project's `[limits]` gives the
decisions role its own numbers, which is a table most projects never write. So on every
project that does not, the second copy states nothing the first did not.

The read exists to replace opening the file, which makes it the read a tool result
truncates first — `[reads] brief` and `budget --brief` both already exist because that
is known. What they measure is the total; what this line is about is the share of that
total which is a repeat.

Two doors, and which is right is the design: emit `deciding` only where it differs from
`shipping`, naming that it was elided; or fold the three into one block with the fields
that vary marked per stage. The first is smaller and keeps the shape callers already
parse.

Falsified if the two blocks diverge on a project with no `[limits]` table per role,
which would make the repeat a coincidence of one corpus rather than a rule.

### §RK1304 What the priority is waiting on

Observed over four consecutive sessions on a port whose roadmap declares Priority as
Block H then Block I. Every task in both blocks is blocked, so brief falls through to
the lowest ready id and reports: picked - lowest ready id; the roadmap's queue names
nothing ready.

That sentence is true and it stops one step short. Block H holds one line, blocked on a
single task in another block. Nothing in the answer says so. The caller who wants to
work on the priority has to open the roadmap, read the priority list, find the block's
lines, read their deps, and look each one up - which is the reading brief exists to
replace, done by hand, at the exact moment the answer was least obvious.

The data is already there. brief computes unblocks for the task it picked, so the graph
is walked in that direction; what is missing is the inverse question asked of the
priority blocks rather than of the pick. Something on the order of: priority Block H is
1 line, blocked; RK-nnn would release it - alongside the pick rather than instead of it,
because the pick may still be the right call when the blocker is expensive.

The case that makes it worth having is the one where the blocker is cheap and nobody
looked. Four sessions of falling through to the same partial is what prompted this.

### §RK1305 Budget answers for a retirement too

Measured while retiring a task in an adopting project. The reason was refused three
times in a row - 250 characters, then 212, then 205, against a limit of 200 - and each
rewrite cut a clause out of the one field whose whole job is to carry evidence. The
sentence that finally landed says less about the measurement that settled the decision
than the first draft did.

Each refusal did its job: it named the limit and how much to delete. What none of them
could do is what `budget` already does before a line is added or a completion written -
answer, before a word exists, how much room this particular retirement has. A
retirement's reason shares the rendered line with the symptom it is retiring, and a long
symptom leaves a short reason, so the usable maximum is not the published one and cannot
be guessed from it.

The skill asks a retirement to open with the decision, give the evidence in numbers
where there are numbers, and say where the conclusion now lives. That is three clauses,
drafted against a budget the author cannot ask for. Extending `budget` to answer for a
retirement costs one more shape of the same reading and removes the loop that trims
evidence away.

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
