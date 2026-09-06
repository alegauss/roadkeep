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

### §RK1527 The window that did not grow with the corpus

RK1495 doubled the corpus the near rows are drawn from — a block's deliveries and now
its open lines — and left the window at `VOLUNTEERED`, which is three. So three rows
cover twice as much, and the two halves compete for them.

That is not obviously wrong and it is certainly not measured. RK441 fixed the count at
three because an absolute score separates nothing and a longer list is a verdict wearing
an order; RK442 made the bound say so. Both arguments were made about one corpus. With
two, a long ledger can fill all three rows while the open line somebody filed an hour
ago sits fourth — the case RK1495 exists for, losing to the case it was not.

RK1477 measured the other end of the same read: a real pair ranked 7th against a window
of 3, and widening was left open. This adds a reason to take that up and a second axis
with it, because the choice is no longer only *how many*: three of each, or three
overall with the open ones preferred on a tie, are different answers, and the second
costs nothing.

What decides it is a reading nobody has: how often the open half wins a slot, and how
often it would with a window of four. Both are answerable from this repository's history
— every duplicate here was filed against a block whose two corpora are on disk.

### §RK1528 The door for one of two corpora

The near row ends with the command that shows the rest: `roadkeep delivered A` is all 6.
RK442's guarantee — a bounded answer says it is bounded and names where the rest are —
made about a corpus that was the ledger alone.

RK1495 made it two. The row now counts both halves and offers the door to one of them,
so a reader who suspects the fourth-nearest is the duplicate can open the deliveries and
not the open lines. `list --block A` is that door and the row does not say it, which
leaves the half the task was filed for as the half a reader cannot follow up on.

Naming both is one more phrase on a row already carrying two counts, which is the
argument against doing it carelessly: this row is printed on every `add`, and RK1374 got
it to its present size by choosing `delivered <block>`'s own two phrases over a second
wording. A second command doubles that clause.

The cheaper shape is one door that shows both, which may already exist: `delivered
--near` is the read this row volunteers, and whether it can take the open lines is the
same question RK1495 just answered for the write. If it can, the row names one command
as it does today and the corpus behind it is the one the rows came from — which is the
version that costs no characters at all.

### §RK1529 The declared path nothing checks

RK1496 added `[history] incidental`, a list of paths a commit here carries for reasons
that are not the work. The parser refuses an absolute one and normalises a backslash,
and nothing anywhere asks whether the file exists.

`[budgets]` is the same shape without that gap: a path declared there and absent from
disk is a finding — *declares a budget and is not on disk: the entry holds nothing*. An
entry naming nothing is not something the parser can see, a project being free to
declare before it scaffolds; it is a fact the gate reads off the tree.

What the silence costs here is worse than a wasted entry. `incidental` only ever
*removes* rows from `unclosed`, so an entry that matches nothing makes the report louder
— and one that stops matching, because a hook was rewritten or a file renamed, makes it
louder without anything having changed in the report's own code. The failure is a filter
quietly doing less, which is precisely the shape RK1496 was filed about from the other
side.

The row is one more `_Rule` over a list the config already parsed, on the sentence
`[budgets]`' own row already carries. What needs deciding is only the severity: a budget
naming nothing is a finding, and an incidental path naming nothing may be a note — the
report is advisory, and failing a build over a path somebody removed on purpose is the
gate turned off in a week.

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

### §RK1522 The record used three ways and documented as one

`Part` is documented as "one `##` section of an every-turn file, and what it costs", and
its fields say so: `heading`, verbatim, or `""` for what stands above the first one.
RK1491 needed a row per note and reused it, so `heading` holds `read.priced` — a code,
which is not a heading, is never `""`, and has no file to be a section of.

The reuse is not accidental, and that is the argument for it. Three subjects want one
shape — a label, a width, a rank — and `Skilled.pages` stretched it once already, to a
reference page where `heading` holds a path. A good shape attracting a third caller is
ordinary; three records with identical fields would be three names for one idea.

What it costs is the docstring, which `agents.md` makes the authority on what a record
is. It describes one of three uses, so a reader meeting `Part("read.priced", 1, …)`
works out from the call site that `heading` is a lie. `lines` and `bytes` are worse: a
note row fills them with 1 and a length nobody reads, because the record demands them.

