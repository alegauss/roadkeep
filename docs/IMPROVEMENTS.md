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

### §RK1481 One act, two spellings, and no way to tell which you are holding

Met three times in one session, by a caller moving between the two surfaces roadkeep
publishes.

The MCP tool is named next_id and the CLI verb is next-id. The MCP argument is
replacement and the CLI flag is --with. Both refusals are good ones - each names the
surface it is on and offers the spelling it wants - so nothing was lost but a call each.

What makes it worth a line is that the caller has no way to know which spelling they are
holding. A session that has been using the tools all day has next_id in mind because
that is what it just called; the CLI is the same engine, the same verb and the same
arguments, and the name is different for a reason that belongs to the transport rather
than to the act.

Two shapes, and the cheap one is probably right. Either the CLI accepts the MCP spelling
as an alias - underscores for hyphens, and the argument names the tools publish - or the
tools publish the CLI's spelling and the transport does the mapping. The first costs
nothing anybody can see and makes every remembered call work; the second is tidier and
moves the surface everything is already written against.

What should not happen is a third surface that spells it a third way.

### §RK1483 The pairs a sweep would have named

RK1459 fixed one pair by hand: `budget --body-file` and `add --section-body-file` are
the same path, and a caller moving from the price to the write was refused for the name
it had just been told to use. Nothing enumerates the rest, and there are more.

Measured on this build, the same shape twice over:

    budget --anchor RK1 --body "…"      section amend RK1 --body "…"
    budget RK1 --retire RK9             retire RK1 --superseded-by RK9

The first names by flag what the write takes by position; the second names the same id
under two words. Both refusals are good — RK1254 answers `--anchor` with *taken by
position* and the argv it wants — and both are a turn, every time, inside the loop this
tool most wants taken: price it, then write it.

The population is enumerable, which is what makes this a check rather than a sweep.
`budget` has eight subjects and each names the write it prices; a test can pair the read
against that write's parser **both ways**: every argument the read accepts reachable by
the same spelling, and every one the write adds askable here at all. RK1458 and RK1461
are that second direction, each met as a wrong number rather than a refusal.
`test_composing`'s shape, and an exemption nobody can see reads like a rule being kept.

What must not come out of it is a rename. `section amend` is right to take its anchor by
position and `retire` is right to say `--superseded-by`; the read is the one verb asked
about every subject, so the aliases belong on it.

### §RK1484 The span the writer already knew

RK1460 writes a verified criterion under the ledger entry, as a continuation of the
bullet. That is `carrying`'s own shape (RK157) and it round-trips, but it makes the
entry **wrapped** — and a wrapped entry costs every later door a count.

`record amend <id> --why` is refused on one until `--lines` says how many it replaces,
the count being the caller saying they read the span. Before this a correction was one
call; after a `--checked` it is a `show <id>` to read the span, then an amend carrying
the whole tail back. RK1049 built that path deliberately and it is right for a
hand-wrapped ledger — but here the wrap is **this tool's**, written by a flag, composed
from a bullet it had already parsed.

So the correction door asks a caller to re-supply prose the writer derived, which is the
shape RK16 confines to the fixer: a derived line is repaired and never retyped.

What is likely missing is that `record amend` should not count a continuation it can
recognise as its own. The carried lines have a form — two spaces, the word `checked`, a
bold lead the criteria grammar wrote — so the span is knowable rather than declared, and
an amend of the sentence alone could leave them where they are. What must not follow is
`--lines` becoming optional in general: a hand-wrapped entry is prose nobody parsed, and
that refusal is the reason the door is narrow.

## Block C — Query

### §RK1486 The ceiling and the corpus it was not read on

RK1463 was filed as *four fifths of the answer*. It measured, on a six-dep fixture built
for it, at 46% — and the duplicate it removed was half of that, leaving `deps_resolved`
at 34% of a 4,846-character brief. The remainder is not waste: each row is a dep, its
resolution, and where it landed.

What the filing could not know is where the ceiling came from. `[reads] brief` is
declared here and `cost --brief` ranks every open line against it — but this
repository's own lines carry **no deps at all**, so the widest brief here has never had
a `deps_resolved` block in it. The number (RK1286: 2,549 units read, 3,300 declared) was
measured on a population that cannot exhibit the growth this task was about.

So the ceiling is real and the reading behind it is narrow. A backlog whose lines depend
on each other pays per dep, per settled dep, per chain — three lists that grow with the
graph and not with the prose — and none of that is in the figure this project holds
itself to.

The cheap move is a corpus reading rather than a new rule: `cost --brief` already ranks,
and Shio's and Turing's pinned trees are in `tests/corpora.py` and do carry deps. What a
widest brief costs *there* is the number `[reads] brief` should have been argued from,
and it is one command away on a tree this suite already reads.

### §RK1490 The half a pick cannot offer

RK1467's symptom was that a requirement gates the **whole** line, so the half of a task
that needs nothing is never offered. What shipped makes the gate legible: the refusal
quotes what the word was declared to mean, so a caller can judge it. It does not make
the half reachable, and the design said as much.

