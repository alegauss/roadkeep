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

### §RK1495 The neighbours that have not shipped yet

Every `add` prints its three nearest neighbours and the row says what they are drawn
from: `3 nearest of 154 delivered under this block`. The ledger, and only the ledger. An
open line is not in the corpus, so two callers filing one defect within the hour cannot
see each other — which is precisely when a duplicate is cheapest to catch and most
likely to happen.

Measured here. RK1472 was filed against `budget` taking no `--requires`, and RK1461 said
the same thing in almost the same words and was **open** at the time; both quote the
same 21 characters of `(requires: upstream) `. RK1461 shipped, RK1472 was designed and
briefed and then retired as superseded. Ranked against the delivered corpus afterwards
it comes back **second** — the window would have named it, had it been in the corpus at
all.

RK1477 is the other failure of the same read and not this one: there the pair ranked 7th
against a window of 3, so widening or re-ranking is the question. Here the ranking is
already right and the corpus is wrong.

Why deliveries alone is worth keeping: RK385 argues the symptoms are what a proposal is
checked against, and a delivery is a claim made good on. An open line is not — which is
a different fact and, here, the more urgent one: a duplicate of shipped work wastes a
task, and a duplicate of open work wastes two sessions at once.

### §RK1496 The bump that defeats the filter

RK1473 drops a commit that touched only files this tool governs, and it works on the
adopting project it was measured against. It does nothing here, and the reason is this
repository's own `.githooks/pre-commit`: every commit bumps the patch version (RK153),
so every commit also touches `src/roadkeep/__init__.py`, `.claude-plugin/plugin.json`
and `editor/package.json`.

Measured after shipping it: `unclosed` reports two of twenty-three open lines, both of
them commits that amended a roadmap line and a rationale section and nothing else — the
exact false positives the task removed — kept alive by three files a hook wrote.

The rule is right and must not learn about the bump: *the files my own pre-commit
touches* is not a fact roadkeep may encode, and a project that bumps a version in every
commit is entitled to do so. But the conformance fixture is this repository, and a
filter that is inert on it is one whose next regression nothing here will catch.

Two readings are open. A diff could be asked whether a one-line change matching a
version literal is a bump — clever, and cleverness in a history reader is how a false
negative gets written. Or the project declares it: `[budgets]` is already a list of
paths, so a key naming what a hook writes every commit is the same shape, argued once by
the project that has one.

Worth weighing against both: the report is advisory, and being loud here costs a reader
who is already this repository's maintainer.

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

## Block D — The gate

### §RK1494 The four causes wearing one code

`engine.disagreement` now composes four clauses — a modified checkout, a plugin at
another number, a vendored copy at a third, and a home that states a fourth. Each was
added by a task that measured it, each is right, and they are joined by `and` into one
sentence with one code.

So the gate has one row for four different states with four different remedies: look at
the tree, `/plugin update`, `install --vendor`, restart. A reader acts on whichever
clauses are true, and `explain engine.disagreement` — the read that says what a code
means and which doors close it — can only describe the union.

Every other multi-cause finding here is split. `priority.block`, `priority.unmigrated`
and `priority.config` are three codes about one section precisely so each names its own
door, and `remedying` keys the table by code. This one is four causes wearing one, which
is the arrangement RK420 built the table to avoid.

The question is whether they are four codes or one code with a subject. They differ from
the priority family in a way that matters: two of them can be true at once and often
are, and four rows on one commit about one subject is the noise RK1308 and RK1443 each
cut. A subject per clause — `engine.disagreement` filed once per differing copy, the way
`install.stale` is filed per surface — keeps one code, gives each row its own remedy,
and lets a project quiet the one it has decided about without silencing the rest.

### §RK1497 The bytes a gate could have refused

RK1474 gave the copied claim a respelling door in the ledger and the decisions file, and
the door is deliberately narrow: the correction must fold to the claim on record. What
nothing does is stop the mangling happening.

The measured case is undetectable at the door — an ASCII transliteration is legal prose,
and `add --symptom "Menu do site novo e semeado"` is a caller writing exactly what they
typed. But it is the *cheap* case, and the expensive one is detectable: `Ã©`, `â€™` and
the replacement character are what a wrong decode leaves, and a symptom carrying them is
bytes that arrived wrong rather than words somebody chose.

