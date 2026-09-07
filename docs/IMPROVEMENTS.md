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

### §RK1622 The shape no test asks a corpus for

RK1566's design named Turing for a property — "a long backlog against a ledger that is
mostly one migration" — and the pin holds the opposite: three open lines against 901
entries, this repository's own shape. The design was written and filed on that sentence,
and the measurement it asked for was the first thing to read it.

Nothing here could have disagreed. `corpora.py` says in prose what each corpus supplies
— block deps, an outline scheme, an unmarked ledger, ranges — and each is a shape some
test names, so a corpus that stopped carrying one goes red or skips. A **ratio** is not
that kind of shape: no test asks for it, nothing reads it, and a paragraph is free to
assert what it likes about the pinned trees.

The advisory in `test_corpora.py` is the near miss. It warns when the pin has fallen
behind, and the warning during this task said `roadmap 3 → 0` — the whole answer,
sitting in output nobody reads until something fails.

What is missing is a shape a design can be checked against: how many open lines and how
many delivered entries each pin holds, and the same per block. Not an assertion about
somebody else's backlog — those numbers move and should — but a **reading**, so a claim
about which corpus exhibits which ratio is answered rather than remembered.

### §RK1623 The corpus measured beside the one that is ranked

`add` builds the corpus its volunteered rows are ranked against: the block's delivered
entries, then the block's other open lines, in that order — and the order is
load-bearing, because every measurement of the split counts an index past
`len(delivered)` as the open half taking a row.

Three tests in `test_ranking.py` rebuild that list by hand. RK1527's two did it to
measure the window, RK1566's `_slots` does it again, and none of them calls the code
that composes it. So the property being measured is *a* corpus of that shape rather than
**the** corpus `add` ranks, and a change to what `add` includes — dropping 🗑 entries,
ranking a second block, ordering the halves the other way — leaves every figure here
passing about a composition production no longer has.

Not hypothetical in kind: RK1495 is exactly that change, made once already. It doubled
the corpus, and the reason the window needed re-measuring was that nothing had been
holding the two halves together.

The fix is a seam and not a fixture. What the tests want is the block's corpus as a
value — the two lists and the boundary — which `authoring` computes inside the function
that also ranks and counts. Lifting it is the argument RK1491 made about `disagreements`
and RK1524 about `composed`: a figure taken off the function the caller uses cannot
drift from what the caller gets, and one taken off a rebuilt copy drifts silently, the
day somebody edits the original.

### §RK1624 The read that runs once and is never available again

RK1567 measured the gap and closed the sentence, leaving the third way out it named: a
read whose subject is a block's **whole corpus**. The rows an `add` volunteers are the
only place that ranking is ever computed, and it is computed once, inside a write.

RK442's guarantee is that a bounded answer says where the rest are. The row does name
two doors — `delivered <block>` for the deliveries and `list --block <block>` for the
open lines — and neither of them ranks. So a reader who suspects the fourth-nearest is
the duplicate has one listing ordered by the ledger and one by id, and the order that
put three rows in front of them cannot be asked for again at any width.

That is not a small residue. Half the insertions here show a row `delivered --near`
cannot reach, and those are exactly the rows the widening was for: the other session
filing this defect this morning. The one read that would find it is unavailable to
everyone who did not just run an `add`.

What it wants is one verb over the block, ranked, each row saying which half it came
from — the marker already does. `delivered --near` widened answers outside its own
subject; `list --near` is the same read under the name of the verb that orders by id.
Which spelling is right is a question about the surface and not about the ranking,
`authoring` already holding the arithmetic behind one call.

### §RK1625 The silence the flag was declared to prevent

`Unclosed.searched` says what it is for: *`()` means two different things otherwise, and
a checkout with no history reading as a clean backlog is the silence RK10 is about.*
Nothing in the package ever sets it False. The walk returns its empty answer on
`HistoryUnavailable` exactly as it does on a backlog with nothing open, and the caller
constructs the record with the field at its default.

So the sentence a reader gets on a tree with no git is `0 of 0 open line(s) already have
commits naming them`, and `--json` says `"searched": true`. Measured on a scaffolded
project holding one open line: both halves are wrong — the count because the rows never
came back, and the flag because the one state it exists to report is the one that
produced it.

`Cited` and `Gap` get it right, which makes this a slip rather than a shape: both are
built by a producer that knows whether the history answered. This record's producer
knows too — it is the branch catching the failure — and drops it.

The fix follows RK1568's split. `Sweep` is what the walk returns and `Unclosed` what the
verb prints, so the flag belongs on the first and passes to the second, as the
incidental reading now does. The count wants the same: how many lines are open is a fact
about the roadmap, knowable with no history, so a report that could not walk should
still say how many lines it cannot speak for.

### §RK1628 The premise a later ship deleted

RK1571 and RK1574 were filed on one day against thirty-one composer rows that were a
work-list. RK1599 landed and emptied it, and `test_composing` now asserts that no row is
`unreached`. Neither line said so. `pick` offered RK1571 first, as the lowest ready id,
and what it proposed was a field that would be empty on every row.

Reading the section is what found it: 245 words of design against a state that no longer
exists. That is the cost this tool exists to avoid — the check was opening the source
the design argues about, one idea at a time.

