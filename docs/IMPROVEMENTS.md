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

### §RK1655 The design a reopen owes

A dismissal carries no design section — that is what a dismissal *is*, the claim being
that no work was filed. So the line `reopen` places points at `§<id>` and nothing
answers it, and the gate reports `ref.unresolved` on every single reopen this tool will
ever perform.

`add` met the same problem and closed it: `--section <title>` writes the rationale in
the same transaction, and without it the follow-up is named in the write's own report
rather than left to the gate. `reopen` has neither half — no flag, and no `needs` row
saying what is owed.

The state is not wrong. A finding that has just become real has a design still to write,
and inventing one would be this tool writing prose (L4). What is wrong is that the write
says nothing about it: the caller reads a clean answer, the gate reports a finding on
the next run, and the two are the same fact arriving twice.

**So the flag and the sentence, both from `add`.** `reopen <id> --section "<title>"`
with the prose on stdin writes the section in the transaction that files the line, and a
`reopen` without it reports the anchor nothing answers — which is `Insertion.needs`,
already built, and already the shape every other door that leaves a pointer owing uses.

## Block C — Query

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

### §RK1650 Where a read may say no

*Reading is never refused* is a real rule here and it is stated four times, each about
one verb. `block list`'s docstring says a project with no block answers rather than
refuses. `criterion list`'s says a project that has not opted in prints an empty answer,
**because a read that refused would leave the caller unable to discover that the list is
the thing they have not declared**. The guard prints the sentence to an agent that tried
to hand-edit a governed file, and `budgeting` measures its width as part of that advice.

RK1608 added the first exception, deliberately: `pick --have <word>` refuses where
`[requirements] declared` names a vocabulary the word is not in, because that is a
caller who typed something this project cannot mean — and it stays a *row* where the
project declared no vocabulary at all, which is the discovery case the rule protects.

So the rule as stated is now false, and the distinction that makes it right is written
in one verb's docstring. Forty verbs are read-only; nothing says which of them may
refuse or on what grounds.

The shape is a sentence somewhere every one of them can be held against, and the
candidate line is already visible in the two halves: a read refuses a caller who named
something the project's own declarations exclude, and never a caller asking about
something the project has not declared at all. Whether that is the whole rule is what
the reading has to find out.

### §RK1651 The complement nothing checks

`test_configured` reads the package three ways for one rule. `_values` takes every
string a module uses and drops what a caller is shown. `_shown` takes exactly those and
nothing else — its docstring says *the complement of that function's exemption, so the
two cannot drift apart*. `_composed_values` reads the f-strings that build a command.

Nothing holds the claim. RK1609 changed what two of the three read — `_shown` now joins
an f-string's parts, `_composed_values` now asks about three value kinds instead of one
— and whether the complementarity survived was answered by measuring it once, by hand,
after the change. It did: zero nodes are read by both. That is a fact about today and
about nothing else.

The measurement is cheap and the property is one line: over `surface.modules`, the pairs
`_values` reports and the pairs `_shown` reports do not intersect, and together they
cover every string constant outside a docstring. The second half is the one that matters
more — a string neither reads is a value both exemptions let through, and that is the
shape RK1558 and RK1609 were each one instance of.

What needs deciding is whether the third reading joins the property or stays apart. It
answers a different question — *does this f-string build a command* rather than *is this
string a value* — so a partition over two and a claim about the third may be the honest
shape, rather than one property pretending all three tile the same set.

### §RK1653 The exemption wider than the collision

`test_advisories` sweeps the suite for a test asserting over **every** note the gate
reports rather than the one it is about — unpacking `(note,) = report.notes`, comparing
it to `()`, indexing it. The sweep matches an attribute called `notes`, and duck typing
means several objects answer to it: `NOT_A_REPORT` is the declared exemption list, on
the stated argument that an exemption nobody can see reads exactly like a rule being
kept.

It is now three rows and each is a whole **module**. `blocking.Merged` and
`blocking.Closed` carry a role-to-line-count mapping, `describing.Shape` a
table-to-sentence one (RK1603), `installing.Removal` what an un-wiring changed but kept
(RK1611). Five classes, one of which is a gate report — and the price of saying so is
that no assertion anywhere in `test_blocking`, `test_describing` or `test_installing` is
swept any more.

That is wider than the collision by a lot. The rule is about a *name reached from a
Report*, and the exemption is about a file.

