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

### §RK1632 The field every line leads with, and the pipe it has not got

RK329 established that every prose argument reads stdin on `-`, so a sentence carrying a
backtick or an apostrophe never meets a shell. RK1187 applied it to `restate --symptom`,
whose help says so today. `add --symptom` was not moved and its help does not: the value
arrives as argv or not at all.

So the field every task line leads with is the one field with no pipe, on the verb that
writes it first. `add --why` takes `-`, `add --section-body` takes `-` and a path, and
between them sits a symptom that has to survive whatever quoted it. The failure is
silent in the direction that matters: a `-` handed to it is not read as a pipe, it is
measured and stored as a one-character claim, which is the exact landing RK1187 was
filed about one verb over.

RK1474 recorded the same class from the other end — a value passed ASCII-only to survive
a shell is bytes that never arrived, and permanent in two files at once. A caller
writing in a language with accents meets this on the first line it files, and a client
composing argv from a text box has no shell to blame.

What closes it is the door the sibling verb already has, spelled the same way in the
same place, and a test that asks the parser rather than the help text which arguments
read a pipe.

### §RK1634 The last look at a section, at the moment it goes

A ship deletes the rationale section in the same transaction that writes the ledger
entry. Three flags carry what was durable in it — `--superseded-design` for the half the
code moved under, `--recorded-in` for the half belonging beside the code, and
`--decides` for the constraint belonging to no file. All three are optional, and the
call that deletes mentions none of them.

So the only answer arrives after the fact: the section is gone and the entry says
nothing about having held one. The evidence a caller needed was in a section they were
not shown, in a session about to end.

What is wanted is not a required flag. Requiring `--decides` compels a sentence where
there may be no decision, and filler in the one store with no deletion verb is permanent
— which is the ADR curve this format refuses. `--checked` settled the same class one
flag over: a criterion nobody names reads as unchecked, and silence was accepted there.

The asymmetry arguing for more here is that a criterion survives a ship and a section
does not. So the cheap form is a read and not a gate: the call names what it is about to
delete — the title, the word count — and the three doors, before it writes. Whether a
project may demand the stronger form, and whether an explicit `nothing survives` is an
assertion worth having or ceremony, is what this design has to weigh.

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

### §RK1630 Which project, and which build, an answer is about

`lint --json` leads with `root`, and `config`, `commands` and `engines` each lead with
`version`. The reads a client actually loops over — `list`, `show`, `brief`, `stats`,
`export`, `pick`, `deps`, `budget` — carry neither, and every path on them is relative
to a root the payload never states. Run from a subdirectory the answer is identical, so
a caller that passed `-C` cannot join what it got back to what it asked about.

That is survivable for one project in one terminal, where the caller is standing in the
answer. It is not survivable for a client holding many at once: three checkouts may
answer for three projects, `engines` says outright that they are allowed to differ, and
what the client then holds is eight payloads with nothing on them saying which
repository or which parser produced each. A key renamed between builds reads as a value
that changed.

Block G's own criterion is that a payload is asserted here as an outside client reads
it. An outside client reads it out of a subprocess whose directory it chose, and the two
facts it needs before it can trust a single field are the two `lint` and `config`
already print separately.

What this does not ask for is a new verb. Both keys exist and are spelled; the question
is whether every `--json` read leads with them, and whether `root` is absolute where the
`file` beside it is relative to that root.

### §RK1631 The probe, and the null that stands in for it

Asking whether a path is governed has no door. `config --json` answers `source: null`,
which is a fact stated by an absence — a client branches on a null and is given no root,
no roles and no reason. `engines --json` exits 0 on a directory with no `roadkeep.toml`
anywhere above it and reports `invoke: roadkeep`, so it answers confidently about
nothing. `lint --json` is the only read carrying `root`, and it gets there by parsing
every governed file, which is a file's work to answer a directory's question.

The caller this is missing for is any client that meets a path before it meets a
project: an editor opening a folder, a gate deciding whether to run, a surface over a
machine's checkouts. Each one reconstructs the discovery rule — walk up looking for
`roadkeep.toml` — in its own language, which is the second implementation this project
exists to remove, and it is wrong the first time discovery changes.

The answer wanted is one call, cheap, that says: governed or not, the absolute root, the
roles `[files]` declares and the engine that would write. Every part of it is computed
somewhere already; none of it is reachable together, and the one signal that is
reachable is a null.

