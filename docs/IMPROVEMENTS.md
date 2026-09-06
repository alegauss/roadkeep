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

### §RK1608 The narrowing that could not narrow

Measured on a throwaway project whose open set is `["📋"]` and declares no undesigned
marker: `pick --designed` exits 0, returns the same line `pick` returns bare, and prints
nothing about the flag. `config.schema.undesigned` narrowed to the empty tuple —
correct, RK83's rule, and the same fallback RK1556 just gave a sentence to one key over.

`pick --have upstream` is the second instance and looser: `[requirements] declared` is
empty by default, so the token names a word the project has never defined, and the
answer is again the unnarrowed one.

What decides the shape is whether the caller is wrong or the project is silent.
`--designed` on a backlog with no undesigned markers is not a mistake — it is a flag
that has nothing to do here, and the answer should say so on the `skipped` row that
already exists and prints only when the count is non-zero. `--have` may be the other
kind: a token `[requirements]` does not declare is a word nothing can satisfy, which
RK1467 refuses on the line side and not on the caller's.

Both are one row or one refusal, and which each gets is what this line has to settle.

### §RK1609 The span three functions rebuild

Measured against the property RK1558 had just shipped. A `help=` f-string whose
backticked command carries a *literal* marker beside an interpolation — the marker
written out, the id filled in — is read by none of the three scans: `_offered` splits
the shown string at each `ast.Constant`, so the two backticks land in different nodes
and the span never re-forms; `_composed_markers` reads only an interpolated marker
*name*; `_values` exempts the words a caller is shown.

The same gap the other way is the second instance. `_composed_markers` matches
`MARKER_NAMES` alone, where the literal sweep and the new one both hold markers, ids and
governed files — so an f-string composing `lint` round the roadmap path constant builds
a command out of a value `[files]` decides, and nothing flags it.

One root: three functions each rebuild what a caller is offered, and each stops
somewhere different. `_composed_markers` already joins an f-string's literal parts
before looking for a backtick, which is the reading the other two want — so the repair
is one helper the three share, and the third value kind on the scan that reads one.

### §RK1618 Nothing to file is a finding

`delivered` states what a block shipped and `reversals` what it undid, and both are
named as the read before an `add`. Neither answers the third question a proposal meets:
was this looked at already and deliberately not filed?

pportal has twenty-five such findings and keeps them in a per-user memory directory
outside its git, so a second machine, a second agent or a second person re-traces them.
The tracing is the whole cost. `session.c:970` returns without closing a socket and is
harmless only because `ChiakiTarget` has six values, two of which the guard excludes,
leaving exactly the four the formatter answers for — reading that took longer than any
fix it ruled out.

A free-prose reason cannot carry it. An entry that says checked, fine is unfalsifiable
and gets re-traced; what makes one durable is the premise it names, because that is the
thing a later commit can break. A seventh target value makes `session.c:970` real, and
nothing else does.

This is none of the three doors that exist. `retire` is for a line that was filed,
`defer` for work still waiting, `reversals` for a decision undone. Here nothing was ever
filed and the finding is that there is nothing to file, which is exactly why it has
nowhere to live — and why the same suspicion is filed from resemblance instead: of four
such filings in pportal, three needed correction.

## Block D — The gate

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

### §RK1588 The figures a decision rests on

RK1541's read found its own subject stale: the withholding reason for `budget --decides`
quoted *2947 characters against 2850*, and the tool measures 2758 today. The number was
right when RK1506 wrote it and wrong within the session that read it back — a surface
moves whenever a `help=` is edited, and nothing connects the two.

That is one instance of a shape this project keeps meeting. RK1530 re-took the mangled
rule's split for it, RK1540 published a page's declaration share for it, and this task
removed a third frozen figure by replacing it with a read. What none of them did is ask
how many are left.

The population is enumerable and nobody has enumerated it. A number in a docstring or a
withholding reason that names a measured total — `2947`, `3,962 fields`, `65k units a
turn` — is a claim about a surface that moves, and the ones that matter are those a
*decision* rests on: withheld arguments, declined ceilings, chosen limits.

What would settle it is a sweep for digit-groups in package prose beside the reads that
would re-take them. That is noisy — most numbers in these docstrings are corpus
measurements whose whole point is being historical, and RK1530's own docstring quotes
two on purpose. So the honest first step is smaller: the reasons `serving.withheld`
declares are a closed set, each is a decision, and each can be read for a figure the
tool can now compute.

### §RK1590 The prefix that says a span is a door

Measured while running the merge row (RK1589): `install --register-merge` was backticked
with no invocation in front of it, in a sentence whose sibling door carried one.
`commands` skips a span that does not begin with the invocation, so the door was not
counted as unreached — it was not counted at all.