Two ways out, and they are different bets. Rename it to what it is — a labelled weight,
`heading` becoming `label`, the counts optional — or leave it and write the three uses
into the docstring. The second is not the lesser fix: a record used three ways honestly
is a record, and the same one used three ways silently is the drift.

### §RK1526 The read a code owns and every row repeats

RK1494 split `engine.disagreement` into a row per differing copy, and RK1491's reading
priced the trade the same day: 643 code units joined, 893 split — 250 more for four rows
a reader can act on separately. That is the right side of the trade and not free, and
most of what it cost is one sentence said four times.

Every row ends with the same clause: *`engines` reads every copy and names the revision
each one is at*. It is there because a note's message is where its door goes — the
remedy table feeds `explain`, and the gate's report renders the message and nothing else
— so a row without it is a row with no read behind its move.

The specific moves are not the duplication: `/plugin update`, `install --vendor` and the
restart each appear once, on the row they close. What repeats is the read that lets a
reader choose between them, which is a fact about the *code* and not about any one copy.

So the question is whether a report can attach a code's shared read once beside rows
that carry their own. `remedying` holds that sentence for `explain` already, and
`_report_rows` is where a terminal renders a row — the fact exists and the render does
not use it. What is not obvious is the shape: a line above four rows is a grouping this
report has never had, and inventing one for a single code is the ceremony RK1443 cut.
Measure it first.

### §RK1530 The measurement behind a refusal

RK1497 drew its boundary from a number: over the prose of three real corpora the
mojibake signature fires 18 times and every one is a false positive; over the 3,962
fields of the same three it fires zero. That reading is why the rule is a field's and
never a body's, and it exists nowhere but in a docstring and a changelog `why`.

The probe was a scratchpad script. Nothing re-runs it, so the next person weighing
whether to widen the rule — to a section title, to a body behind a flag, to a second
codec — has the sentence and not the measurement. RK30's argument in the shape this
repository keeps meeting: a number nobody counts is one that stops being true.

The suite already has the corpus. `tests/corpora.py` pins Shio and Turing at a revision
and skips where they are absent, which is what CI does and why a green run here proves
more than a green run there. A test walking the two populations and asserting the split
— zero in fields, non-zero in prose — costs one pass over files the suite already opens.

It catches both directions. A field growing a run is either a real mangling in a live
backlog or a signature that has begun matching prose people write; a prose count falling
to zero means the boundary bought nothing. The second is what nobody would look for, a
rule that never fires reading exactly like one that is right.

### §RK1531 The field on the wrong side of the boundary

Measured one command after RK1497 shipped. `add --section "O menu Ã© semeado"` is
accepted and writes the heading, while the same six bytes in the symptom beside it are
refused. The title lands in a prose file as a permanent heading, which is the durability
the refusal exists for.

The boundary RK1497 drew is *field, not body*, and a title is on the field side by every
property the measurement used: one line, bounded by a limit, composed by a caller as an
argument, and never where somebody quotes an example — the design section under it is.
All 18 false positives were in bodies. So this is not a widening but the population
already argued for, minus a door.

It is worse than a mangled symptom in one way. A symptom is corrected by `restate
--typo`, which RK1474 built for exactly this and the remedy row names; a heading is
`section amend --title` and the anchor stays, so the correction is cheap. But a heading
is what `ref.dangling` and every listing quote, so the bytes are copied onward before
anybody looks.

The same question is open one field over: a non-goal's lead, a criterion's lead, a block
label. Each is a short composed field in a governed file, and whether the rule reaches
them is answered today by which validator the door happens to call — which is what to
find out first, because the answer may be one shared function away.

### §RK1532 The work-list with no sizes in it

Thirty-eight rows of `composing.SITES` carried one shared sentence: *the message needs a
state no fixture in this suite builds yet.* True of all of them, and it is why none was
picked for as long as the list existed — an item whose cost is unstated reads as
open-ended, and a work-list of thirty-eight open-ended items is a list nobody starts at.

Measured by starting at it. Four of the thirty-eight came out in one sitting, and each
wanted **two lines of fixture**: a ledger entry beside a ⏳ line, a deferred copy beside
an open one, two symptoms sharing an id. The shared reason was accurate about every one
and useful about none, because what a picker needs is not *why not yet* but *what would
it take*.