## Block D — The gate

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

### §RK1635 The reader that is the assumption

RK1498 built an instrument that runs every composed command, and sixteen sittings
emptied its work-list. It runs them through `shlex.split` and `cli.main`, which is a
Python reading of a line a **shell** is going to read — and RK1580 is what that costs:
every door was quoted with `'`, the sweep was green for a year, and in `cmd.exe` the
symptom arrived as `'A` plus seven stray positionals.

Nothing in the suite could have said so. `shlex` is the reader under test, so a line
quoted wrongly for a shell round-trips through it perfectly; the only way the defect
surfaced was a person typing the printed line into three terminals and reading the argv
back.

What closes it is not running every door in three shells — a subprocess per door per
shell, on a suite already four minutes long, and two of the three are absent where CI
runs. It is running **one**: take the door `report` prints, hand it to `cmd`, PowerShell
and `sh` in turn where each is present, and assert the argv each delivers is the argv
the composer meant. Skipped where a shell is not there, which is what `tests/corpora`
already does with its pins.

One door is enough because the quoting is one function now. `provenance.quoted` is what
every composer reaches, so a shell test on any door is a test of the rule — and the
check that no composed span carries a `'` is what carries it across the rest.

### §RK1637 The cadence the tables do not count

`cost` has seven subjects and each was filed as *the Nth cadence, and the one nothing
counted*. RK1424, RK1428, RK1491, RK1524 and RK1582 each made that argument from
scratch, each correctly, and none could say how many were left: the sentence is prose in
five docstrings and the count a number a reader increments by hand.

What is missing is the population. `USES` says what every caller of `Part` holds,
`SITES` what every composed command is, `CARRIED` what every off-shape register is —
this package answers *how many are there* with a table everywhere except about the thing
the tables are for. The seventh was found by reading a docstring and noticing prose, the
discovery method RK1498 exists to replace.

A cadence is enumerable: a text composed on a stated trigger — per connect, per turn,
per read, per refused write, per gate run, per `add` — and `cost`'s `answers` already
names all seven. What it does not carry is the **trigger**, the field that makes the set
a set: two subjects sharing one are one cadence counted twice, and a text whose trigger
nothing prices is the eighth.

So the shape is a trigger per subject beside the flag that reads it, and a sweep asking
whether every per-write composer has one. What it must not become is a limit on the
total: different surfaces are paid by different callers, and a sum charges one session
for all — the mistake `Noted` keeps `emitted` and `appended` apart to avoid.

### §RK1638 The span addressed by its own words

Both checks in `test_naming` find their prose by splitting the source on a phrase — one
for the guard's comment, one for the tool table's preamble. The span is addressed by a
sentence somebody wrote, so an author who rewords the opening clause does not break the
test: they empty it.

That is the failure the file exists to end, one level up. RK1539 was prose drifting from
its table; this is a check drifting from its prose, and it fails the same way —
silently, green, covering nothing. RK496 declared the module set once for exactly that
reason.

The guard is cheap and half-present. The tool-table check asserts the span names at
least one verb before checking any, so an empty read is a red; the collision check has
no such line, and neither says the span it took was the span it meant.

What closes it is addressing prose the way `surface` addresses a module: by the **thing
it is attached to** rather than by its own text. Both spans here sit immediately above a
named assignment, which `ast` gives exactly — `spoken` already walks source that way,
and `USES` is reached by name.

So the shape is a reader taking a module and a name and answering with the prose above
it, and every caller in `BESIDE` moving onto it. A phrase-split stays where a span
genuinely is one clause inside a longer docstring, and is then a stated exception rather
than the default.

### §RK1639 The prose a caller is handed

RK1588 swept one closed set and found two of nine reasons resting on stale figures — a
third of those carrying a number at all. That set was the honest first step, and the
general form is not cheap: most numbers in package prose are corpus measurements whose
point is being historical.

The next sets are closed too and unswept. `remedying`'s remedies, `serving`'s notes and
`guarding`'s refusals are each an enumeration this suite holds total, and each reaches a
**caller** rather than a maintainer — which makes a stale figure worse there. A
withholding reason is read by whoever edits the surface; a refusal by whoever met it.

What made the sweep cheap was the distinction and not the regex: `RK1506` is an address
and `943` is a measurement, and one line of pattern separates them. That holds wherever
the prose is reached through a declared table, which is exactly these three.