An AST walk over the package, docstrings excluded, finds ninety such spans across
nineteen files. Most are prose — `install --vendor` being named as a flag, `ship
--decides` as a family — and some are doors. Nothing distinguishes them, which is the
whole finding: the sweep's population is whatever authors happened to prefix, and a door
that forgets is invisible rather than red.

Two ways out, and the choice is the work. A gate rule that every backticked span leading
with a verb carries the invocation would make the ninety a list to walk and would refuse
prose that legitimately names a flag. A narrower one — only spans in a string that
reaches a printed message — needs a way to tell those from the rest, which is the same
static question one layer in. What is not open to question is that a scan reading the
prefix cannot decide which spans it was meant to read.

### §RK1591 The step before the command

`export.unmarked` fires where a file carries a begin marker and no end. Its remedy is
`export --readme`, which is the command that closes it — after the two lines the message
names are pasted. Before that it refuses, and `repair` walks `run` doors, so it
dispatches one it cannot open and reports `0 ran, 1 refused`. That is RK1475's rule met
from the other side: a finding naming a command that then refuses is worse than one
naming nothing.

None of the six kinds fits. `decide` is a choice between doors and a test holds it to
more than one, there being nothing to choose here. `read` says the command writes
nothing, which is false. `compose` says a field is the author's, and no field is.
`restore` says another tool owns the command. `fix` is the mechanical pass and `run` is
what it is.

What is missing is a kind whose door is complete, writes, and is not runnable **yet** —
the precondition being an edit in a file this tool does not own. That is one field on
`_Rule` and one branch in `runnable`, and it is the second half of the same question
RK1475 answered by withdrawing an offer: a door with a precondition can be printed
honestly or not printed at all, and this tool has only ever had the second.

### §RK1600 The argv inside the paragraph

RK1584 gave a refused call a payload: the violations, the two clauses above them, and
the sentence. What it did not give is the **retry** — the caller's own argv with the
address this tool derived substituted into it (RK1149), which is the one thing in a
refusal a reader executes rather than reads.

It is in there. `said` carries the whole rendering, retry row included, so an agent that
wants the command parses a paragraph to find it — which is the arrangement the payload
was added to end, one row further down.

Two things make it not a copy of the sentence. The retry is an **argv**, and every other
argv this package publishes goes on the wire as a list: `lint --json` publishes a
finding's door that way, and `explain` publishes a remedy's. And it is derived rather
than quoted — the address came from a read this refusal made, so a caller holding it can
retry without a second call.

What is not settled is the shape. A door elsewhere is `{argv, what}`; a retry has no
`what`, being the caller's own call. Whether it publishes as a bare list, or beside the
address that was substituted into it, is the decision this line is for.

### §RK1601 The flag named and the call unspelled

RK1541 gave `cost --tools <name>` the reading, and pointing it at the whole surface
answers with a number nobody had: **58 arguments across 33 tools**, worth 9,939 code
units of schema, appear in no call the shipped guidance spells.

Not undocumented. `ship --decides` is written about at length in `writing.md` and
appears in no `ship …` span there; `section amend --replace` has a paragraph and no
call. That is the distinction `tests/composing` draws between a flag named in prose and
a command somebody pastes, and for an agent-first tool it is the one that matters: an
agent reading the orientation is told the flag exists and left to compose the call,
which is exactly the composition RK1198's whole family found going wrong.

The cost is paid twice. Every session pays the schema at connect, and the session that
needs the flag pays a refusal to learn how it goes.

What is not settled is which way to close each one. A call spelled in the pages costs
words on an every-turn budget `lint` holds (RK30); withholding the argument costs a
caller the subject entirely. The reading now exists per tool, so the decision is per
tool — and `ship` at five arguments and 967 units is where it is worth making first.

### §RK1602 The comment that says it is derived

`reverting._MARK` recovers the forward pointer a superseded decision carries, and the
comment above it reads: *Built from that constant rather than spelled again — the writer
and the reader of one clause disagreeing is the defect this package is about, and a
second literal here is how it would start.*

It is a second literal. `_MARK = re.compile(r"\(superseded by ([^)]+)\)")` spells the
head that `shipping._SUPERSEDED` composes, and nothing joins them. The comment is not
merely stale — it is the argument for the pairing, written at the site that does not do
it, which is worse than silence: a reader checking whether the coupling exists finds a
sentence saying it does.

Cheap, and the shape is settled twice over. RK1507 paired the carried line, RK1542
paired the retirement head, and both landed as a reader beside the writer with a
round-trip test between them. Here the writer is `_parenthesised(why,
_SUPERSEDED.format(replacement=<id>))` and the reader wants the same treatment: one
function in `shipping` answering the id a parenthesised clause names, and the regex
built from the constant it already claims to be built from.

