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

### §RK1545 The axis measured on the wrong corpus

RK1510's first reading over this repository: 110 of 229 Block D comparables filed
something behind them, at a median of 0 and a p90 of 2 — and the span is 1 commit at
every percentile up to p90. Every recent entry reads `filed 1 over 1`.

That last figure is not a property of the work but of the loop. A session that ships a
task and immediately files the improvement it turned up produces one filing one commit
later, every time, whether the task decomposed into real follow-on work or somebody had
a thought. The distinction RK1510 exists to make is flattened by a cadence.

The span carries the same problem in the unit. Commits over the two governed files is a
proxy for elapsed work, and it is a good one where commits are work; where a session
commits a docs line per idea it is a count of the loop's own steps. The port RK1510 was
measured in went from id 66 to 727 over three weeks, and *that* is the shape the reading
was built for.

So the axis is right and this corpus is the wrong one to read it on — which is worth
saying before somebody reads a median of 0 here as a fact about how roadkeep is worked.
The honest next step is the reading over Shio or Turing, where the cadence is not one
commit per thought, and `tests/corpora.py` already pins both.

### §RK1546 The criterion with no origin

RK1511's fold names the destination in the ledger — `superseded by RK7: <reason>` — and
writes the criterion under RK7. The criterion says nothing about where it came from.

That is the half of the join the design explicitly asked for and this did not build:
*the criterion cites no origin*. After the fold, RK7's list carries a claim whose id is
spent, and the only route back is `origin` over history or reading the ledger for a
retirement naming RK7. A reader of RK7's brief sees a definition of done with one bullet
that was somebody else's line and no way to tell.

It is not a missing field so much as a decided one. A criterion's grammar is a lead and
a reason (RK1265), and an id in either would be a reference outliving the work —
RK1457's argument against putting an answer in a non-goal. So the options are a third
element on that bullet, changing a grammar two verbs write, or nothing, the ledger
holding the fact.

What decides it is who asks. A reader of RK7 is holding a brief, and `brief` prints the
criteria list — so the cheapest shape may be neither: the *brief* could name the folded
ids, joining the ledger it already reads to the list it already prints, and the file
stays as it is. That keeps L2's store and puts the answer where somebody is asking.

### §RK1547 The reason with no expiry

RK1512 asked for the count **and the oldest reason** and shipped the count. The store
cannot say which line is oldest: a deferral carries a reason and no date, and the file's
order is by block. Age is derivable — `added_ids` over the deferred role walks
`--reverse` — but `pick` runs every loop iteration, and a git call there is a cost the
count does not have.

That is the second half RK1512 called the audit. A deferral is the one governed line
with a reason and no expiry: nothing goes red for it, prose not going red. The measured
case is exact — one of seven deferrals in a live port cited a premise twenty files under
the tree had already falsified, and the pause outlived it by weeks.

What can be said cheaply is age, and the reason beside it is what makes age actionable.
So the read belongs where a git call is already paid: `weight` takes two and `unclosed`
takes two, and neither is on the loop's path. A `resume --stale` would put the oldest
pauses in front of a reader once, rather than a number in front of them every time.

What it must not become is a rule. How long a pause may stand is a judgement about work
(L4), the same one `[claims] held` refuses to make for a claim — so the answer is an
order and never a verdict, which is what `weight` already is for a different question.

### §RK1548 The placeholder that cannot survive its own quotes

RK1513's door read `--lead <what is true when it is>`, and the test that parses it
refused the call: `shlex.split` takes `<what` as the value and hands argparse four stray
words. The fix is a quote, and the rule is one this tree already breaks three more times
— `ship <id> --part <what landed>`, `section move <a> --to <free anchor>`, `anchors
--family <one of them>` — in a tool whose claim is that the door it names is the door.

Nothing catches it. `composing._BLANKS` accepts both spellings, `<x>` and `"<x>"`, and
only the quoted one survives the split — so the unquoted placeholder never matches, and
`filled`'s loud `<unfilled --flag>` branch, which exists so an argument is never quietly
dropped, does not see it either. It arrives as literal argv and the command silently
becomes a different one.

The check does not need the site to be reached, which is what makes it worth having
beside RK1498: a span holding a placeholder with a space in it is wrong from the string
alone, so one pass covers the thirty-odd sites no test runs as well as the ones it does.
Three of the four here were found by grep after the fourth was found by a hand-written
test.

What it must not do is police prose. `--part <what landed>` outside backticks is a flag
being named in a sentence, and is correct; the rule binds a backticked span that starts
with the invocation, the boundary `commands` already draws.

### §RK1556 The seventh key, and the sentence for a project without it

RK1519 gave `[markers]` a key for the marker a claim is taken at. The partial marker has
none, and `ship --part` on a project whose open set spells no ⏳ writes the line's
existing marker instead — deliberately, and in silence. Measured on the project the
claim defect was found on: the ship exits 0, prints the ledger entry, and leaves the
roadmap line as it was.

The fallback is right; a command that invented a marker would write a line its own gate
refuses. What is wrong is that it is unreported and closes a door. A partial the file
cannot mark is a state nobody sees, `pick` never offers the remainder as one, and the
later `--part` correcting a qualifier refuses with `NoQualifier` — it asks whether the
open line is at ⏳.

Two writes, and the second is smaller. A seventh key, `[markers] partial`, on
`working`'s terms exactly: a narrowing of `open`, refused where the open set does not
spell it, empty where a project declares neither. Then the sentence for a project that
declares neither — the shipment saying what it could not record, rather than reporting a
partial the file does not carry.

What decides whether the key is worth it is whether a partial is a *state* or a
*report*. If the ledger entry is the whole of it, the roadmap marker is decoration and
the sentence is the fix alone. `pick`'s tiers say otherwise: the marker is what makes a
remainder findable.

### §RK1558 The exemption one of two scans keeps

`test_configured`'s three literal scans skip what a caller is shown: `help`,
`description` and `metavar` are full of `e.g. RK7`, and the module says why — the parser
carrying them is built before any project is known, so nothing in a help string is
derivable and scanning them would produce an allow-list of forty strings.