So the split is still a discovery made by disbelieving a refusal. A caller who reads
*this needs upstream, which is push access to the second repository* and thinks *the
part I want is in this repository* has no way to say so: `--have upstream` is a lie,
`pick` has no flag for taking a line partly, and the only honest move is to work outside
the ranking and let `ship --part` record it afterwards.

The shape is small and half-built. `ship --part <what landed>` leaves the remainder open
with a `why` of its own, which is this tool already holding the idea that a line has
parts. What is missing is the same idea *before* the work: a line could name which
requirement gates which part, or — cheaper and with no new field — `pick` could offer a
withheld line under a tier saying *ready except for what it requires*, so the caller
reads the whole thing and decides.

What must not follow is `--have` becoming a way to say *not really*: the vocabulary is a
contract, and a caller claiming a requirement it lacks makes every later refusal
meaningless.

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

## Block D — The gate

### §RK1488 The answer that leaves without a word

RK1457 decided that a line's design is where an answer to `non-goal.reaches` goes, on
the ground that it **ages out with the work**: the ship deletes the section, so no stale
bookkeeping survives. Shipping RK1465 proved the other half of that. Its design carried
the clause answering *No supported Python API.*, the ship deleted it correctly, and the
only sign anything had happened was a `ref.dangling` from a *different* section that had
cited it in prose.

So the answer is silent going out as well as coming in. Nothing in the ship's register
said a clause somebody wrote to settle a gate row was among the words being deleted, and
nothing would have said it at all had no other section happened to point there.

Ageing out is still right. What is missing is that the write should **say** it: `ship`
already reports `dropped §RK1465` and `cited §RK1478`, so the shape exists — a row
naming the constraint whose answer went with the section is one more fact off a section
the write has in hand, and it is the last moment anybody can read it.

Whether the answer should then be re-recorded is a separate question and probably no:
the line is gone, so the pair the note was about no longer exists, and re-filing it
somewhere would be the stale bookkeeping RK1457 rejected the field for. Saying it left
is the whole of what is owed.

### §RK1489 The fixture that cannot hold the answer

RK467's sweep runs every pair of a verb's flags against one fixture and reads a
swallowed flag off the output: if `a b` answers exactly as `b` alone, `a` did nothing.
It is a good reading and it has a blind spot — a flag whose subject the fixture cannot
contain.

Met adding `anchors --retired` (RK1466). Retired addresses are read out of **git
diffs**, and the pairs fixture writes four files and inits no repository, so it holds
none: the flag is correct, the wide listing genuinely has nothing to withhold there, and
`--retired --json` answers byte for byte as `--json`. The sweep reports it as swallowed,
which is false.

What closed it was publishing `retired_listed` — the call's own narrowing, beside
`family` and `role`, which the payload publishes for a stated reason. That is a real
improvement and it is also the shape the sweep will accept from anything: a key echoing
the request makes any flag look honoured, whether or not it changed the answer.

So the sweep now has a way to be satisfied that is not evidence. What is missing is the
fixture's own reach: it declares an outline project on purpose, because under ids
`anchors` refuses and every pair exits 2 — the same reasoning one state further. A
repository with one deleted section, one shipped line and one claim would let three
verbs answer about the states they are for, and the flags whose subject is history would
be measured rather than declared.

### §RK1491 The cadence nobody counts

`engine.disagreement` is composed one clause per fact and joined with `and`, which is
the shape RK1440 gave it and the reason RK1468 could add a third in a line. Composed
with all three true it is **475 characters**, and it fires through the `Stop` hook on
every turn.

Nothing prices it. `[budgets]` holds the every-turn files, `[tools]` the served surface,
`[reads] brief` the read that replaces reading a file, and `cost --deny` a refused write
— five cadences, and a note is in none. So the message a wired project reads on every
turn is the one no number is kept about.

RK30's argument is exactly this and was made about `agents.md`: a limit nobody counts is
a limit that moves. This note has moved twice in three tasks, each time for a good
reason, each time by a clause nobody measured against anything.

The reading is cheap and the verb for it exists. `cost` has five subjects and each is a
cadence; notes are a sixth — what a clean run says beside its verdict, which is what a
session pays for being told nothing is wrong. Then `[reads] notes` or a ceiling of its
own is a number somebody argues rather than a paragraph that grows.

Worth weighing against it: there are few notes and they fire rarely, so the total may be
small enough that a ceiling is ceremony. That is a reading and not a guess, and taking
it is what this task is.

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

## Block E — Adoption

## Block F — The plugin

### §RK1482 The finding that is about the reader

Measured on one long session in an adopting project. The session-start hook said the
skill had drifted, in its first message. Every `lint` after it ended with three
`install.stale` lines. The session read past all of them for hours, and only went
looking when it ran out of roadmap work.

What it cost is specific. `asking.md` and `writing.md` were not merely stale in that
project, they did not exist — so the session never learnt that `budget --anchor`
measures a section before it is sent, or that `--body-file` names the paragraph by path.
One design took five refusals against the word limit, each re-sending the paragraph, for
want of a page one command away.