What that also buys is the guard RK1542 wrote, widened: nothing outside `shipping`
recovers either clause by hand.

### §RK1603 The note said once per key

`config --json` is 34,172 code units over 75 keys, of which 16,503 are the harvested
notes and **10,052 are repetition** — the same sentence carried on every key of its
table. `[files]` sends its note six times for 5,190 units; `[install]` three times for
2,580.

It is a payload key and not a printed row, so the terminal never shows it twice: the
listing prints the note once above its table and the JSON attaches it to each key. That
is the shape RK1526 removed one answer over, where a gate note said the same read on
every finding and was published once with a marker on the first.

Two ways out and they are not the same. The note could move to a table-level entry
beside `keys`, which is a payload change a consumer notices; or it could stay per key
and be sent once, on the first key of each table, which is what RK1526 did and costs a
consumer nothing but a lookup.

What decides it is who reads this. `config` is served, so the caller is an agent holding
one key's row and asking what its table means — and a row that answers only sometimes is
a row that has to be joined.

### §RK1604 The three questions one name answers

`Config.has(role)` is `role in self.paths` — one line, no docstring, in a package where
the module docstring is the authority and every function carries an argument. It is
called 109 times.

Three questions it could be answering, and it answers none of them cleanly. *Does the
project declare this role* — no: on a tree with no `roadkeep.toml` it says true for
`roadmap`, `changelog` and `improvements`, whose paths are this build's defaults. *Is
there a file* — no: none of those three exists. What it answers is *does this build have
a path it would use*, which is the question nobody asks by name.

Measured by getting it wrong. RK1544's first reading asked `has` for the roles a brief
consults and produced a clause that named `deferred` and `strategy` on this repository —
roles it has chosen not to declare, where the figure is whole — while staying silent
about the ledger and improvements file that were genuinely absent on the tree the read
is for. Two wrong answers from one call, and the correction was `paths.get(role)` and
`is_file()`.

What is worth deciding is whether the other 108 want the same correction, or whether the
name should say which question it takes.

### §RK1605 The population the guarantee is over

RK1498 ends with a sentence worth being exact about: *every site is run or deliberate*.
The population it quantifies over is `census()`, which is every function calling
`invocation()` — so a door composed without the prefix is not a site, is not counted,
and is covered by nothing.

Met, not theorised. `sections._WAYS_OUT["amend"]` printed `section move {anchor} --to
<free anchor>` at every over-long amend since RK1034 and appeared in no census. It was
bare, so nothing found it; the placeholder held a space, so nothing could have run it;
and the sentence promised the one act `section move` refuses by name (RK377). Three
defects in one clause, none reachable by the sweep built to find exactly this. It
surfaced only because RK1548 added the invocation while quoting the placeholder — which
made it a site, which made the census red.

The fix is not to widen `census()` to every backticked verb: help strings name verbs
constantly and are prose. What is undecided is whether the guarantee should be restated
over the population it actually covers, or the population widened to the doors
`commanded` finds — RK1590's ninety spans are the same question asked about findability.

### §RK1607 The four the sweep found next

RK1518 moved one of `adopt`'s argument rules to the parser and RK1555 moved a second.
The scan that decided the third — every raise in the package naming two flags — found
**six**, and four of them are two answers `answers()` already spells:

`govern --because/--instead`, `retire --folds-into/--superseded-by`, and
`--block/--task` at `criterion list` and `criterion drop`. All four verbs declare **no
subjects at all**, so `_one_answer` lets the pair through, the pair sweep reads a
correct exit as something it cannot account for, and over MCP the rule is discoverable
only by making the call — which is the cost RK1518 closed once and RK1555 closed twice.

Each is one `answers(...)` call and a deleted raise, with the sentence moving into the
two `what` phrases the dispatcher reads it from. What needs care is the fifth raise
beside them: `criterion add` refuses a call naming **neither**, which is a required
choice rather than two answers — the shape argparse spells on a command line and cannot
spell over a transport where both fields exist and neither is marked required.

### §RK1610 The key that exists, one table over