RK1520's scan does not apply that exemption. It walks every f-string in the module,
including the ones inside an `add_argument(help=…)`, so a help string composing a
command round a package marker is a red there and invisible to the scan beside it.
Nothing is flagged today, which is why this is a question and not a defect: the two
readings differ and neither states that they do.

The case for keeping the difference is real. The exemption exists because a help string
cannot name *this* project's values, and a **command** in one is not that: it is
something the reader is told to run, and a marker inside it is wrong for the reason it
is wrong anywhere else. Under that reading the new scan is right and the inconsistency
is a sentence.

The case against is that a help string is the one place an example is legitimate, and
`status <id> 🛠` shown as an example of the syntax is not a claim about the reader's
vocabulary. Which of the two holds is a judgement about the text, so the answer is a
stated rule either way and never a scan that quietly has one.

### §RK1566 The corpus this measurement cannot exhibit

RK1527 measured the near window over both corpora and kept three, on a figure that is a
property of this repository's ratio rather than of the read: 167 delivered entries
against a block's nine open lines, so the open half takes one slot of thirty-three. On a
project whose backlog outnumbers its deliveries the same read measures the other way,
and nothing anywhere would say so.

That is the population the volunteered rows are *for*. An `add` on a mature ledger is
proposing work beside a long history; an `add` on a young one is proposing work beside a
backlog somebody filed last week, which is exactly the collision RK1495 added the second
corpus to catch — and it is the case this repository cannot exhibit.

The corpora are already pinned. `tests/corpora.py` holds Shio and Turing at a revision,
and Turing's roadmap is the shape wanted: a long backlog against a ledger that is mostly
one migration. So the measurement is available without inventing a project, which is the
condition every other bound here was set under.

What it would decide is not necessarily the number. Three may still be right for both,
or the honest answer may be that the window is a ratio — so many of each — which is a
shape `nearest` does not have and would need arguing for. Either way what is missing is
the second reading, and a bound set from one corpus is the thing RK1477 already had to
reopen once.

### §RK1567 The read the row says it is

The near rows an `add` prints are `delivered --near` volunteered — the code says so, and
RK1374 chose that verb's own two phrases for the row rather than invent a second
wording. Since RK1495 they are not the same read. `add` ranks over a block's deliveries
**and** its open lines; `delivered --near` ranks over the ledger alone, so a caller
running the read the row is a copy of gets a different answer from the one shown.

Nothing is wrong on either side. `add` was widened because two sessions filing one
defect within the hour could not see each other, and `delivered` is named for the ledger
— asking it about undelivered work is a verb answering outside its own subject. What is
wrong is that one of them is described as the other.

Three ways out, unequally cheap. Widen `--near` and accept that `delivered` answers
about open lines under one flag; leave the reads apart and stop calling the row that
verb's; or give the duplicate read a door of its own — the honest shape and the dearest,
since a verb whose subject is *a block's whole corpus* is what both callers want and
neither `delivered` nor `list` is it.

The measurement deciding it is small: how often the two answers differ across this
repository's blocks. If the open half rarely enters the volunteered rows — RK1527
measured one slot in thirty-three — the reads agree nearly always, and the second is the
cheapest honest answer.

### §RK1568 The entry that is there and filters nothing

RK1529 says when an `[history] incidental` entry names a file this tree does not hold.
The reason it gave was wider: a filter that stops matching makes `unclosed` louder with
nothing having changed in the report. An absent path is one way to stop matching. The
other is a path that is there and that no commit touches on its own, and that one is
still silent.

Same defect, same cost. `incidental` removes a commit only when every path it touched is
declared, so an entry naming a file always committed alongside real work filters nothing
— and reads, in `roadkeep.toml`, as a project that has accounted for its hooks. A
version bump that moved from one file to two is that state, and the tree holds both.

What makes the second half a different job is the cost. Existence is a `blob` this gate
already asks for; *matched anything* is a walk of the history, which `lint` does not pay
for and should not start paying for on every commit. The place where the walk is already
bought is `unclosed` itself — the report the entry shapes — and RK1512 settled that
shape of argument once: a reading belongs where a git call is paid, not on the loop's
path.

So the row belongs on `unclosed` rather than in the gate: *this many commits were set
aside, and these entries set aside none*. The report knows both halves already.

### §RK1573 The heading only the scaffold writes

`declare non_goals` opens the table that governs the list and names the write it gates:
`non-goal add --lead … --why …`. On a project past `init` that command refuses — *no
non-goals heading in ROADMAP.md: the heading declares the list, exactly as a block
heading declares a block* — and no verb writes that heading. `init` does, once, at
scaffold time.

So the door is unopenable on exactly the population RK1328 was filed for. That task
opened the table for projects past scaffolding, because it went in by hand and no verb
opened one; the same sentence is now true one level down, about the heading.

The symmetric fix is one this format made twice. `criterion add` writes its `## Done
when — Block X` heading where the block has none (RK427, RK1265), the list being opened
by the act of writing the first entry, and `priority add` does the same. Either
`declare` writes the heading with the table, or `non-goal add` opens it as its two
siblings do — the second being more consistent, since a project may have the table and
still be one write from the list.

What it must not do is guess where. A block heading has a place in the file and this one
does not: `init` writes it after the blocks, which is a convention and not a rule, and a
verb placing it anywhere else would move a section a reader knows the position of.

## Block D — The gate

### §RK1498 The doors nothing has ever run

RK1475 withdrew one offer that would refuse. The rule it broke — *a finding naming a
command that then refuses is worse* — is `removable`'s own docstring, held by the gate
for one finding, and now by the event for one door. Nothing holds it for the rest.

There are many. Every refusal in this tool ends with a door and several compose one from
a state they did not check: `add`'s follow-up `section add`, the remedy table's rows,
the `install --check` verdict, the criteria and priority families.