Two ways in. The sweep already follows one step of dataflow — `_bound` finds names
assigned from a bare `.notes` — so it could ask what the receiver is:
`lint(config).notes` and `report.notes` are the shapes it is really about, and
`removal(project).notes` is not. Or the exemption stays a declaration and narrows to a
symbol rather than a module. Which is cheaper depends on how many receivers the suite
actually spells, and that is one grep.

### §RK1656 The answer a dismissed target has none of

`Backlog.resolve` reads the roadmap, the ledger and the deferred store, and a dep naming
an id none of them holds is `deps.unknown`: *in neither the roadmap nor the changelog,
so nothing can say whether it is done*. The dismissed store makes that sentence false —
it says precisely what was decided, and names the premise under which it stays decided.

RK92 is the same finding one store earlier. Before it, a dep on a paused line read as a
missing id: the gate reported it, `pick` could not rank the line waiting on it, and the
fix was a fifth `DepStatus` plus a `blocked-paused` readiness. The seventh role arrived
without the sixth.

What it costs is smaller than RK92's and is the same shape. Nothing *should* depend on a
dismissal — the entry is a finding nobody filed — so the honest answer is not
`DEFERRED`'s: a dep on one is work waiting on something this project decided not to do,
which is closer to `deps.retired` than to a pause. That distinction is the design:
whether the resolver gains a sixth status or the existing unresolvable branch gains a
second sentence.

**The measurement first.** Neither adopting corpus declares this store yet, so the
population is this tool's own suite — which is exactly the state RK1084 found for the
pair it wrote a rule for anyway, on the argument that a contradiction the format can
express should not be silent.

### §RK1657 The premise nothing prices

`budget <id> --defer` exists because a pause's reason is not held to `[limits] why`: the
door wraps it around the design the store carries forward, so what refuses it is the
rendered line, and an author composing to the field's number was composing to a figure
nothing enforced.

A dismissal wraps its premise by the same rule and for the same reason, and both fields
it carries are new — so the gap is wider here than it was there. `budget --defer` at
least prices a line that already exists; there is nothing to price a dismissal against,
because the entry does not exist until `dismiss` has been refused.

That is what makes the subject different rather than a copy. `--defer` takes an id and
reports what the line leaves the reason; this one takes no id, and what it prices is a
**shape**: the structure of a rendered dismissal, the symptom, and what the wrapper
costs before a premise is written. `budget --block <x>` already answers that shape for a
line `add` would write next, so the question is whether this is a flag on that read or a
subject of its own.

**Measured before it is offered.** The wrapper is 14 characters here against the pause's
14 — the same width by coincidence rather than by rule, since both are prose this
package chose — so a subject that quoted one number for both would be right today and
wrong at the first rewording of either.

### §RK1661 One word, two populations

`lint --json` carries one `notes` entry per address, deliberately: a consumer acts per
address, which is why the fold RK1565 shipped was left out of that register entirely.
`cost --notes --json` carries a `notes` list too, and since RK1620 its entries are the
*blocks* the terminal prints — five stale surfaces are five there and one here.

Both are right about what they answer. What is wrong is that they answer under one word:
a consumer holding both, which is any tool reading the gate and pricing it, joins
`notes` to `notes` and gets two counts of one run with nothing in either payload saying
they are different questions.

RK1620 added `folded` beside the figure for the reader who takes the number away, and it
is the half that makes this recoverable rather than the half that fixes it: a consumer
would have to know to add the surfaces back before the two lists compare. The keys are
what a client reads first, and a name shared across two answers is a join somebody makes
without checking.

**Which of the two moves is the question.** Renaming the census's list — `blocks`,
`printed` — says what it is and leaves the gate's untouched; adding the block count to
the gate's entries would make the two joinable and grows a payload every turn pays for.
Neither is obviously right, and the measurement that decides it is whether anything
joins them today.

## Block D — The gate

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

### §RK1644 The guard that reads characters

RK1542 refused a second site recovering `superseded by <id>` by hand, as a regex over
lines matching four string methods. `reverting` did not use one of the four — it
compiled `\(superseded by ([^)]+)\)` — so the guard read that module as clean for the
whole of RK1542's life. Widening the pattern to `re` then matched `reverting`'s own
docstring, which quotes the regex it had just stopped using: a sentence recording why a
coupling went is not a coupling, and a scan over characters cannot tell them apart.
RK1602 rewrote it to walk calls, where the question does not arise.