Measured twice while building RK1559`s fixtures, both times by writing valid TOML in the
wrong order. `priority = ["RK1"]` after a `[files]` header is `files.priority`, and
`roadmap = 10` after `[limits]` is `limits.roadmap`. Both are refused as unknown, and
both keys exist — one table away.

The sentence RK1064 wrote is right about the case it was written for and wrong about
this one: "a typo if nothing declares it, an upgrade if a newer roadkeep does" points a
reader at their spelling and at their version, and the edit is neither. It is a header,
three lines up, that they cannot see from the message.

What makes this cheap is that the answer is already assembled. `describing.py` holds the
whole map — `_DESCRIBED` names every table and `_DEFAULTS` every key under it — for the
surface `config` prints, and the reader that composes this refusal has no route to it
only because the two were written a year apart.

So the clause is conditional: where the key names one this build knows under another
table, say which, and keep RK1064`s sentence for the key that truly is unknown.

### §RK1612 The flush nobody wrote down

Off a terminal Python buffers stdout fully and leaves stderr unbuffered, so a verb
printing an answer and then a note into one pipe emits them in the wrong order. RK1561
met it and put the note above the answer it is about; `_report` met it earlier and
carries a bare `sys.stdout.flush()` with no sentence saying why.

Swept: 34 functions in the package print to both streams and 2 flush between them. The
number is loose on purpose — most of the 34 are an answer *or* a refusal, mutually
exclusive, and need nothing. What no scan here separates is the ones that write both in
one run, which is exactly the set that needs it.

So the deliverable is the separation and not a flush everywhere. Either a helper both
callers go through, so the rule lives in one function rather than in two disciplines, or
a census naming the verbs whose success path reaches both streams — with a probe, since
a claim about the two streams is only worth what a run of it says.

The first fix having no comment is the finding, not an aside: a rule discovered twice
with nothing written down is a rule that will be discovered a third time.

## Block E — Adoption

## Block F — The plugin

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

### §RK1606 The copy that is mostly not the tool

Measured while building RK1549's removal, on this repository's own checkout vendored
exactly as `install --vendor` writes it: **22.18 MiB across 970 files**. What a launcher
runs — `src/`, `skills/`, `scripts/`, `hooks/` and the root files — is **3.79 MiB**.

The rest is `site/` at 11.78, `tests/` at 3.81, `build/` at 2.28 and `docs/` at 0.39.
`_UNVENDORED` names `.git`, `__pycache__`, `.pytest_cache`, `.venv` and `node_modules` —
history and caches — and stops there, so a built website ships to every adopter who pins
an engine.

It is not free. RK1193 put the copy inside the project so the path a declaration names
is stable, and RK1549 has just measured what removing it costs. Six times the bytes is
six times that cost, and an adopter who did commit the tree commits a website with it.

What is undecided is the rule. Naming the four directories a launcher needs is an
allow-list that goes stale when a fifth arrives; widening `_UNVENDORED` by name is a
deny-list that goes stale the same way one directory later. Which failure is cheaper is
the question, and the engine's own `__init__` is the only thing that must be right.

### §RK1611 Half of somebody else's wiring

Measured immediately after RK1560, on a project declaring `uv run serve-roadkeep mcp`:
`install`, then `uninstall`. The entry stays, as it now should, and
`.claude/settings.json` goes — it held only this command own keys — taking
`enabledMcpjsonServers` with it. Their server is declared and unapproved, which
`_merged_settings` own reasoning already calls indistinguishable from one never
declared.

So the kept row tells half the truth. It says the declaration stays; what it does not
say is that the thing which made it run does not.

Three answers and the choice is the argument. Keep the approval, which means keeping a
settings file for one key on a project that has otherwise finished un-wiring. Take it
and say so in the same row, which is honest and leaves work. Or ask whether un-wiring
should reach a declaration this command left alone at all — the reading RK1560 settled
for the file may settle this one too, one key over.

What decides it is whether the approval is ours or theirs. We wrote it; it approves
their server.

### §RK1619 The other end of the same f-string

RK1564 narrowed the sweep to the **first** call in an `Answer` f-string, on the ground
that the note is what the site is for. That reading is exact against the failure it was
filed for, and inexact in the other direction for the same reason: a helper called
*before* the composer takes the kind's name, and the note that follows goes undeclared.

Nothing writes such a site, and the shape is not live in the way the suffix was — `_now`
is a clause three composers already end with, while nothing here opens a note with a
helper. So this is smaller than RK1564 and files as an idea.

What would make the reading exact costs nothing extra: the note is the interpolation
after the literal ending in `\n\n`. That is what appending a paragraph *is* — a blank
line, then the paragraph — and it is the fact `_advise` writes at all four sites, rather
than a rule about which call comes first. It reads a separator the module already
spells, so it is neither a naming rule nor a list of exempt helpers, the two answers
RK1564 ruled out for rotting.

Against it: it binds the sweep to a literal, and a site composing that separator
differently reports no kind at all — a silent miss where today's reading gives a wrong
name. Which failure is preferable is the question, and it turns on whether the four
sites are the population or a sample.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