The gate already has the shape. `lint` refuses an invisible codepoint by name, on the
argument that a character a reader cannot see is one no author meant — and mojibake is
that argument with the character visible and meaningless. The write path is where it
belongs (L1): a symptom refused at `add` costs a retyped field, and one caught by the
gate costs the respelling door this task had to build.

What is not obvious is the boundary. Prose may legitimately quote a byte sequence, and a
check refusing `Ã` outright would refuse a line about encoding bugs — which this backlog
has. So the rule is probably a note, or a refusal a flag steps over; either way it is a
reading taken against a real corpus and not a pattern written from memory.

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

### §RK1499 The gate a limit claims to have

`govern` refuses a number the corpus already breaks, on an exact argument: a limit whose
first act is a finding is one somebody lowers, reads the report and raises again. RK1476
declared a key that has no finding at all — `[reads] list` bounds an answer the verb
declines to compose, and the ledger it is declared against is over it permanently and by
design. So the refusal fired on the one project the key exists for, and the write was
undeclarable.

The fix was a `refuses` flag on `Measured`, False at that one reading. What it says is
*no gate reads this key* — a fact about `linting.py` restated by hand in `governing.py`,
with nothing holding the two together. A key marked True whose finding is withdrawn
refuses writes for a gate that is gone; one marked False that a gate does read lets a
red be declared, the exact failure `Violated` exists to stop. It defaults to True, so
both drifts arrive silently.

The population is enumerable. `GOVERNED` names five tables, `describing.TABLES` every
key in them, and four functions in `linting.py` read one. So the property is: for each
governed address, `refuses` agrees with whether any finding reads it — one test over two
tables neither of which was written for it, which is the shape `test_composing` and
`test_surfaces` already use. `prose` and `claims.held` are the same fact stated a third
way, in prose a gate cannot read.

### §RK1500 The half of the ranking nothing can score

RK1477 joined the `why` to the ranked corpus and measured it: six of eleven known pairs
inside the five became nine, worst reached rank 11 → 3. The other half of that change
could not be measured at all.

`add` ranks the line it just wrote, and that query has a `why` too. Joining it looked
better — RK1303 moved 3 → 2, RK1456 2 → 1 — and the reading is worthless. A retired
entry's `why` is written **at the retirement**: it names the partner and paraphrases it.
So the eleven queries whose answer is known are the population where the ground truth is
an input, and a figure over them scores the ledger's own bookkeeping.

The corpus side is clean because the corpus is the *partner's* text, which no retirement
wrote. That asymmetry is what makes one half of this change a measurement and the other
an argument, and `claim` says which it is — the shape this project already uses for
`prose` and `claims.held`, where the honest answer is that nothing measures the key.

What would settle it is a query population answered before the answer was known: the
`add`s whose volunteered rows the author acted on. Nothing records those, so nothing
knows which proposals this read has already caught — the one fact that would price its
own query side, and the absence RK441 worked around by using retirements.

### §RK1501 The answer a ship takes with it

RK1478 made the answer readable from the rule. It did not make it survive. `settling`
reads open lines only, and has to: a ship deletes the design, so the clause that settled
a constraint goes with it. Both of this repository's answers were lost that way inside
an hour — the incident the task was filed from — and the report shows a `settled` row
until the line ships.

That is the shape of the store and not a defect in the read: a decision argued in a
design lives as long as the work, and the constraint outlives it. So the next `add` on
that subject gets `non-goal.reaches` again with no trace the question was asked — the
loop RK1457 broke, closing back up one ship later.

There is already a file for facts that outlive the work: `DECISIONS.md`, what was
weighed and what a constraint cost, which `ship --decides` writes from the open line's
claim. Nothing carries the settling clause across, though the ship knows it is deleting
a design and `settles` can say which constraint that design answered.

The judgement is not the tool's (L4): a ship whose design settles a constraint says so,
and the sentence is the author's — a door at the moment the design is deleted, never a
synthesis. The alternative already rejected is a second store keyed by lead, and the
decisions file is not that: it is where this project already writes what a constraint
cost.

### §RK1502 The write that measures nothing

RK1479 set out to price a pause and found the write did not measure it. `defer --reason`
composed a store line and validated nothing: `_as_paused` re-renders from data, `place`
checks the anchor and the block, and the field the caller had just typed went in
unmeasured. A reason that pushed the line past 320 landed, and `lint` reported it
afterwards — L1 inverted on the one door where nobody had noticed.