Both failures are properties of the reading, not of that rule. Twenty-two guards over
this package's source already read the AST — `test_shadowing`, `test_importing`,
`test_invariants` — and nine read the text. `test_document`'s is the same shape exactly:
it looks for `.block(` in a module's characters, so a docstring naming the method counts
as a second caller.

What is undecided is which of the nine are wrong. A guard whose subject really is
*characters* is right to read them — a marker codepoint appearing anywhere, a project's
own value in a help string — and converting those would narrow a rule that is
deliberately wide. So the work is a reading per guard, asking whether its subject is a
code shape or a byte, and the population is nine.

### §RK1645 The second list nothing promised

`tests/test_payloads.INSIDE` says what its docstring says: *the keys inside the one
object each of those carries a list of*. One per verb, which was true of every payload
until `config`, and `config` now carries three — `keys`, `tables` and `fixed`.

RK1603 met the limit and worked around it, adding `BESIDE` for `tables` and a second
parametrized sweep beside the first. That is two tables and two tests for one claim, and
a fourth list would want a third of each. What it did not do is notice the one already
there: `fixed` has been in that payload since RK1381, six keys per row — `name`, `at`,
`sample`, `percentile`, `reading`, `why` — and neither `PROMISED` nor `INSIDE` names it.
A consumer reading `fixed[0].reading` is reading a field nothing here holds, which is
exactly the breakage these tables exist to make red.

So the shape is one question and the population is one payload. `INSIDE` could take a
tuple of lists per verb rather than one, which folds `BESIDE` back in and makes `fixed`
a row somebody has to fill; or the two could stay apart and `fixed` get a third. What
decides it is whether *the object a payload holds a list of* was ever the right singular
— the editor host reads two of `config`'s three, and the promise is about what a reader
outside this process depends on.

### §RK1646 The guard that stops at the package

RK1604 folded `config.has(role) and config.path(role).is_file()` into `Config.on_disk`
at 41 sites and wrote the sweep that keeps it folded. That sweep reads
`surface.modules()` — the package — and stops there. `tests/test_corpora.py:384` and
`tests/test_exporting.py:744` still spell the pair out, and nothing reports them.

RK1542's guard is the precedent and it reads both: `modules()` for the package and
`suite()` for the tests, on the argument that a second spelling anywhere is the
coupling. Half of that was copied. It is not obvious the halves deserve the same rule —
a test may reasonably ask the question the long way where it is *about* the two halves —
but two sites that simply predate the fold are not that, and neither is a rule silent on
which they are.

Widening it needs RK1644's reading first. The sweep matches lines, so the third hit
today is `test_config.py`'s own docstring quoting the idiom it refuses: the prose that
records why the fold happened would be reported as the thing that undid it. That is the
same two-sided failure RK1602 met and the reason its guard walks calls instead — so this
is one task with that one, or it is a rule that has to carry an exemption for the
sentence explaining it.

### §RK1647 The scope walk written three times

`composing.census` walks a module's syntax to answer *which function is this call in*.
`composing._owners` walks it again to answer *which function is this line in* — RK1605
added that one. `test_budgeting._parts` walks it a third time for the same question
about `Part` calls. Each builds its own name stack, pushing on `FunctionDef` and popping
after.

Two of the three push `ClassDef` too and join the stack with a dot, so a method inside
`Created` is `adopting.py:Created.stated`. The third pushes only functions and takes
`stack[-1]`, so the same method is `stated` — a name several classes in one module can
share. That is not a style difference: it is the third walker answering a slightly
different question under the same shape, which is how two readings come to disagree
without either being edited.

`tests/surface.py` is where this belongs and says so: it exists because a survey
deriving its own view of the layout agrees with every other one until the layout moves
(RK496). It already holds `modules`, `address`, `names`, `suite` and `claimed` — every
shared reading of the tree except this one.

What is not settled is the shape it should take there. A mapping from line to address
serves `_owners`; a visitor hook serves the two looking for a particular call. One
reader answering both is the question, and three call sites is a small enough population
to design against rather than guess.

### §RK1649 The choice that has to be made

`answers(...)` declares that two flags are two answers, and `_one_answer` refuses both
together before a handler runs — on the CLI and over MCP, from one declaration. What it
cannot say is that one of them is **required**.

`criterion add` needs that: it writes the bullet, so there is no lead on file to resolve
an address from, and a call naming neither `--block` nor `--task` has nowhere to put the
line. `_required_address` raises it inside the handler, which is the shape RK1607 took
out of four other verbs for three reasons that all still apply here — `_one_answer`
never sees it, the pair sweep reads a correct exit as unaccounted for, and an agent
meets the rule by making the call.