What it must not become is a rule about digits in this package. `test_corpora` quotes
pinned counts on purpose, `budgeting` quotes what a surface measured the day a limit was
chosen, and RK1530's docstring names two figures it is about. The line is *prose a
caller is handed*; outside it a number is a record, not a claim.

So the shape is that sweep over the next three tables, and a row per table saying
whether its prose is a caller's or an author's — which decides whether a figure in it is
a defect or a date.

### §RK1640 The bare verb with nothing to compare it against

RK1590 made a message's own two spellings the tell, and that is the shape RK1589 had. It
is not the shape most of the package holds: 331 messages carry 421 verb-leading spans
with no prefixed door beside them, and the mixed shape the rule fires on now numbers
zero. So the sweep is red for a regression of RK1589 exactly and silent for a door that
forgets in a message where nothing else runs.

What is undecided is whether those 421 hold any doors at all. Sampling says mostly not —
`add --section` is a flag family, `pick` alone is prose, `init` beside `adopt <file>` is
two verbs being named. But `adopt <file>` carries a placeholder, which is what a caller
pastes and a flag family never has, and that is a tell nothing has been measured
against.

The design is that measurement, and its result may be that the population is prose and
the pair rule is the whole answer. That would be worth writing down: RK1590's section
argues no scan can decide which spans were meant to be doors, and a count showing the
undecidable ones are all prose turns that from a limit into a bound.

### §RK1641 The door sweep that is really one fixture

`test_every_door_the_gate_offers_on_this_project_lands` loops over every finding a
project emits, builds the remedy, fills the blank and runs the argv — which reads as a
property over the table. It is a property over one fixture, and that fixture emits
**one** finding: `ref.unresolved`. Of the 84 rows whose kind is `fix`, `run` or
`compose`, it executes one.

That is why the same defect keeps arriving as a task. RK472 found a `section drop` the
file refuses. RK1015 measured why a door field cannot replace the kind. RK1591 found
`export --<target>` dispatched against the state that emits its own finding. Three
corrections to one predicate, each by example, with a sweep in the tree that would have
caught all three had it reached the rows.

What is undecided is the cost. Eighty-three more emitting states is eighty-three
fixtures, and most of the codes need a project shaped a particular wrong way — which is
the work, and is why the existing test settled for the findings it had.
`tests/test_doors.py` holds the other answer: a declared cross-product of states, each
door executed, and an empty cell that has to say why there is none. Whether that shape
ports here is the design, and the number to weigh it against is one, not eighty-four.

### §RK1642 The other command in the same refusal

A refused write can print two commands. RK1149's retry is the caller's own call with a
derived address in it, and RK1435's `foresee` row is the read that would have refused
the same draft without writing — `budget --why <draft>` for a `why` over its limit,
seven codes carrying one. RK1600 published the first as an argv. The second is still a
line of `said`, which leaves the payload naming the rule that refused and not the read
that would have made the refusal unnecessary.

It is one key, and the shape is where the thinking is. A `foresee` door is
**incomplete**: `<draft>` is the caller's own prose, so the argv is a template rather
than a command, which is the difference `Door.complete` already publishes and the retry
never had to say. Publishing it as `Door.payload()` says all of it — argv, what,
complete, writes — at the cost of a fourth vocabulary in one payload.

What is not settled is whether it goes beside `retry` under its own name or under the
shared `doors` list. RK1324 says one name and one shape wherever a payload publishes a
runnable command; RK1600 argued the exception, that a retry is the caller's call and not
an offer. A `foresee` read is an offer, which puts it on the other side of that line —
and makes `doors` the answer unless the incompleteness is reason enough to keep it
apart.

### §RK1643 The page that has no number

`SKILL.md` is 11,671 code units against `ORIENTATION_MAX = 13_000` in
`tests/test_skill.py`. `writing.md` is 47,404 and `asking.md` 20,500, and no test, no
`[budgets]` key and no reading bounds either. Together they are the guidance six times
over, and the ceiling is on the third of it that shrank.

RK1601 is how that reads in practice: it added 1,361 units to one page and 1,076 to the
other, both correctly — the argument being that a page's cost falls on the turn that
opens it — and nothing anywhere could say whether the page could afford them.
`roadkeep.toml`'s own comment already anticipates the shape, saying `SKILL.md` is
deliberately absent from `[budgets]` because trigger-loaded and that its ceiling lives
in a test instead. The pages are trigger-loaded one cadence further out and got neither.

