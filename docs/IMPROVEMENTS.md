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

### §RK1511 The door a one-task-one-commit rule needs

One task, one commit has a consequence nothing here has a door for. A task that finds
work inside its own sentence cannot do it, because the commit is that task's; so it
files a line instead, and the tree carries the half-built thing until the second line is
worked. In the port this tool governs, four of the nine idea-marked lines are that exact
shape: a seam nothing calls, a check its own commit reworded around, a departure
recorded only in a comment.

The other reading is that they were never separate work. Had the finding been a
criterion on the task that found it, the line would have shipped partial under RK1433's
rule and finished under the same id, and nothing would have been carried between two
commits.

What is missing is the move from the first shape to the second. `criterion add --task`
writes the sentence and `retire` ends the line, but they are two writes: the criterion
cites no origin, the retirement cites no destination, and the id is spent either way
with no record that the two acts were one.

A fold is one transaction: the open line's own symptom becomes the criterion's lead
under the task named, the line leaves by the door `retire` already opens, and the ledger
says which task absorbed it. It refuses where the target has shipped, the case the
second write cannot see today. Whether the fold is right stays the author's judgement.

## Block C — Query

### §RK1510 The question weight is the other half of

`weight` (RK71) prices what a comparable task cost, so granularity is a query rather
than a feel. Nothing prices what a task left behind. In the port this tool governs that
reading took two `git log` runs and a `comm` over roadmap snapshots: the backlog held 19
to 26 open lines for three weeks while the id counter went from 66 to 727. Neither
figure is derivable from anything this tool prints.

It matters because a backlog decomposing and a backlog discovering look identical from
the count alone. Four of the nine idea-marked lines open there were debts the
immediately preceding commit chose to leave, not findings the work turned up, and which
of the two it is decides whether the answer is a smaller task or a criterion written
earlier.

The join is the one `unclosed` already makes from the other end: a commit names ids, the
ledger dates each entry, and an id first appearing within a span after an entry is that
entry's fallout. RK94's correction binds here too - a commit shipping several entries
gives its filings to none of them rather than a share, a divided count being one no
commit contains.

Two axes and no score, the way `weight` refuses one: filings per entry, and the span
they arrived over. Whether a rate is too high is a judgement this has no model for, and
the block whose lines file the most behind them is often the block where the leverage
is.

### §RK1512 A store the picker does not know is there

`defer` is the door for work that is neither shipped nor abandoned, and the store it
writes to is read by nothing that picks. `picking.py` and `briefing.py` mention the role
nowhere: the `paused` counter is lines blocked on a paused dep, RK92's answer, which
reaches a deferral only where something open still depends on it. A deferral nothing
depends on is invisible to every tier.

Measured in the port this tool governs: roughly thirty-four loop iterations ran on one
block without the file being opened once. Six of its seven deferrals were honestly
waiting on hardware. The seventh was set aside as accepted, citing a premise that twenty
files under the tree had already falsified, and nothing went red for it because a reason
is prose and prose does not go red.

So the ask is not that `pick` offer them - a pause is a decision and offering it would
undo the decision. It is that the answer stop being silent about a store the project
declared: the count, and the oldest reason, in the sentence that already names ready,
blocked and paused. A caller then knows there is a file to read, at the one moment the
backlog looks fully gated.

The audit is the second half and belongs with it: a deferral carries a reason, and a
reason has a date and no expiry. What `resume` needs is not a prompt but a reading, and
the reading starts with knowing the lines are there.

### §RK1513 The absence nothing says before the work

RK1185 settled that a criterion is read before the first edit rather than at the ship,
and it settled it for lines that have one. Where a line has none the brief prints
nothing, and the absence is first said out loud by `criterion.absent` - which
`linting.py` scopes to the partial marker, so it fires after part of the work has landed
and the question it raises is how much is left.

That is the wrong end for the one case this repository already has evidence about. A
task that will find work inside its own sentence is exactly the task whose criteria
would have caught it, and the only moment those can still be written is the call that
starts it.

Not a gate, and not a demand that every line carry one: most do not need one, and RK1358
already refuses to read an empty list as a met one. What the brief owes is the same
sentence it gives the deps - this line carries no criteria - so the absence is a thing
the caller declined rather than a thing nobody was shown. The judgement stays the
author's, which is L4.

The cheap version is one clause in an answer already composed, and it is worth pricing
against RK1309's finding that a first body is written blind: both are the same shape, a
read the author needs at the moment before writing and can only reach after.

### §RK1519 The marker a project may not declare

Measured. A project declaring `[markers] open = ["📋", "💡", "🔨"]` — legal, validated, and
exactly what L6 says a project may do — gets this from `pick --claim`:

    status: '🛠' is not one of 📋 💡 🔨 [status.unknown]