The repair was three lines; finding it took a budget predicting a refusal that never
came. That is the interesting part. Every other write here is held by the same law and
nothing says which ones are: `add`, `amend`, `ship`, `retire`, `restate` and the three
list verbs each compose prose and each validate it, and `defer` looked exactly like them
from outside.

The population is enumerable the way `test_surfaces` enumerates wired writes: verbs that
hand a composed `Task` to a renderer, against the ones calling `validate` first. What
made this one invisible is that its field is *composed* rather than taken — the wrapper
and the carry are the tool's, so a reader scanning for a bare `--why` reaching a schema
sees nothing missing.

So the check is not *does this verb validate* but *is every field it writes measured
before it is rendered*. One test over the writes census this suite already builds, and
it would have named `defer` the day the store shipped rather than when somebody tried to
price it.

### §RK1503 The limit that is not in the file

RK1480 set out to name the dep in a refusal and found the refusal does not name the line
either. Where the line binds, `why_budget` folds the line's remainder into the field's
own ceiling, so the schema reports `why.too-long — 167 characters, limit is 162`. There
is no `[limits]` key with 162 in it. The number is derived, per line, from the symptom's
width and the deps the line happens to carry, and the message says so in a parenthesis
after the fact.

That is why the measured author went and shortened a sentence. They were told a limit,
the limit looked like a limit, and the door it named was the `why`. Nothing in the
sentence was wrong: what had changed was a dep.

`Share.bound_by_line` already publishes the distinction, and `budget` prints `← the line
binds, not the field` on exactly these rows. So the read knows and the refusal does not
— the inverse of the arrangement this tool is built on, where the number arrives before
the prose and the refusal is the backstop.

The repair is not a new rule but a field: a violation carrying which of the two ceilings
refused it, so every reader — gate, write path, remedy table — can say *the field is
legal and the line is full* rather than quote a ceiling nobody declared. `DepRefused`
reframes one case by inspection; the other doors adding structure to a line,
`--requires` and `--ref` among them, meet that sentence and reframe nothing.

### §RK1504 The name that is two acts

RK1481 made the CLI take the MCP spelling, and the guard it needed is the finding.
`claim` is a command here *and* the tool name for `brief --claim`; `scope` is a command
here and the tool name for `claim --path`. Respelling either rewrites a correct call
into a different act — a silent wrong write, worse than the refusal replaced. The rule
is one line: never respell a verb this CLI has.

What that line does not remove is the collision. Two names are each a command on one
surface and a different act's tool name on the other, and nothing anywhere says so. A
third such pair is one `Tool(..., named=...)` away, and the person adding it has no
reason to look: the declaration is about naming an act, and the fact that the name is
already a verb of this tool lives in `cli.py`.

It is checkable and cheap. Tool names and command paths are both enumerable, and what
has to hold is that a served name which is also a command names the *same* act — `list`
is `list`, and `claim` is not `claim`. Two rows break it today and both are deliberate,
so the test is a table of the pairs with a reason each: `test_composing`'s shape and
`test_surfaces`'.

Renaming one side is the wrong repair: `scope` and `claim` are right on their own
surfaces, and the cost is not the collision but that nobody is told it exists.

### §RK1505 The page named, and not what it says

RK1482 split one note in two and put a count on the summary. What it did not do is
answer the question the note now raises: which pages a project is missing, this gate
knows, and what those pages *say* it does not.

The measured cost was never the file's absence. It was that `budget --anchor` measures a
section before it is sent, `--body-file` names a paragraph by path, and the session did
not know either — so one design took five refusals against the word limit, each
re-sending the paragraph. The note now says a page is missing. A session that already
skipped three notes because they were about tooling has been given a fourth of the same
kind.

What would not be skipped is the verb. `install.absent` on `asking.md` could name one
command that page documents and this project's reader has no way to find — derived,
because the page is in this checkout and the backticked commands in it are enumerable,
and `test_composing` already walks composed commands for exactly that reason.

The risk is what the whole gate is written against: a note that grows a list gets
skipped for a different reason. So it is one verb and not the roster — which one is a
judgement, and therefore the page's to state rather than this tool's to rank (L4). That
makes it a line of frontmatter in the skill pages and a read here, not a heuristic.

### §RK1506 The lines a departure writes and this cannot price

RK1483 paired `budget` against six writes and found the table wants a seventh column.
Eight of the exemptions it had to write are `ship`'s, and four of those say the same
thing in different words: the field belongs to a *different line* than the one this
subject prices.