What is undecided is the number and who holds it. A test is where the orientation's
lives, and it is one figure per file, which is what a page-cadence ceiling wants;
`[budgets]` is where a project's own belong, and these ship in the plugin, so a project
cannot be the one to set them. **No effort or size field.** does not reach this: that
non-goal is about a field on a task line, and a ceiling on a file this tool ships is
what `lint` holds for two others. Whether a bound helps is open — a reference refusing a
rule because it is full is the failure `agents.md`'s budget causes on purpose, and a
page's may not.

## Block E — Adoption

## Block F — The plugin

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

### §RK1629 The trim two files spell twice

RK1573 gave `scoping` a heading to open and, with it, the question `criteria` had
already answered: where does a section appended to a roadmap go? Both files now carry
the same four lines — walk back from the end while the line is blank — under two names,
`criteria._trimmed` and `scoping._end`, and the second was written by reading the first.

Nothing forced the copy. `criteria` reaches into `scoping` for `HEADING` and cannot be
reached back into, so the shared answer has nowhere to sit between them. One layer down
it has somewhere: `kernel/document.py` owns `blank`, and its docstring says why that is
public — *every writer has to reason about it*, a doubled blank being a change the
round-trip cannot catch because both spellings round-trip. The index one past the last
non-blank line is that reasoning finished, asked by every verb appending a section
rather than inserting one.

So the fix is a reader on `Document` and two call sites deleted. What it is not is a
sweep: `criteria` has two more loops walking back from a **region's** end and
`governing` and `queueing` have one each, and those answer a different question — where
one section stops, not where the file does. Folding those into the same name would be
the fold that stops folding, which is the shape RK1565 had to undo one file over.

RK1602's instance is a literal spelled twice; this is a rule implemented twice, which
the gate cannot see at all.

### §RK1633 The one write outside the layer

`declare refs` is the only handler in `verbs/` that writes a file. The thirty other
writes there are `.save()` on a record a domain module composed and validated; this one
takes `namespaced`'s `config_text` and calls `write_text` on `config.source` itself.

That is why it is absent from every count of this file's writers. RK1533 named `govern`;
RK1576's design enumerated four more and put the number at five; the AST sweep found
six. The extra one is exactly the write that does not look like a write from the domain
module's side — `namespaced` returns a string and claims nothing about it landing.

The asymmetry is the finding, not the missing check, which RK1576 closed. `Written`,
`Declared`, `Opened` and every other record here own their save: the transaction is
compose, validate, save, and a caller holding a rendered string can forget the middle
step. This one did, across two tasks looking straight at it.

So the shape is `namespaced` returning a record that saves both files, the way
`declare`'s `Retrofitted` already does, and `_refs` calling `.save()` like its thirty
siblings. The ordering its docstring argues for — prose file first, config last, so a
failure lands on the side that changes nothing — becomes a property of that save, which
is where a test holds it.

What it must not become is a `Document` for the config: that file is TOML, its
round-trip is `readable`, and a parse-render pair would drop the comments a scaffold is
made of.

### §RK1636 The import a def silently ate

RK1581 added `from roadkeep.config import declares` to `installing`, which already has a
public `declares` of its own — about a documentation page, returning `(str, str)`.
Python resolves that silently: the later `def` wins, the import is dead, and `plan`
called the wrong function. What surfaced it was a `TypeError` inside `os.path.relpath`,
three frames from the name that was wrong.

It cost ten minutes and it was luck: the two return types are incompatible, so it
raised. A collision between two functions that both return a string is a wrong answer
with a green suite, which is the shape this package spends its docstrings refusing.

The scan to host it already exists. RK1194 reads every module for a dead import — AST
for annotations, symtable for the rest — and reads *this* one as used, because the name
is called; just not the imported one. A module-level rebinding is the case that reading
has no branch for, off the reader it already uses.

What it must not become is a style rule about shadowing. A local named `found` over a
builtin is not this; the finding is narrow, which is what makes it checkable: **a name
this module imported and then defined**. That is never intentional — an import nothing
can reach is a dead line or a bug, and both want removing.

`installing` keeps the alias RK1581 gave it: renaming either public function is a change
to a surface, for a reason no reader could see from the name.

## Block I — The documentation area (what an adopter reads before there is a session to ask)