`_UNMEASURED` in `test_pairs` is the same table one file over and says the state each
row wants — *no `[non_goals]` table*, *no deferred store*, *a clean tree* — which is
what makes a row there something somebody can act on. This list has the field and spends
it on a constant.

What it buys is a size. A row naming the state names how far the suite is from it: *a
project with no config at all* is `init`'s own fixture and cheap, *a home replaced under
a live process* is not, and saying so stops the two looking alike. RK1498's remainder is
thirty rows, a number that means nothing until each says what it costs.

### §RK1533 The write that closes the file behind it

Measured. On a project declaring `[tools] characters = 3000, session = 70000`:

    roadkeep govern tools.characters 80000
    roadkeep.toml:7  tools.characters = 80000 (was 3000)

    roadkeep lint
    roadkeep: tools.session is 70000 and tools.characters is 80000:
    a surface may not cost less than one tool in it

The write landed and the file is now unreadable. Every verb fails on it, `govern` among
them — so the number cannot be put back by the verb that moved it, and the repair is the
hand edit the guard denies.

`Violated` guards one thing and guards it well: a number the *corpus* already breaks.
This is the other kind — a number the *config's own parser* refuses, because two keys in
one table constrain each other. The parser knows the rule and says it clearly; `govern`
never asks. It reads the corpus, writes, and hands back a reading.

The population is small and enumerable, which is what makes this worth closing rather
than accepting: cross-key rules live in `config.py`'s own validators, and the one
measured here is the only pair in `[tools]`. `[markers]` has three such rules and
`declare` writes that table.

The shape of the fix is the shape `Document` already has for a governed file (L3):
render the file that would be written, parse it back, and refuse the whole write if the
parse says no. One `Config.parse` against a string this verb has already composed — and
it turns a class of unreadable configs into a refusal that names the rule the parser
would have.

### §RK1535 The readings nobody keeps

RK1500 held the reason one half of the duplicate read cannot be scored: every known
answer is written into the field a query would join, so the only population with a
ground truth is the one where the truth is an input. That leaves the read half-measured
for as long as the corpus is retirements.

The population that would settle it exists and is not recorded. Every `add` prints three
ranked neighbours, and some of those authors then act — `restate`, `retire
--superseded-by`, or nothing at all. Each of those is an answer given **before** the
answer was known, which is exactly what the retirement corpus is not.

Nothing writes it down. The rows are composed, printed and dropped; the ledger records
the retirement and not the reading before it, so which proposals this read has caught is
unknowable — and RK441's threshold measurement was taken over retirements for that
absence.

What would record it is a decision about scope and not a design: the ids a write
volunteered, in the transaction that volunteered them, so a later `retire
--superseded-by` joins to whether the read had named its partner. That is a fourth thing
the roadmap holds, which is why it is weighed rather than done — a log of readings is
not a fact about the backlog, and L2 says what the store is.

The cheaper half may be enough: `add --json` publishes `near` already, so a session
keeping its transcripts has the population without this tool storing anything.

### §RK1536 The decision with no door of its own

RK1501 had to put its sentence in `brief` rather than at the deletion, for a reason
worth naming on its own: `ship --decides` is a flag on the departure, and no verb files
a decision afterwards. `revise` corrects one that exists, `supersede` replaces one —
both start from a record. So the moment the answer is lost is the moment nothing can be
done.

That shapes every door around it. RK1488's `quoted` row names the constraint whose
answer just went and can offer nothing; RK1501's row has to fire on a read taken
*before* the work, which means a session that skips `brief` never sees it. Two rows
about one fact, one of them too early to act on and one too late.

The ledger does not have this problem. `record add` writes an entry that was never a
roadmap line, on the argument that the only route in was a fictitious line shipped in
the same breath — which taught that the format can be gamed. The decisions role has no
such door, so that route is the only one: file a line, ship it with `--decides`.

Whether it should is a real question, not obviously yes. A decision with no work behind
it may be what an architecture note is, or may be the file filling with claims nothing
paid for. What decides it is who writes one: measured here, both answers this repository
lost were written by an author who had just done the work.

### §RK1537 The limit one door does not read