Argparse spells this and cannot help. A `required` mutually-exclusive group refuses on a
command line and says nothing over a transport where both fields exist and neither is
marked required, which is why no verb here uses one: measured across 82 leaf verbs, zero
required groups and sixteen `answers(...)` declarations.

So the shape is a flag on the declaration — `answers(parser, ..., required=True)` —
enforced beside the pair it already checks, and published into the served schema so the
transport carries it too. The population is one verb today. Whether that is enough to
declare against, or whether one raise with a good sentence is the right amount of
machinery, is the same question RK1555 answered the other way for `--prefix` beside
`--sections`.

### §RK1652 The edit with no door

`govern` was built on one argument: every table in `roadkeep.toml` except the four it
writes was a hand edit, *which over the served surface is no edit at all*. RK1610 wrote
a new message straight into that gap — `misplaced key 'files.priority': this build
declares it as \`priority\` at the top level — the header above it is what to move` —
and the move is a hand edit with no verb behind it.

Measured: `describing.TABLES` declares 20 tables, `governed` writes 5, `declare` opens a
role's `[files]` entry, and **15 tables no verb reaches**. A misplaced key in any of
them is a refusal naming an edit precisely, in a file this tool otherwise owns, to a
caller that may have no editor.

It is the sharper case rather than a new one: the same is true of every hand edit those
15 tables need. What RK1610 changed is that the tool now knows the exact repair — which
key, which header, from a map it already prints — and still hands back prose.

So the shape is a verb that moves a key between tables, and the question is its bounds.
`govern` refuses a key with no reading behind it, on the argument that a name or a path
is a decision and not a measurement; moving one is neither — it is a correction to a
placement the tool can derive whole. Whether that makes it `govern`'s, `declare`'s, or a
door of its own is the design.

### §RK1654 The eight nobody separated

RK1612 put the stream ordering in `refusing.beneath` and pointed its two known callers
at it — `cli._may_offer` and `adopting._report`. What it did not build is the other half
its own design named: the separation between a function that writes an answer *or* a
refusal, which are mutually exclusive and need nothing, and one that writes both in a
single run, which is the set that needs the flush.

Measured after the repair: **10 functions print to both streams in one body and 2 go
through `beneath`**. The eight are `cli._rendered`, `linting._report_rows`, four in
`verbs/adopting`, and three reads in `verbs/querying`. Most are almost certainly the
exclusive shape. Nothing says which, and reading them one at a time is what the census
exists to replace.

The guard shipped with it does not close this. It refuses a `sys.stdout.flush()` written
anywhere but the helper — so the *repair* cannot be re-implemented — and says nothing
about a plain `print(..., file=sys.stderr)` following a `print(...)`, which is the
defect itself. A rule that catches the fix and not the fault is the shape RK1602's guard
had.

What the reading needs is a run, not a scan: whether a body reaches both streams on one
path is a question about execution, and the eight are few enough to drive.
`tests/test_answers` now has the subprocess that merges the two pipes, which is the
instrument that was missing when the rule was found the first two times.

### §RK1660 The other fold

RK469 folded findings sharing a sentence and RK1565 folded notes by copying that loop
one list over. RK1620 then lifted the note half into `linting.runs`, because a *second*
reader needed it: `cost --notes` was summing one row per note while the report said a
run of them once, and the only honest fix was one fold with two callers.

The findings' half stayed a loop inside `_print_findings`. So the rule — group by what
the emitter declared shared, runs of two or more, addresses under the sentence — lives
in two places, and the pair has already drifted: notes key on `(code, shared)` and
findings on `(code, shared, file)`, a real difference with a stated reason and also the
shape a copied loop takes the day somebody changes one.

**What makes a lift worth it is the second reader, not the duplication.** A fold with
one caller is a printer; RK1620's argument is that a figure claiming to be what a
session pays has to read what was printed. Nothing prices a *report* — the findings'
side has no census — so that reader does not exist, and lifting for symmetry alone buys
indirection against nobody.

So the decision is which this is: a duplication to remove now, or a lift that waits for
the read needing it. What settles it is whether a report is a cadence — a clean run has
no findings, and a backlog with standing debt prints the same one every run.

### §RK1662 The other two facts about the session

`_ABOUT_THE_SESSION` is `("install.stale", "install.absent")`, and its sentence says
these are "about the reader's own tooling rather than about this project's files".
`gate.behind` and `engine.disagreement` answer to exactly that description — one says
the copy judging is behind the pinned one, the other that the code answering is not the
code on disk — and neither is in the set, so neither reaches the summary.