`take` writes `set_status(config, id, IN_PROGRESS)` with the package constant, and
`claiming` compares against it in five more places. `[markers]` has five keys — `open`,
`shipped`, `retired`, `deferred`, `undesigned` — and no sixth, so the marker the whole
claim machinery turns on is the one thing about a marker vocabulary a project cannot
say.

The reach is every door that claims — `pick --claim`, `brief --claim`, `hold`, and
`claiming.follow`, which releases by asking whether the marker just written was that
one. On such a project `claims` lists nothing ever, no line being able to reach the
state it lists, and nothing says why. RK1490 found it by composing `status <id> 🛠` and
running it.

The fix is a sixth key and a reader, and the shape is settled by the other five: `open`
already carries the marker, so `markers.working` naming one of them is a narrowing and
not a new vocabulary — with the refusal every other key has when it names something
`open` does not.

What it must not become is a guess. Picking "the open marker that is not `undesigned`"
would answer 📋 here, which is the *default add* marker, and a tool that quietly claimed
lines by moving them to the state a fresh `add` writes is worse than one that refuses.

### §RK1520 The gate the fix walks past

`test_no_module_writes_a_marker_a_project_declares` scans the package for a literal
marker codepoint, on the ground that `[markers]` is per-project and a message naming one
tells the reader about a glyph their files may not use. It works: RK1490 wrote `status
<id> 🛠` into a composed sentence and the gate caught it inside a minute.

The repair it accepts is to interpolate the constant instead, and that is the whole
problem. `f"status {task_id} {IN_PROGRESS}"` renders the same six bytes, says the same
wrong thing to the same reader, and is invisible to a scan for the codepoint. Both of
this package's remaining sites are that shape, and one of them is a refusal telling a
caller how to take a line.

So the gate rewards the fix that does not fix it. What it looks for is a message naming
a marker the reader's project may not declare; the literal is one route there, and the
import is the other — the one a developer takes *because* the gate is there.

Reading the import is mechanical: the name is `IN_PROGRESS` and the same scan finds it
one token over. What a scan cannot decide is whether an interpolation is wrong, a
message about the marker a write just moved being legitimate — that fact came off the
file. So what is missing is a stated shape rather than a rule: a *composed command*
carrying a marker constant is the wrong one, and a report of what a write did is not.

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

### §RK1515 The citation that reads as a decision

Measured on RK1488's own shipment. Its design quoted *No supported Python API.* while
**describing** RK1465 — the case that proved an answer leaves silently — and the ship
printed `settled 'No supported Python API.'` as though a judgement had been made and
lost. None had: the clause was a citation of somebody else's decision.

The rule is `settles`, a substring match on the lead, and RK1457 chose it deliberately —
a lead is the constraint's address, matching it is cheap, and the alternative is a
reader of intent, which is L4. That trade was made for a **note falling silent**, where
a wrong match costs one advisory nobody sees. RK1478 put the match in a listing and
RK1488 in a write's report, so it now carries two claims it was never sized for: this
line settled that rule, and the answer just left.

The corpus: this repository has two designs quoting a lead and one of them is a
citation. Fifty percent of two is not a number, but it is the only one there is, and it
fired on the first shipment after the feature landed.

What might close it is a shape and not a reader — an answer names the rule in a sentence
about the rule, while these citations are prose about another line and carry its id.
Whether that is recognisable without a model is the open question, and the honest
outcome may be a weaker verb in the sentence rather than a narrower match.

### §RK1516 The fourth door that deletes a design

RK1488 gave `ship`, `retire` and the closure door a row naming the constraint whose
answer went with the design they deleted, on the ground that the write is the last
reader that still has the section. `section drop` deletes a design too, and says
nothing.

The three that were taught share `_drop_section`, which is why they were one change.
`sections.Deleted` is a different record for a different verb and already carries the
neighbouring facts — what nested under the heading, who is left citing it — so the field
it lacks is the one this task added next door. RK206's history repeating: the citation
line came through the departure path first, and this verb stayed silent for a year.

The argument for doing it is unchanged from the departures. Against it: this verb is
aimed by hand at a section the author is looking at, so they may already know. That does
not survive contact — dropping prose somebody else wrote a year ago is the ordinary
case, and RK1478's whole finding was that the clause reads as a stray remark about its
subject.

Cheap either way: the reader is `scoping.answered`, already called by
`shipping._settling` for exactly this, and the row is `rendering._settled_rows`, already
written. The one question is the seam — `drop` takes a `Document` and not a `Config` on
purpose, so the leads arrive the way `claimed` and `where` do, passed in by the verb
holding both.

### §RK1517 The flag the transport makes inert