Why it reads past. Everything else `lint` prints is about the project's own files: a
line over its limit, a criterion with nothing to check it, a pointer resolving to
nothing. Those are work. This one is about the reader's own tooling being older than the
engine answering it, which is a different kind of fact wearing the same shape, and it
sits in the same list at the same weight.

Two cheap shapes, and neither is a new check. The finding could say what the staleness
costs rather than that it exists — naming a verb the installed copy does not document is
a sentence nobody reads past. Or the summary line could carry it, since a reader who
skims one line a run sees that one and not the fifteen above it.

### §RK1485 The guard with no way in

RK1462 gave `install` a record — `[install] wired` — so a refresh cannot be a downgrade.
Every project already wired has no such record, and that is exactly the population the
defect was measured in: an adopter whose surfaces came from a later engine, running an
older one, being offered the write that deletes a fix.

The record arrives on the next `install`, and the next `install` is the write being
guarded against. So on the tree that needs it most the guard is inert until somebody
makes the very edit it exists to refuse — and having made it, the record says the older
engine wrote the surfaces, which is then true.

Nothing is wrong with the design; what is missing is a way in. Two shapes are visible.
`install --check` could say the record is absent and name what would establish it, which
puts the reader in front of the decision. Or the version could be *derivable*: the
bridge and the skill are copies of files this package ships, so a checkout with its own
history could order them without a record — though an adopter's clone cannot.

The narrow answer may be that absence should read as *unknown and worth saying*, not as
*behind*: `install.stale`'s sentence claims a direction it has not established, and
where no record exists that claim is a guess with a write attached. Saying so costs a
clause and tells the one population this task could not reach.

### §RK1487 The copy a refusal does not mention

RK1464 moved the vendor in front of the surfaces and accepted the hazard RK1193 put it
behind them for: a run that copies an engine and then fails to wire it leaves a copy
nothing points at. The trade is right — a downgrade somebody commits is worse than a
directory one more `install` clears — but nothing says so when it happens.

The failure is quiet in both directions. `install` writes every surface or none, and a
refusal after the vendor exits non-zero with a `.roadkeep/` on disk that no declaration
names; the caller reads what stopped the surfaces and not what landed. And a pinned
project is now the *source* for every later plan, so a wrong-version tree there is what
the surfaces come from — which `_pinned_engine` guards by requiring the five carried
files, a shape test and not a version one.

What is missing is one sentence at the one door. A refusal raised after the copy could
name what landed and what it is not yet wired to, which is `NotVerified`'s own shape —
that one leaves the tree on disk deliberately and says why. Nothing here does.

Worth weighing beside it: `uninstall` takes the declarations out and leaves
`.roadkeep/`, so the pair is not symmetric either. Whether the copy is `uninstall`'s to
remove is a question about what an artefact is, and the answer may be that it says where
it is rather than deleting somebody's megabyte.

### §RK1492 The argument nobody marked

RK1469 made `engines --invoke` read this project's own `.mcp.json` and stop at the
program, because the declaration ends in `mcp` and a caller is about to put a verb
there. Finding the program means finding the last argument that looks like a Python file
— which works for every spelling this tool writes and is a guess about somebody else's.

`.mcp.json` is a **declaration**, and `install` merges into it rather than owning it:
the file is the project's and other tools declare in it. So the roadkeep entry can hold
something this reader did not write — a wrapper, an interpreter with flags, `uv run`
with the launcher three arguments in — and `.py` is what tells them apart today.

Where it is wrong it is wrong quietly. A declaration whose program is not a `.py`
returns the whole argv, `mcp` and all, and the line a caller pastes runs a server
instead of the verb they appended; one carrying a `.py` *option value* stops in the
wrong place.

The fact is knowable rather than guessable. `install` writes the declaration and knows
which argument is the program — it is `_rooted`'s own substitution point — so the honest
answer is for the argument that ends the command to be marked at the moment it is
written, or for the read to match the launcher path it already computes rather than a
suffix. Either turns a heuristic over somebody else's file into a fact about ours.

### §RK1493 The kinds nobody declared

The served notes are now four kinds — the landed write, the inventory, the witnessed
refusal, the swapped home — and three of them are held to *once per process* by a set of
string keys in `_SAID`. The fourth, the witnessed one, deliberately is not.

Nothing enumerates them. `_said_once("swapped")` was added in one line beside
`_said_once("landed")` and `_said_once("inventory")`, and a fifth kind arrives the same
way: a literal, invented at the call site, never checked against anything. Two spellings
of one key would silence a note that had never been said; a key nobody registers reads
exactly like a note that fires every time.

Which of them is once-per-process and which is per-call is also a decision, and it is
written as the absence of a call. RK1443 argued the rule and RK267 argued the exception,
and both arguments live in the docstrings of the branches that happen to make the call —
so the population is *whatever the code does*, and a reader asking "which notes repeat"
has to read the function.

The shape is `composing.SITES`' and `test_surfaces`': a declared set of kinds, each with
the sentence saying whether it repeats and why, held total against the literals the
module passes. Then a fifth note is a red until somebody says which it is, and the
exception is visible rather than inferred.

Cheap, and the sweep exists twice over in this suite — which is the argument for doing
it rather than for a third one.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