RK1482's argument is about the reader: a session read past three of these for hours and
only looked when it ran out of roadmap work, so the count went where somebody skimming
one line a run would meet it. That reader skims past `engine.disagreement` the same way,
and this repository's own gate emits it on every run with uncommitted work.

The split may still be right. A surface behind is a **count** — five of them are one
sentence and a number — while a disagreement is one note whose whole content is which
copies differ, so a summary clause would either repeat it or say `1`, which is the
clause a reader stops seeing.

What is missing is the sentence saying so. The set's comment argues the pair *in* and
never the other two *out*, so a fifth session note lands in the same silence: RK1621
re-took this line's count against a fold that had changed under it, and the set it reads
was never re-taken at all.

## Block E — Adoption

## Block F — The plugin

### §RK1648 The bytecode the check leaves behind

`vendor` verifies by running `<copy>/scripts/roadkeep.py --version`, which is RK1193's
fourth rule and the one that makes picking by version mean anything: the evidence is the
copy answering. Running it imports the package out of the copy, and Python writes
`__pycache__` beside every module it loads.

Measured while building RK1606: the copy as written is **3.89 MiB across 90 files**;
after the verification it is **7.24 MiB across 147**, of which 60 files and 3.35 MiB are
bytecode nothing asked for. The proportion is what makes it worth a line — the check
costs almost as much as the artefact.

It predates RK1606 and was invisible beside 22.46 MiB. It is also not a bug: the
bytecode is valid and is what the launcher would write on first use anyway. What it is
is an artefact that stopped being the size its own rule says. **No supported Python
API.** does not reach it — that non-goal is about what this tool offers a caller to
import, and this is what CPython writes for its own loader.

Three ways out and they differ in what they give up. `-B` or `PYTHONDONTWRITEBYTECODE`
on the verification subprocess leaves the copy as written and makes the first real run
pay instead. Deleting `__pycache__` after the check is a second sweep over a tree just
walked. Or the figure is simply stated — `install --vendor` reports what landed, and a
report saying 7.24 when the rule says 3.89 is the part that misleads.

### §RK1658 The sample that was never counted

RK1619 read the note as the interpolation after `\n\n`, and kept the first-call reading
as a fallback so a site spelling no blank line still reports a name. That fallback is
what makes an undeclared kind fail loudly instead of passing in silence — and it is also
what makes the opposite failure invisible.

A site that *stops* spelling the separator changes the answer a caller reads: the note
runs on from the text instead of arriving as a paragraph. Under the fallback the sweep
still names the kind, `NOTES` still matches, and every test in the suite is green. So
the one property the reading rests on — that appending a paragraph is what these four
sites do — is asserted nowhere.

The design's own last sentence asked whether the four sites are the population or a
sample, and the answer shipped was *a sample plus a fallback*. Three tests construct the
shapes by hand and none of them reads `serving.py`.

**So count them.** The sweep already walks every `Answer(f"…")` site in that module;
what it does not say is how many took the primary reading and how many the fallback, and
the second number is a property with a right answer today: zero. A test asserting it is
one line beside the census, and it fails on the commit that drops a separator rather
than on the session that notices the note reads wrong.

### §RK1659 The separator that could be a call

`_advise` writes `Answer(f"{text}\n\n{_kind(…)}")` four times. The blank line is the
same fact each time — *this note is a paragraph after the answer* — spelled as a literal
in four places, which is the duplication this package removes wherever it finds one.

RK1564 and RK1619 are both what that costs. Each read the f-string for the note's
identity, each was exact against the shape it was filed for and inexact against the
mirror one, and RK1619's answer still needs a fallback: a site spelling the separator
differently gets the older reading, because a literal is what the sweep matches on.

**One helper dissolves the question.** `_appended(text, note)` composes the blank line
once, and the site becomes `Answer(_appended(text, _landed(changed, root)))` — where the
kind is the second argument, not the call after a literal, not the first call in an
f-string. There is no separator to spell differently, so there is nothing for a fallback
to be about, and the census reads an argument position rather than a string this module
happens to write.

Against it: it is a wrapper around a two-part f-string, which is the kind of indirection
that buys nothing where a rule does not already turn on it. Here one does — twice — so
the test is whether the reading gets simpler, and it does: one call site shape, no
literal, no fallback, and the suffix `_now` composers already carry stays exactly where
it is.

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