`serving` appends `--json` to every call it makes, so a flag whose whole effect is on
the terminal rendering shapes nothing over this transport. `origin --why` was one: the
payload carries each commit's `reasoning` either way, and an agent setting the flag read
an unchanged answer as the one it had asked for. RK1489 found it by accident — the pair
sweep could see it only once its fixture had a git history to resolve against.

Eighteen boolean flags are served today and nothing asks this of them. The pair sweep is
the closest thing and not close: it runs `reads_only` verbs, so the four on writes are
out by construction, and three more sit in `_UNMEASURED`. What it does cover it covers
by comparing `X --json` against `--json` — the right reading, aimed at the wrong
population.

The read that would answer it is one call per served boolean: run the tool's own argv
with the flag and without, and a payload identical both ways is a flag this surface
cannot honour. Cheap, total, and it says which of the three things is true — the flag
shapes the payload, the payload already carries what it composes, or it belongs in
`withheld`.

The value flags are the harder half and probably not this task's: 122 of them, most
narrowing a listing, and "identical payload" is the right signature for a boolean and a
weak one for a value that may legitimately match the default.

### §RK1518 The refusal a declaration was built to replace

RK489 replaced twenty-five hand-written lines inside `budget` with a declaration every
verb makes at `add_parser`, so one dispatcher refuses two answers before a handler runs.
`adopt` kept its own: `--ledger and --sections measure different units` is raised from
inside `adopting.adopt`, six hundred lines past the parser and after the file has been
located.

The refusal is right and its sentence is better than a generic one. What it costs is
that nothing else knows. `_one_answer` lets the pair through and `separated()` reports
the two as compatible — which is how RK1489 met it, as a row in `_UNMEASURED` saying a
correct exit came from somewhere the sweep cannot read. The served surface is the
sharper half: over MCP the pair is discoverable only by making the call and reading the
error.

The estimator makes it concrete. `_widened` retries the other role when nothing was
asked, and its own comment says "tried separately because the two flags are refused
together, and the estimator is what declines the pair" — a function reasoning about a
rule enforced two files away, which is the coupling the declaration exists to remove.

What closes it is `answers(adopt_parser, ("ledger", …), ("sections", …))` and deleting
the raise, with the sentence moved into the group's `what` so nothing is lost. The one
thing to check first is whether any caller reaches `adopt()` directly with both set —
the library door has no parser in front of it, and a rule that lived there may still be
load-bearing.

### §RK1521 The population a note figure is taken over

RK1491 gave notes a cadence and could not say what it left out. The read prices the
notes this project's gate emits — one, at 282 — and one composed worst case, and there
is no third number because there is no list: nothing anywhere says how many note codes
exist.

The registry is almost there. `remedying`'s table is asserted **total** over every code
`linting` and `schema` can emit (RK421), and it holds 122 of them — but a note and a
finding sit in it side by side with nothing separating them, so the population of notes
is not derivable from the one place that knows the population of codes.

What that costs is what `brief` refused to accept for its own subject. `read.priced`
exists because a figure taken over part of a population is one a reader misreads: it
says *4 of 26 open lines priced, 22 not asked for*. `cost --notes` says nothing of the
kind and cannot — 282 reads like the answer when it is one of an unknown number of
sentences.

The split is a field on the remedy row or a set beside the table — a decision about
where the fact lives, not a discovery. What it buys is the sentence `brief` prints and
one more: an unmeasured note code is a clause somebody adds without meeting a number,
which is the drift RK1491 was filed against and closed for one note out of however many
there are.

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

That shapes every door around it. RK1488's `settled` row names the constraint whose
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

## Block E — Adoption

## Block F — The plugin

### §RK1514 The copy uninstall keeps and does not report

RK1487 gave `install` one sentence about a copy it left behind: a vendor that lands and
then fails to wire now names what is on disk and what the next run does with it. The
same tree pointed the other way says nothing.

`removal` already has the field for it. `Removal.kept` exists precisely so "a surface
silently kept reads as missed", and RK284 made what goes in it a reading of the disk
rather than a constant — but only one path is ever considered, the CI workflow. A pinned
project's `.roadkeep/` is the whole engine, several megabytes of it, and after a clean
`uninstall` it is a directory nobody declared, nothing points at, and no line of the
report mentioned. The caller who asked for the tool to be gone reads a success and still
has it.

Deleting it is the wrong reflex, which is why this is a report and not a removal. The
bytes may be committed, they are the adopter's, and a verb whose subject is declarations
is not licensed to take out an artefact a later `install` would reuse. What closes this
is one `kept` row on the same terms as the workflow's: the copy is there, nothing is
wired to it now, and here is what removes it.

Worth deciding alongside: whether `--check` counts it, since the `changing` verdict is
about surfaces and a copy is not one.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