Nothing here can judge a premise and nothing should try (L4). RK1439 is the neighbour
and it does not reach: it names the shipped entries whose sentences cite an open id, and
RK1599's cites neither of these. What is derivable is the distance — `origin` names the
commit that proposed a line, and the ledger records every entry under its block in
order. An idea filed before twenty entries landed in its own block is not thereby wrong,
but it is the line whose design a picker should re-read before starting.

So `pick`'s `because` carries it and `show` beside the pointer: proposed at that commit,
with that many entries recorded in the block since. A count and not a date, which is the
non-goal one field over — the question is how much has happened under this line, and an
ordinal answers it where a calendar would not.

## Block D — The gate

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

### §RK1620 The number the fold does not reach

`Noted.here` sums one `Part` per note and calls that "what a clean run costs now — the
per-commit and per-turn figure". Since RK1565 a run of notes sharing a sentence prints
once, so the sum is what the gate *composed* and no longer what it *said*: five stale
surfaces are 1,149 characters to this reader and 358 on the terminal.

Invisible here, which is why it files as an idea rather than a defect. This repository's
gate emits `read.priced` alone and a single row folds to itself, so every number `budget
--notes` prints is still exact. The population it is wrong about is every wired project
whose surfaces are behind — the one the fold was measured on.

The fix is not a second reading of the report. `_print_notes` already knows the answer:
the fold is `(code, shared)`, and a group costs one sentence plus its addresses. What
`note_cost` wants is that grouping over the rows it prices — a call, not a parser.
Pricing the rendered text would be a second reader of what the gate composes, the drift
`disagreements` was lifted out of the gate to end.

What to decide first is whether the figure follows at all. `here` claims to be what a
session pays; a second figure for what was composed is the number nobody reads. The
honest shape may be one number and a line saying which rows folded, which is a judgement
about the report rather than about the arithmetic.

### §RK1621 A reason that stopped being true

`_wiring_line` argues for itself in one clause: "Not a second check and not a second
sentence: the notes carry the paths and the door, and this carries the count." That was
exact while a note was one row per surface — the count existed nowhere else in the
report, so the summary was the only place a skimmer could meet it.

RK1565's fold gives the note row a count of its own. A wired project behind on five
surfaces now reads `5 surface(s)  install.stale …` where the notes are, and `5 wired
surface(s) behind this engine` on the summary — the same number, twice, four lines
apart.

Small, and not obviously wrong: the two readers are different, one skimming a line and
one reading the notes, and the summary still adds what the fold cannot — how many of the
five are missing entirely rather than behind. So this is a question about the sentence
and not a bug to be closed by deleting one of them.

What it costs is the argument, which is the part that rots. The clause above is now a
reason that has stopped being true, and a comment stating a fact the code no longer has
is worse than no comment — it is the one a later reader trusts. Either the summary earns
its count on a ground the fold does not take, or the fold's row drops the number the
summary already carries; whichever way, the sentence beside it says why.

### §RK1626 The sweep CI has never run

RK1569 separated what this build claims from what somebody else's checkout happens to
hold, and the sibling sweep has the same seam in the other direction. The field half
reads this repository's fields **and** both corpora, and calls `require` on each corpus
inside the loop — so a machine without Shio skips the whole assertion, including the
2,246 symptoms and whys of our own two governed files.

Those are the population the rule is most about. `docs/` is this format's conformance
fixture, and whether a field here has grown a mangled run is a claim about this build
alone, answered by files in the tree. CI has neither corpus, so the sweep that would
catch the signature beginning to match ordinary prose has never run there.

The bar the skip protects is met without them. `assert len(fields) >= 2000` exists so a
survey covering nothing cannot pass, and this repository carries 2,246 alone — so the
non-vacuity `require` stands in for is a property of the local files. What the corpora
add is scale and other people's vocabulary: worth having, and not what makes it honest.

So the shape is the one RK1569 just drew: read every corpus that is present, name which
were read, and keep the red for the fields. A corpus that is absent contributes nothing
and skips nothing — the same rule `present` already gives every other reader here,
applied to the one sweep that reached for `require` instead.

### §RK1627 The register the composed fields have not got

RK1570 found the block title by being told where to look. What it could not have found
is the next one: nothing enumerates the fields a caller composes, so "which of them has
a validator" is a question answered by remembering.

The population is small and already spelled. A symptom and a why are
`Schema.validate`'s; a section title and body are `sections`'; a non-goal's lead and why
and a criterion's are their families'; a block title was nobody's until this task. Every
one is a string a caller passes as an argument and this tool writes into a governed file
— a property a sweep can read, the `add_argument` declaring each flag being where every
one of them enters.

The register for it exists twice over. `test_backstop.py` holds every code a write
refuses against what the gate says about that state; `tests/composing.py` enumerates
every site that composes a command. Both are totals over a population read from the
source, and both caught something the first time they ran. Neither asks the question one
field over: which composed fields reach a file, and which pass a validator on the way.

A sweep would have named the block title on the day `block add` was written. What it
costs is deciding what counts as a composed field — a flag whose value is written
verbatim, most likely — and that decision is the whole task, the sweep after it being an
`ast` walk of the same shape as the two already here.

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