The instrument is not the gap. `runs()` executes each command a message composes and
asserts the exit code it was told to expect, which is exactly the property RK1475 broke.
The gap is the population it is pointed at: `SITES` accounts for thirty-six composers
and thirty of them are `unreached` — a work-list with a reason per row, honest and never
run. Six are executed, and RK1476's narrowing is a thirty-seventh that reaches `runs()`
only because a test was written for it by hand, which is the arrangement this is about.

So the work is fixtures, not a verdict: each `unreached` row is a state no test builds
yet, and what turns it into an answerable question is the state. That is a task per
family rather than one sweep — and the reason to file it as one line is that the six
that do run were each bought by a defect that had already shipped.

### §RK1538 The fact made structural and read as prose

RK1503 put `bound` on the violation so a reader can tell *the field is over* from *the
line is full*, and reframed the sentence the write path prints. Two readers it was
argued for do not use it.

The remedy table is one. `why.too-long` has a single row and a single door, and the two
states want different edits: a field over its own number is shortened, and a field the
line binds is a line whose *structure* is full — a dep, a `requires` group, a pointer.
RK1480 reframed exactly that case by inspection inside `DepRefused`, which is one door
of several and the only one that knows.

The protocol surface is the other. A `Violation` reaches a caller as a string, so an
agent over MCP reads the reframing as prose and branches on it by matching — which is
the reading `test_composing` exists to say is not a reading. The field is on the record
and no payload publishes it.

Neither is a defect today: the sentence is right and a terminal reader acts on it. What
is missing is that the fact was made structural and is still consumed as prose, which is
the arrangement it was made structural to end.

Worth deciding together, because they are one question: whether `bound` belongs in the
payload every refusal already publishes, and whether the remedy table keys on `(code,
bound)` — at which point `DepRefused`'s inspection becomes a row, and the doors that
reframe nothing get one.

### §RK1541 The surface trimmed by argument and never by reading

RK1506 added `budget --ship --decides` and exposing it over MCP put the tool at 2947
characters against the 2850 `[tools] characters` allows. So the flag is withheld, with
that number as the reason — and the caller it was written for is exactly the one that
cannot reach it.

The argument for the flag is a transport argument. `brief` prices all three lines a
departure writes and answers about the whole task; a caller composing one sentence wants
the allowance for that sentence, and over MCP a refusal costs the whole payload again.
That is the case for `--why`, `--retire`, `--ship` and `--defer`, each of which *is*
served. The tenth subject is the one the ceiling stopped, and nothing about it is
different in kind.

`budget` is where this bites because RK1321 already split it once: `tools`, `session`
and `brief` moved to `cost` when eight subjects under one name made it the largest
served tool. The split bought room and the room is gone, and the next subject meets the
same wall — so the answer *raise the ceiling* is the reviewer's limit RK30 replaced, and
the answer *split again* has no obvious seam left.

What is worth reading before either: which of `budget`'s sixteen exposed arguments the
served callers actually pass. `cost --tools budget` ranks the fields by what they cost
and nothing ranks them by what they are used for, so the surface has been trimmed twice
by argument and never once by measurement.

### §RK1542 The prefix the corpus is recovered through

RK1507 paired the carried line's writer and reader and said the ledger's continuation is
where the second such shape will be. It is already here, one field over, and it has
three readers.