`--remainder` writes the roadmap line's why. `--decides` writes the decision's. `--part`
and `--decides-ref` are structure on lines this subject is not about. `brief` already
knows this — it prints `shipping`, `deciding` and the line's own row off one read, three
budgets for three lines — and `budget` has one subject per *verb* rather than one per
line, so a ship that writes three lines is priced as one and the other two are
exemptions.

That is the asymmetry worth naming. What `brief` gives free is what `budget` cannot be
asked: there is no `budget <id> --decides`, and the number is already composed a few
frames away. A caller mid-ship who wants the decision's allowance has `brief`'s whole
answer, or nothing.

The cheap shape is not a subject per line but a departure's subject pricing *every* line
that departure writes, as `brief` already composes them: `budget <id> --ship` printing
the ledger sentence it prints now and the decision's beside it where `--decides` is
passed. The exemption table then loses four rows, which is the test saying what the
surface should have been.

### §RK1507 The carried line's two readers

RK1484 taught `record amend` to recognise a continuation this tool wrote. It recognises
it by a string prefix — two spaces, the word, the bold that opens a lead — matched
against what `_verified` composes a thousand lines away in the same module. Two readers
of one shape, and their failure is silent in the direction that costs: change the indent
or the word, the recogniser stops matching, the entry reads as hand-wrapped, and the
door returns to demanding a span. Nothing goes red, and a caller meets the refusal
RK1484 removed.

The kernel's rule is the answer and is already stated: `Schema.render` is the only
writer of the line format and `Document` the only reader of a file, because a field
written by one function and read by another is one the two come to disagree about. A
carried line is a line of a governed file. It has a writer, now a reader, and neither is
the schema.

So the shape is one function composing a carried line and one deciding whether a line is
one, beside each other, with a test round-tripping a composed line back through the
recogniser — `render` and `validate`'s arrangement at the smaller scale, which the
module docstring already claims about every other line this tool writes.

One shape today. It was zero before RK1460, and the ledger's continuation is the obvious
place for a second — which is when the prefix match becomes a table of them.

### §RK1508 The version the bytes already carry

RK1485 made the absent record readable and left the second shape its own design named
unbuilt: the version could be *derivable*. The bridge and the skill are copies of files
this package ships, so which engine wrote them is a question their bytes can answer
without a record.

That is not a guess, it is a lookup. Every released version of this package contains one
`hooks/roadkeep-launch.py` and one `SKILL.md`, and the surfaces on disk either match one
of them or match none. What blocks it today is that a checkout holds exactly one version
of each, so the comparison has one candidate — which is why RK1462 wrote a record
instead.

Where the candidates come from is the question. Git has them: the same file at every tag
this repository carries, one `git show` each, the answer being the newest whose bytes
match. No adopter's clone can make that read, which is the honest limit and also the
population that does not need it — a plugin-served project has no vendored copy to date.

So the shape is narrow and one-shot. `install --check` on a repository with this
package's history could say *these surfaces are 0.2.71's*, once, before the first
`install` writes a record. That buys the one decision RK1462 cannot inform — whether the
refresh in front of you is an upgrade — and everything after it is the record's, which
is why this is a read.

### §RK1509 The reading nobody adopting is shown

RK1486 took the reading its own design asked for and the reading falsified the design.
The graph rows reach 133 units on Shio and 183 on Turing, a twentieth of a brief; what
makes those briefs wide is prose. It shipped the split that proved it, corrected the
argument above the key, and left the number alone.

What it could not leave alone is that Shio's widest brief is 3,354 against the 3,300
declared here. That number is this project's own (L6) and Shio declares none, so nothing
is broken — and nothing tells Shio either. A project that has never declared `[reads]
brief` gets silence from the gate, which is the opt-in working and also the state every
adopter is in permanently.

The reading is one command and now says something an author can act on. What is missing
is the moment it reaches them: `install` and `declare` write configuration, `adopt`
measures a tree before either, and none of the three prices the read this tool
recommends over reading the file — so an adopter learns their briefs are 3,354 by
meeting a refusal, or never.

The narrow shape is `adopt` reporting it: that verb reads a foreign backlog and states
what governing it would cost, and the widest brief is a number of that kind. Not a
default and not a finding — a figure in the report, so the project choosing a ceiling
has the reading in front of it at the moment it chooses.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