RK1502's sweep nearly filed a defect that was not one. On a fixture declaring `[limits]
why` and no `line`, `defer --reason` accepts a 172-character reason where every other
write in the table refuses — which reads exactly like the defect RK1479 repaired, coming
back.

It is not. A pause is charged against the **rendered line** and never against `why`
(RK1479, RK1115): the field carries a wrapper and the design carried forward, so what
bounds it is what the line comes to. Declare `line` and the same call is refused. The
fixture was wrong and the verb right — and the two are indistinguishable from outside: a
caller sees a long reason land and cannot tell *nothing measured it* from *the number
you declared is not the one this reads*.

That is the thing to close. Every other over-long field is refused with the limit it
broke and the key it comes from; a pause under a `why` nobody declared `line` for is
accepted in silence, and the author who set `why` to bound their prose has bounded
nothing here.

`budget --defer` already prices the pause correctly, so the refusal is not the place —
the write is right to accept. What is missing is a sentence where the number is chosen:
`govern limits.why` could say a pause is not held to it, which is
`Measured.unmeasured`'s reading one level down — the key is read, and one door does not
read it.

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

### §RK1539 The example written from one side

RK1504's design names two collisions: `claim`, a verb here and the tool for `brief
--claim`, and `scope`, "a command here and the tool name for `claim --path`". The
enumeration finds one. `scope` is not a verb of this CLI — it is a name `_accepting`
*takes*, mapping it to `claim`, which is RK1481's own work.

So the design's second example was wrong about which surface holds `scope`, and the
sentence in `cli.py` that RK1481 left says the same thing: "`scope` is a command here
and the tool name for `claim --path`". Both were written from the tool table, where
`scope` is a name; neither checked the parser. Nothing broke, because the rule they
justify — never respell a verb this CLI has — is right whichever example illustrates it.

What that costs is a reader who follows the example. The comment sends them to look for
a `scope` verb, and the guard it explains fires on `claim` alone; the sweep now says
which, and the prose beside the guard still says the other.

The fix is one sentence and the finding is not. It is that a comment naming a population
was written from one of the two enumerations it compares — the shape RK1504 closed for
the *names* and left open for the *prose about them*. `test_configured` scans this
package for a marker literal already; a comment naming a verb this CLI has not got is
the same claim.

### §RK1540 The frontmatter a reader pays for

RK1505 put two lines of frontmatter on `asking.md` and `writing.md` so the absent-page
note can name the verb a reader is missing. Those pages are loaded by a session that
opens them, and the frontmatter is loaded with them — on every turn that opens a page,
for a fact only the gate reads.

It is small: two keys, about 90 characters each. It is also exactly the kind of cost
this project measures rather than assumes. `[budgets]` prices what loads every turn,
`cost --skill` prices the write path, and RK1437 split the pages off `SKILL.md` because
65k units a turn was a reference loaded as an orientation. A page whose whole reason for
being a separate file is what it costs to open now opens with two lines addressed to
somebody else.

Nothing measures it either way. `cost --skill` reports `pages` beside the skill — one
row per reference page — so the figure exists and the frontmatter is inside it,
indistinguishable from prose a reader uses.

Two shapes are worth weighing. The declaration could live where the other per-file facts
do — `PLUGIN_PAGES` is a tuple and a second element per entry costs a reader nothing —
at the price of the page no longer stating its own claim, which is why RK1505 put it
there. Or the figure is taken and 90 characters turns out not to be worth moving, which
is a reading and not a guess.

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
`rendering._settled_rows` and §RK1536 named RK1488's `settled` row, both of them prose
about code that had just stopped existing. Both were found by grepping `docs/` — `lint`
was clean before the amend and clean after it, and a shipped design citing a dead symbol
is exactly what this repository's docs being the conformance fixture is supposed to
catch.

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

## Block E — Adoption

## Block F — The plugin

### §RK1523 The fifth copy, which is a command

RK1492 stopped `declared_launcher` guessing at a program it did not write, and the
honest answer where it finds neither launcher is `""`. `Engines.invoke` then falls
through to the copy that is answering, which is right — and indistinguishable from a
project that declares no server at all.

Two facts share one silence. *Nothing is declared here* means the running copy is the
only one; *this project declares a server whose program I do not recognise* means the
harness runs something the report cannot name, the state `engines` exists for. RK415's
own argument from the row above: "no plugin" and "a plugin this could not read" look the
same, and only one of them means the writes are unjudged. That distinction was made for
the plugin and never for the declaration.

The declaration is in no report either way. `Engines.declared` feeds `--invoke` and
appears in neither `stated` nor `payload`, so a reader asking which copies this project
runs sees four rows and not the thing the harness executes. A wrapper, `uv run`, a shell
script — any of them starts the server, and the answer to "which copy" is inside it.

What closes it is a fifth row on the same terms as the other four: the declaration as
written, and where the program is not one this command wrote, said so rather than
dropped. Read and never judged, which is `driver`'s rule one row over — a command beside
the trees, with the comparison left to whoever reads it.

### §RK1524 The notes on the transport nobody counts

RK1491 gave the **gate's** notes a cadence: `cost --notes` prices what a clean run says
beside its verdict, on the argument that a paragraph nobody counts is a paragraph that
grows. RK1493 then enumerated a second population entirely — the four notes this server
adds beside a tool result — and nothing measures any of them.

They are the same kind of text under a heavier cadence. `_landed` rides on a successful
write, `_inventory` on a refusal this process did not witness, `_swapped` on a home gone
from disk, and the witnessed paragraph on every refusal that overlaps — each of them
appended to an answer an agent is already paying for, over the transport L5 exists to
keep cheap. Three are once-per-process, which bounds them; the fourth is per-call by
design.

The history is the argument. RK267 cut one for being 450 characters of correct and
irrelevant text on a refusal that had said everything actionable in one line; RK1443 cut
another for arriving four times in a batch. Both cuts were made by reading and neither
left a number, so the third growth is invited exactly as `engine.disagreement`'s was —
which RK1491 found had grown 35% since the task naming it was filed.

`Noted` is the shape and `NOTES` is now the population, so what is missing is the
composer being callable the way `linting.disagreement` was made callable: each note
built with its worst-case arguments, ranked, and the per-call one marked as the one paid
every time.

### §RK1525 The half a call-site sweep cannot see

RK1493 made `serving.NOTES` total against the literals the module passes to
`_said_once`, so a fifth once-per-process note is a red until somebody declares it. That
is three of the four kinds. The fourth is in the table by hand and matched by nothing.

The asymmetry is structural rather than an oversight. A once-per-process note is
recognisable because it *makes a call* — the guard is the thing the sweep reads — and a
per-call note is recognisable by nothing at all: it is a branch that appends a
paragraph, which is what most of this module does. So the sweep is total over the half
that announces itself and silent over the half that does not, and a second per-call note
added tomorrow arrives exactly as the kinds did before RK1493: invisible.

What makes it worth closing rather than accepting is that the per-call half is the
expensive one. Three kinds are bounded by the process; the fourth is paid on every
refusal that overlaps, which is the population RK267 had to cut once already.

The reading that would work is the one `test_composing` takes over `invocation()`: find
the sites rather than the calls — every `return Answer(f"{text}\n\n…")` in `_advise`,
which is what appending a note *is* — and hold the count against the table. That names a
shape the module already has instead of asking a per-call note to announce itself, which
is the `_said_once` guard turned into ceremony for a kind that needs no guard.

### §RK1534 The orientation printed before there is anything to orient

Measured while widening RK1498's sweep. The orientation `install` prints on a tree with
no governed files names five commands: `brief` picks the next line, `add` files one,
`ship` closes it — and none of them can run there. `runs()` executes a message's
commands **in the order printed**, which is RK1198's finding, and here the sentence
saying what has to happen first is not first.

Nothing is wrong with any one line. Each names the right command and the orientation is
correct about a governed project. What is missing is that the same five lines are
printed to a reader who has one and to a reader who does not, and only the second needs
the order to mean something.

That is why the site is still `unreached`. A fixture that runs the orientation has to be
a project the orientation is *about*, and building one is a task: a config, three files,
a line filed and a design under it — at which point the five commands run and the sweep
says something. On the tree where the note actually appears they refuse, and a test
asserting that would be asserting the defect.

So the shape to decide is whether the orientation belongs on that answer at all, or
belongs after whatever the project still owes. `Plan` knows which surfaces it wrote and
what it could not; the orientation is composed from neither.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