`shipping._retired_why` composes a retirement's sentence as `superseded by <id>:
<reason>` or `abandoned: <reason>` — a derived prefix in front of the author's own
words, which the same docstring calls "the same shape and the same argument" as the
carried line. Two places read it back by splitting on the literal:
`tests/test_ranking.py` twice, to recover the partner id for the corpus every
duplicate-ranking figure is measured on.

So the number RK441, RK1183 and RK1477 all rest on is recovered by a hand-written
`split("superseded by ", 1)[1].split(":", 1)[0]`, against a string composed in another
module. Change the word and the pairs go to zero — and the test that would catch it is
the one asserting *at least eleven pairs*, which is the assertion protecting exactly
this and the reason nothing is silently wrong today.

That makes it cheaper than the carried line was: the guard exists and the coupling does
not. What is missing is the reader beside the writer — `superseded(why)` answering the
id or `None`, next to what composes it — so the split is spelled once and the corpus
reader asks for a fact rather than parsing a sentence.

Worth doing with it: `abandoned:` has no reader at all today, which is why it is the one
that will break first.

### §RK1544 The brief priced without its other files

RK1509 prices the widest brief for an adopter, and the reading is taken over the file
the run was **handed** — because `adopt` exists for a tree that has declared nothing,
where the roadmap role points at a path that is not there. Everything else the estimate
reads comes from the same handed file for the same reason.

`brief` does not. It resolves deps across the ledger and takes the design out of
whichever prose role declares the anchor — so on an unconfigured tree both are absent,
and the figure is a brief with no deps resolved and no design. Right about what this
tool could answer today, and low against what it answers once the project declares its
files.

How low is measurable and unmeasured. On this repository the same read over the declared
roles is what `cost --brief` prints; on a foreign tree there is nothing to compare
against, which is exactly the population the figure is for.

`adopt --with` already takes the other prose files for the doubled-anchor check, so the
seam exists: the same flag could give the estimate a design to price. What it cannot
give is the ledger, and deps are where a brief grows (RK1486) — so the honest shape may
be the figure with a clause saying what it does not include, rather than a wider read.

Either way the row currently states a number without saying which brief it is a brief
of.

### §RK1550 The pointer that runs the other way

RK1515 renamed one helper and two governed sections went stale: RK1516 named
`rendering._settled_rows` and RK1536 named RK1488's `settled` row, both prose about code
that had just stopped existing. Both were found by grepping `docs/` — `lint` was clean
before the amend and clean after it, and a shipped design citing a dead symbol is
exactly what this repository's docs being the conformance fixture is supposed to catch.

The pointer between two sections has `ref.dangling`; the pointer from prose into the
package has nothing. That asymmetry is the whole finding, and it is not about prose
being harder to check: an open design is read by the session about to do the work, and a
name it cannot find is the same wasted turn `ref.dangling` was built to prevent.

The rule is narrow enough to be safe. A backticked `<module>.<name>` or
`<module>.py:<Name>` whose module is one of this package's is a claim about code, and
resolving it is an AST walk of the tree `surface.modules` already enumerates. Anything
else — a flag, a filename, another tool's symbol — is not shaped like that and is never
asked about, which keeps the check off prose it has no business reading.

What decides its worth is which side it errs on. A design citing a symbol that a later
refactor renames is stale the moment the rename lands, and the finding has to name the
section rather than the rename: there is no automatic repair here, the sentence being
the author's.

### §RK1551 The note that says nothing about its own silence

RK1515 made every register honest about what it measured and left the gate where it was:
`non-goal.reaches` still falls silent the moment a design quotes a lead, answer or
citation alike. The suppression is right — RK1457's trade holds — but it is now the one
claim here nobody can see, the only place it is reported being `non-goal list`, which a
session runs when it is writing a constraint and not when the gate is what it is
reading.

So the finding is a missing sentence, not a missing rule. `lint` is where the note lives
and where its absence is a fact about the run: a line the note *would* have named,
silent because its own design quotes the lead. Said where a clean gate says what it did
not report, beside the counts, and never as a finding — nothing is wrong, and a project
whose designs answer their constraints would go red for having done the right thing.

What it buys is the case RK1515 was measured on. A citation suppresses a note about a
line whose author decided nothing, and the only reader who can tell is the one being
shown that it happened. Today they would have to run a second command to find out a
first one stayed quiet.

The cost is a line on a lint already printing two advisory rows, bounded by the same
rarity: most designs never quote a lead, and a project with none sees nothing.

### §RK1552 The reading taken twice

RK1516 gave `section drop` the row the three departure doors had, and did it by adding a
second call to `scoping.answered`: `sections._quoting` on the standalone path,
`shipping._settling` on the departures'. The rule stays one function, which is what
RK1478 was protecting, but the *reading* is now taken twice on two paths that delete the
same section through the same `sections.drop`.

They already share more than that. `shipping._drop_section` calls `drop`, gets a
`Deleted` carrying `cited` and `nested`, and returns five of its fields as a six-tuple —
the comment beside it says so: those are `drop`'s own answers, and a second reading here
would be two more things to keep true. `quoted` is the field that arrived after the
tuple was fixed, so it is the one that went around.

The close is to stop unpacking. `_drop_section` passes `constraints` the way the verb
does and returns the record; the departures read `deleted.quoted` and `_settling` is
deleted. That also removes a six-tuple whose positions the two callers spell out, which
is the sort of signature that acquires a seventh element rather than a name.

What makes it worth doing rather than tolerating is what the two would drift into. A
citation is suppressed by the substring either way, and the next question about *which*
quotations count is a change to one reader — with two, it is a change to one reader and
a grep for the other.

### §RK1553 The harder half of the same question

RK1517 asked one question of eighteen booleans and left it unasked of a hundred and
twenty-two values. The transport is the same — `serving` appends `--json` to every call
— so a value flag whose whole effect is on the rendered form is inert in exactly the way
`origin --why` was, and nothing anywhere would say so.

What stops the same sweep being pointed at them is the signature. A boolean has one
other form: leave it off. A value has as many as the field takes, and "identical
payload" is strong evidence for the boolean and weak for the value — `list --block A` on
a project with one block answers what `list` answers, correctly, and a sweep reading
that as inert would be reporting its own fixture again.

The shape that might work is a **difference the caller chose**: run the flag with two
values the fixture can tell apart, rather than against its absence. `--block A` beside
`--block B`, `--role improvements` beside `--role strategy`. Identical there is a much
harder thing to explain away, and it needs a fixture with two of everything the flags
narrow by — which is most of what this one already is.

The cheaper half first, if either: the values that are **enums**, where the parser
declares `choices` and the alternative value is derivable rather than invented. That is
a population the parser can enumerate, unlike a free string, and it is where a narrowing
flag that reaches nothing would hide best.

### §RK1554 The history with nothing written under it

RK1489 gave the pair fixture a history because a flag about the past cannot be read
against a directory with no `.git`. It gave it commits, not messages: both are written
with a subject and no body, so `origin --why` — which adds each commit's body under the
rows — answers identically to `origin` on the terminal too, and not only over the
transport RK1517 measured.

That went unnoticed because the flag is closed twice over. It is withheld from the
served tool and `--why` and `--json` are declared two subjects, so neither sweep asks it
anything any more. The next flag about a commit body will not have those, and the
fixture will answer the same way: no difference, for a reason that is nothing to do with
the flag.

The fix is one string. `git_commit` takes a message, and a body is a blank line and a
sentence; giving one of the two commits a real one costs nothing and takes an entire
class of flag out of the unmeasurable. What it must not do is give *both* a body, since
the fixture's value is that its two commits differ in named ways.

Worth doing because it is cheap, not because anything is broken. This is the third time
this fixture's reach has been the thing under discussion — RK1466 read it as a swallowed
flag, RK1489 as nine refusals — and each time widening it cost less than the reading it
produced.

### §RK1555 The two rules the declaration did not take

RK1518 moved one of `adopt`'s three argument rules to the parser and left two where they
were: `--with` without `--sections`, and `--prefix` with `--sections`. Both are raised
six hundred lines into the estimator, after the file has been located, and both are
invisible to everything that reads declarations — the dispatcher, the pair sweep, and
the schema an agent is sent.

They are not one job. `--with` is a narrowing, and `narrows(adopt_parser, "alongside",
"sections")` says it exactly. Declaration and enforcement both exist; what stands in the
way is the sentence, the caller reading *`--with` narrows a rationale file* rather than
*a backlog holds lines and not headings* — the shorter truth and the less useful one.

`--prefix` has no shape here at all. It is right beside `--ledger` and right alone, and
wrong only beside `--sections` — a flag refused **by** a subject rather than narrowed
**to** one, which `Answer` and `narrowing` between them cannot spell. So either a third
kind of declaration or an honest exception, and the choice turns on whether a second
instance of it exists anywhere in eighty verbs. If it does not, one raise with a good
sentence is the right amount of machinery.

What makes it worth a line is the surface: over MCP both are discoverable only by making
the call and reading the error, which is the cost RK1518 closed for one rule of three.

### §RK1559 The twelve sentences nothing has measured

The population is knowable now, and the first thing it says is that the figure covers
two of it. Fifteen note codes exist; this project's gate emits `read.priced` and
`non-goal.reaches`, and `engine.disagreement` is composed because no checkout here can
produce it. The other twelve have never been measured by anything.

That is RK1491's argument one step further along. A note is prose the gate says on every
run; it grew a clause in each of three tasks against no number, and the answer was to
price it — but what was priced is what this repository happens to trip. A sentence
nobody meets is one nobody has read for length either, and a note is the kind of text
that accretes: `block.emptied`, `task.worked` and `section.unpaired` each explain a
state, and none has appeared in a `cost` run.

Composing them is what `widest` already does for the fourth. Each of the twelve is a
function of a state a fixture can hold — a block with nothing under it, a section
addressed to no line — so the reading is one call per code against a fixture built for
it, which is what `tests/test_linting.py` largely already has. The figure that comes out
is *what this build can say*, beside *what this project meets*, which is the pair
`widest` and `here` already are.

It must not become a ceiling per code: RK1491 declined one for the whole cadence, and
twelve numbers with no argument behind them would be twelve limits that move.

### §RK1563 The census that reads a word and asserts a meaning

`tests/carrying.py` sweeps the package for a class with a field named `served` and
asserts the population matches a table of four. It found a fifth:
`budgeting.Noted.served`, the notes this server appends, which carries no prefix and
never could. The red was right and the message was not — it says *carries the prefix,
unaccounted for*, which is a claim about a field that has nothing to do with the prefix.

The census cannot tell the two apart, which is a property of what it reads. `served` is
the invocation prefix a caller is handed and also the ordinary word for anything this
server does; the sweep is by name, so any record reaching for it lands in a table about
something else.

Two ways, and different bets. Narrow the reading — a carrier is a `str` filled from
`served_by`, which the third test already checks and could check first. Or keep it and
fix the sentence: say what the field would have to be, so a reader meeting the red is
told to rename or to add a row rather than told a falsehood.

The second is smaller and closes the actual cost, which was one reading of a message
that did not describe the state. The first is what stops the next one arriving — and
both are cheap, so the question is only whether a name this generic is worth guarding by
shape.

### §RK1565 The same arithmetic, one note over

RK1526 saved 201 code units on `engine.disagreement` by saying its shared read once, and
the same shape is one file over. `install.stale` and `install.absent` file **per
surface** — the skill, its two reference pages, the hook, the launcher, the workflow —
so a project whose wiring is behind gets one row each, and RK1482 already measured a
session reading past three of them for hours.

Whether they repeat a read is the question, not an assumption. Each row carries the path
and the same door: `install` rewrites the ones this checkout ships. That door is a fact
about the *code* in exactly the sense RK1526 used — one command closes every one of them
— while the path is the row's own. So the arithmetic is the same and the population is
larger: six surfaces against four copies, on a note that fires on a wiring nobody has
refreshed.

What differs, and why this wants measuring rather than assuming, is that these rows are
not one note. They are separate subjects, and a reader may meet one alone in a report
about something else — the case RK1526's "whichever comes first" answer depends on not
existing.

So the honest first step is the number: what the six rows cost on a project with every
surface stale, and what they would cost with the door said once. If it is another two
hundred units the shape follows; if it is thirty, the rows are already right.

### §RK1569 The half that is somebody else's to change

RK1530 re-takes the split RK1497 drew its boundary from: zero in fields, non-zero in
prose. The first half is sound — 5,318 fields against the 3,962 the original counted,
and still zero. The second is a hard assertion resting on somebody else's checkout
keeping a sentence that happens to look mangled.

It has already moved. Eighteen prose hits at the measurement, three now: the corpora
advanced and RK1497's design, which quoted both examples, was deleted by its own ship.
Two of the three that remain are Shio's `×–` — a multiplication sign and an en dash, a
legitimate sentence somebody may reword tomorrow. When that happens the test goes red,
and what it will be saying is *somebody edited a backlog we do not own*, which is
nothing about the rule.

The suite already has the register for this. `test_corpora` warns and stays green where
the subject is a corpus that moved — the pins advisory is exactly that shape — and reds
only where the claim is about this build. A prose count falling to zero is worth a
reader's attention and is not a broken build, which is the definition of advisory this
module already wrote down.

What must not happen is a fixture. A string invented here that exhibits the signature
would make the assertion pass forever and measure nothing, which is the scratchpad probe
RK1530 replaced, one step further from the corpus.

### §RK1570 The composed field with no validator

RK1531 put the mangled rule on the fields the measurement argued for and left one out: a
block's title. `block add J --title "…"` writes a heading into every governed file at
once, and `blocking` validates nothing — no length, no shape, no codec. It is the only
composed field in this format with no validator at all.

That is a gap in a different direction from the one RK1531 closed. A section title had a
validator and the rule was missing from it; a block title has nowhere for the rule to
go, so adding this one check means deciding whether block titles are governed at all —
which is a question about the format and not about codecs.

The evidence that they should be is what the field does. A block heading is written into
the roadmap, the ledger and every prose role in one transaction, it is what `stats`
groups by and what `delivered` names, and `block merge` exists because two headings
under one label is a state worth a verb. A field with that reach and no rule is unusual
here.

What it must not become is `[limits] title`. A heading has no measured corpus behind it,
and RK1381 is the standing rule that a number this build fixes carries the reading it
came from — so the honest first move is the checks that need no number: not empty, one
line, no markup, and the bytes not arrived through the wrong codec.

### §RK1571 The five fixtures behind fifteen rows

Writing thirty-one states in one sitting made the next fact visible: they cluster. Three
rows want a checkout of this tool beside the project, four want a `ship --part` against
an id the ledger already holds, three want `declare` on a project missing a role, three
want a git history with a retired address in it, and two want a stored capture. Fifteen
of the thirty-one, five fixtures.

The table cannot say so. Each row names its own state, which is what RK1532 bought, and
a picker still reads thirty-one items rather than five families and a tail — the
difference between *this costs two lines* and *these four cost two lines between them*,
and the second decides where somebody starts.

A field would do it, on `Site` beside `state`: the fixture a row waits on, empty where
it waits on nothing anybody else does. Derived is unavailable — two rows wanting "a git
history" is a judgement about what a fixture would be, not a fact the source states — so
it is a declaration, held the way the states now are.

What it must not become is a taxonomy. Five names invented for five families is a second
vocabulary to keep true, and the honest form is the name of the **fixture that would
build it**: `test_installing`'s `source`, `test_pairs`' `_origin`. A row pointing at a
fixture that exists says how far the work is in the one unit that is not a guess.

### §RK1574 The rate two families measured

RK1572's family and this one are two of five, and both went the same way: the fixture
was cheap, and taking it found a door that could not be taken. The partial-ship family
turned up a `finish` spelled without backticks and a `ship <id>` that refused for want
of a `--why`; the `declare` family turned up `non-goal add` named on a project with no
heading for it (RK1573). Three defects, six rows, two sittings.

That is the rate the remaining twenty-five should be planned against. RK1498's own
sentence is that a composed command nobody runs is a command nobody has checked, and the
evidence is now that roughly one row in two hides something — not a stale reason, an
actual door that refuses, is invisible to the scan, or names a state the project cannot
be in.

What follows is ordering, not effort. The families left are a checkout beside the
project, a git history with a retired address, and a stored capture; the first is the
dearest fixture and the largest family. If the rate holds, the cheap ones are worth
finishing first for RK1532's own reason: each that comes out argues the next from
evidence.

What must not happen is the rows going quiet again. Each one now names its state, and a
row flipped to `run` on a test that asserts a sentence was printed would be the exact
failure this list exists to have ended.

### §RK1576 The rule one writer of five keeps

RK1533 gave `govern` a read-back — render the file, parse it, refuse the whole write
when the parse says no — and filed the rule as a decision: *a write to the config is
refused unless the file it would leave parses*. That rule now binds five writers and one
of them implements it.

The others are `declare <role>`, which adds a `[files]` row; `declare <table>`, which
opens an opt-in table; and two in `installing`. None reads back, and none is obviously
safe — which is the point: today's cross-key rules sit in `[tools]` and `[markers]`, and
the next lands wherever a table grows a second key constraining the first.

The fix is not five copies. `_readable` takes a composed string and a config and raises
the parser's own sentence; making it public and calling it from each writer is one
import per site, and what it costs is a TOML parse of a file every command already
parses once.

What makes it a task rather than a tidy is the property behind it. This package holds
`Document`'s round-trip over governed files by refusing the write, and the config is the
one governed file that had no such rule; a decision that says every writer is held and a
code base where one is, is a decision that reads as kept. The honest form is a sweep:
enumerate what writes `config.source`, and assert each goes through the read-back.

### §RK1578 The state nothing measures until it is taken

RK1532 gave thirty-one rows a state each, written in one sitting from the docstring at
each site. RK1577 took two of them and both were wrong the same way: they said a git
history with a retired address, and the reading wanted an outline with two families — a
two-line fixture described as a repository.

Overstating is the direction that costs. A row that reads dearer than it is stays
unpicked, which is exactly the failure RK1532 was filed to end, one level up: the
constant said *some state, unknown* and thirty-one rows went untouched; a state that
says *a git history* when it means *two headings* does the same thing to one row at a
time.

Nothing checks them, and nothing can: a state is prose about a fixture that does not
exist yet. What can be checked is the moment it is taken — a row flipped to `run` had
its state tested against reality, and the honest move is to record what the fixture was.
RK1577 did that in its comment; nothing made it.

So the shape is a rule, not a check. A row that becomes `run` keeps a sentence saying
what the fixture was — what the three families so far each wrote by hand — and the
table's test asserts a `run` row carries one. Thirty-one guesses and a growing count of
measurements is the most an unbuilt fixture can honestly be.

### §RK1580 The shell the composer assumes

`capturing.Capture.filing` composes with `shlex.join` and `tests/composing.commands`
reads with `shlex.split`. Both are POSIX by default, and this project's own platform is
not: a capture's absolute path goes in as `C:\Users\…\x.json` and comes out as
`C:UsersalexaTemp…`, because a backslash is an escape to the splitter that reads it.

Two halves of one question, and only one of them is a test's. The splitter is the
sweep's, and what it costs is a row that stays unreached with an honest state (RK1579).
The **joiner** is the tool's: a line composed for a reader to paste is quoted for a
shell they may not be running, on the one command whose whole job is to be pasted by a
maintainer.

Which shell that is, this package cannot know and should not guess —
`provenance.invocation` already refuses to describe a machine. What it can do is not add
quoting that is wrong everywhere but one family of shells: the fields here are a
symptom, a why and a path, and the only one that needs quoting is a value with a space
in it, which `shlex.quote` handles and `shlex.join` applies to the whole argv.

The measurement that would decide it is small and this platform is the one that has it:
take the line this repository's own `report` prints, and see whether `cmd`, PowerShell
and Git Bash each run it. If all three do, this closes as declined; if one does not, the
door on a Windows checkout has never been takeable.

### §RK1582 The third cadence nobody counts

Every `add` prints a header and three ranked neighbours, and nothing counts them. RK1491
gave the gate's notes a cadence, RK1524 gave the transport's, and this is the third:
prose composed per write, on the one command an agent runs most, never measured against
anything.

The argument is the one those two made and it applies harder here. A note fires on a
state; the near rows fire on **every** `add`, and they grew in three tasks — RK1370
wrote them, RK1374 added the counts, RK1495 added the second corpus and RK1528 the
second door. Each was argued and none was counted, which is exactly what RK30 says a
limit nobody counts does.

The reading is cheap and the shape exists. `Noted` prices what a run of the gate says,
and the same record fits: the header, the rows at the width this project's own symptoms
reach, and the sentence that says what the order is not. `VOLUNTEERED` bounds the rows
at three, so the figure has a ceiling by construction — which is more than the notes
had.

What it must not become is a limit. The rows are the duplicate read, and a project that
shortened them to fit a number would be trading the one thing this answer is for.
`Skilled`'s rule: the figure and where it went, with the judgement left to whoever takes
it.

### §RK1583 The other end of the sentence

RK1537 says at `govern limits.why` that a pause is not held to it. The other end of that
sentence is silent: `defer --reason` accepts a reason no `why` limit bounds and reports
nothing about what did bound it, so a caller who set that number and then paused a line
still learns the answer by inference.

The write is right to accept — the pause is charged against the rendered line (RK1479),
and `budget --defer` prices it correctly. What is missing is one word in the answer. A
deferral already reports what it wrote; saying the reason was measured against the line,
at the figure it came to, costs a clause and closes the loop RK1537 opened at the other
end.

The register exists. Every over-long field is refused with the limit it broke and the
key it came from, and RK1503 taught the refusal to say *which of two ceilings* bound a
field where it has both. This is the same fact on the accepting side: the number that
did apply, said once, where a caller can see it against the number they declared.

What it must not do is repeat itself. A clause on every pause is the note a reader stops
seeing (RK1443's rule, one register over), so the honest form is the figure beside what
was written rather than a sentence explaining the rule — the rule is at `govern`, where
the number is chosen, and this is the measurement.

### §RK1584 The one answer with no payload

RK1538's remaining half turned out to be larger than the sentence describing it. A
refusal does not have a payload: `_refused` prints to stderr and returns an exit code,
and over MCP `serving.call` hands the caller that text with `isError`. So there is
nowhere to publish the bound — not because nobody added a key, but because the surface
every write refuses through has no structure.

That is worth stating on its own, because it is the same finding one level up. This
package publishes a payload for every answer — `add --json`, `lint --json`, `brief
--json` — and the thing an agent most often meets is the one it can only read as prose.
`--json` on a refused call prints nothing to stdout and the diagnosis goes to stderr as
English.

What a caller does with it today is match. `serving` reroutes the command names inside
the text (RK475) so the sentence names tools rather than a shell; the rest — which
field, which code, which limit, which of two ceilings — is left in a paragraph, and the
agent reading it has exactly the options RK1503 was filed to remove.

What it must not become is a second vocabulary. Every violation already carries `code`,
`field`, `bound` and a message; a refusal payload is those, published, and never a new
set of names invented for the wire. Whether the exit code stays the contract is
untouched — the payload is what a caller reads *after* it has decided.

### §RK1585 The prose beside a table

RK1539's check reads one comment and one phrase: a backticked word within forty
characters of *command here* has to be a verb this parser has. It caught the defect it
was written for and it is narrower than the finding, which was that a comment naming a
population had been written from one of the two enumerations it compares.

The general form is not available cheaply, and saying why is worth a line. A bare
backticked word in this package is a verb, a flag, a field, a file, a config key or an
English word in emphasis, and nothing in the text separates them — `composing` can check
a backticked span that starts with the invocation because that prefix *is* the marker,
and prose about a verb carries no such thing.

What is available is the other direction: the enumerations. `COLLIDING`,
`serving.TOOLS`, `remedying.codes`, `composing.SITES` and the six laws are each a set
this suite already holds total, and each has prose beside it that a reader takes for the
set. RK1539's check is one instance of *the prose beside a table names what the table
holds* — and the question is whether that is a rule stated five times or a shape built
once.

The cheap version is a helper: given a table and its neighbouring comment, assert every
member is named and nothing claimed that the table lacks. Whether the second half is
decidable depends on the table, which makes this a design rather than a chore.

### §RK1586 The order nothing says is load-bearing

Adding one field to `Part` broke a reading in another module and the suite caught it,
which is the good half. The bad half is why: two of the three callers build the record
**positionally**, so a field declared above `characters` took the note's width and the
transport's prices went to `None` — measured, in one edit, on a record RK1522 had just
documented as shared by three subjects.

The record is right and the construction is what is fragile. `_parts` and `_pages` pass
keywords; `note_cost` passes four values in order, and nothing anywhere says the order
is load- bearing. RK1522's own table names who builds one and what its label holds — it
does not say *how*, and how is the part that broke.

The fix is small and is not a comment. `Part` can be keyword-only, which costs one line
at the declaration and turns every future insertion into a compile-time question rather
than a silent reassignment; RK1522's table then keeps meaning what it says. The
alternative is a rule nobody can enforce, which is what the note now beside the field
is.

What makes it worth doing rather than shrugging is what was nearly kept. The break
surfaced because one test compares a composed figure against the composer; a field added
where nothing did that would have moved a published number and gone green — which is
precisely the class `test_pairs` and `composing.SITES` exist to make visible everywhere
else.

## Block E — Adoption

## Block F — The plugin

### §RK1543 The version that is a commit

RK1508's design proposed dating a surface against "the same file at every tag this
repository carries". Measured while building it: this repository carries **one** tag,
`v0.2.0`, and 1,650 commits. The read had to walk revisions of the file instead, and the
reason it works at all is RK153 — the hook stamps a version into `__init__.py` on every
commit, so every revision is a version.

That is the finding: this project releases by bumping a patch number on every commit and
tagging almost nothing. Two things read as if it did otherwise. `origin` resolves a task
to the commits that proposed and shipped it, which is right; but `[install] pinned`, the
`gate.yml` reader and the plugin manifest all speak of versions as if a version were a
release somebody cut, and what a version actually names here is one commit.

Nothing is broken. Every version is real, every one is reachable, and `engines` compares
them correctly. What is absent is a statement of which model this project is on, in a
repository whose own docs are the conformance fixture for what a project should write
down. An adopter reading `[install] pinned` cannot tell whether pinning `0.2.103` pins a
release or a commit, and the answer changes what pinning means.

The cheap half is a sentence in `agents.md` or a decision record; the honest half is
asking whether the tag should exist at all, since a tool published as an action and a
plugin is consumed by ref.

### §RK1549 The last step this tool cannot take

RK1514 gave the copy a row and decided the default: a kept path is not a surface, so
`uninstall` reports the vendored engine and never deletes it. What that leaves is an
adopter who cannot get this tool off their disk with this tool. The row names no verb
because there is none — it says "delete the directory", the only sentence in the
un-wiring report that hands the work back to the reader.

The decision binds the default and nothing else. Deleting a `.roadkeep/` nobody asked
about is the reflex RK1514 refused, and every reason turns on the caller's silence: the
bytes may be committed, they are the adopter's, and a later `install --vendor` reuses
them. An `uninstall --engine` is the opposite act — the caller named the copy — so what
is left is that the removal is megabytes and irreversible.

Which makes it a design question, not a flag. Every other write here is all-or-nothing
over files this tool wrote; this one takes out a tree copied from somewhere else, and
`--check` has to say so first — *would delete*, which the withdrawal vocabulary already
spells. Whether it refuses a tree holding anything the copy did not put there is the
half worth settling: an engine an adopter has edited is not an artefact any more.

What would decide it is how large the copy is on a real adopter. Small enough to ignore
and the sentence is the whole answer, and this closes by being declined.

### §RK1560 The one entry the merge rule does not protect

`.mcp.json` is a declaration this tool merges into and does not own, and RK1492 stopped
a reader guessing at the program inside it precisely because a wrapper or `uv run` is a
legitimate thing an adopter writes there. `install` replaces it. Measured: a project
declaring `uv run serve-roadkeep mcp` runs `install`, exits 0, and holds the launcher —
the adopter's command gone, with no row naming what was there.

The merge rule is kept and that is what hides it. What survives is everything that is
not *this project's roadkeep entry*, which is right for a file other tools declare in
and wrong for the one entry an adopter may have written themselves. The two are told
apart by RK1523's own reading: a declaration whose program this command wrote is ours to
refresh, and one whose program it does not recognise is somebody's decision.

So the write splits where the report already does. Where the program is one of
`_PROGRAMS`, refresh it as now. Where it is not, the honest outcomes are to leave it and
say so, or to replace it and say what was replaced — and the choice is the adopter's,
which argues for the first plus a line naming the flag that overrides.

It must not refuse the whole run. `install` writes five surfaces, and a refusal over one
entry leaves a project half-wired for a decision about a file the other four do not
touch — the shape RK370 settled the other way.

### §RK1561 The fall-through the one-line answer does not mention

RK1523 gave the report a row for a declaration whose program this command did not write.
`engines --invoke` still answers as though there were none: it falls through to the copy
that is answering and prints `roadkeep`, which is correct as a shell instruction and
silent about the thing that makes it interesting — the harness is starting something
else, and which copy that reaches is inside a wrapper this tool cannot read.

The fall-through is right and RK1492 argued it: an invented answer is worse than the
honest one. What is missing is the same sentence the row now carries, at the one flag a
caller uses when it has decided to run something. A session reading `--invoke` alone
gets a command; the row beside it, which it did not ask for, holds the fact that the
command may not be the copy its tools go through.

Cheap, and the shape is settled by the flag's own history. RK1230 made `--invoke` one
line with no verdict, deliberately, because it answers *which copy to call* and a
paragraph there is a paragraph in a pipe. So the note belongs on stderr, where the
answer stays one line and a reader who piped it loses nothing — the same split `lint`
makes between a report and its verdict.

What it must not do is refuse. A declaration this tool cannot read is a legitimate state
and the caller asked for a command to run, not for an opinion about their harness.

### §RK1564 The suffix that would read as a fifth note

RK1525 finds a note by its site: an `Answer` whose text is an f-string, and the name of
any function called inside it. Four sites, four kinds, and the reading is exact today
because each site interpolates one composer and nothing else.

It is exact by accident. A site appending a note and a suffix — `{_landed(changed,
root)}{_now(served)}` — would report `now` as a fifth kind, and `_now` is the clause
this module reaches for: three composers already end with it, one dereference further
in. The sweep would be saying *a note nobody declared* about a sentence fragment, which
is RK1563's shape one file over — a census reading a token and asserting a meaning.

Narrowing it is cheap and there are two shapes. Take the **first** call in the f-string,
on the ground that the note is what the site is for and a suffix is not; or require the
call to be the whole of one `FormattedValue`, which is what a note appended by itself
looks like. Neither needs a list of exempt helpers, which is the answer that would rot.

What it must not become is a rule about naming. `_<kind>` is stated in `serving.NOTES`
and held by this sweep going red, and that is the right amount: a convention with one
reader and one failure. A second check that the composer is named after its kind would
be the same fact asserted twice, and the second copy is the one that goes stale.

### §RK1581 The config this verb looks for and the one every other finds

RK1534 made the orientation lead with `init` on a tree that governs nothing, and the
reading that decides it is `(root / "roadkeep.toml").is_file()`. That is a path this
module spells for itself. Everywhere else the config's location is `Config.source`,
discovered by walking up from a directory — and the two answer differently on a project
whose config lives in a parent, which is every subdirectory of every governed
repository.

The consequence is small and the wrong way round. `install -C sub/` on a governed
monorepo reads no `roadkeep.toml` beside it and tells the adopter that nothing is
governed yet, naming `init` — which would scaffold a second project inside the first.
That is the failure `_init`'s own comment names in as many words: a discovered config
would be an ancestor's, and scaffolding under someone else's paths is how a subproject
writes into its parent's roadmap.

So the literal is not obviously wrong: `install` is aimed at a tree, and the question
*does this tree declare its own* is a different one from *is this tree governed by
something*. What is missing is that the sentence answers the second and the reading
answers the first.

The fix is a sentence rather than a reader, if the reading is right: a tree under a
governed parent wants to be told so, not offered `init`. Whether `install` should
discover at all is the question behind it, and `Config.discover` answers it for every
other verb — the asymmetry worth stating before either changes.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
