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

### §RK1474 The half of a decision that was never typed here

RK1453 gave the decisions file a correction door for the half `ship --decides` composes.
The other half of that line has none, and it is a copy: the symptom is the roadmap
line's claim, carried across by the ship, and `--decides` writes no symptom on purpose.

So a typo there is worse placed than the one RK1453 fixed. `restate` corrects a roadmap
line's symptom, and by the time a decision exists that line is gone — shipped, its
ledger copy correctable by nothing either, `record amend` calling the symptom "the
claim" and declining to touch it. Three files hold the same words and no verb reaches
two.

Whether that is a defect is open, and the ledger's own answer argues it is not. `record
amend` excludes the symptom deliberately: an entry's claim is what the work was filed
against, and a claim editable afterwards records what somebody later wished had been
claimed. The decisions file inherits that argument whole.

What it does not inherit is the mechanical case. A symptom mangled by a shell — the
ASCII transliteration RK1453 was met by — is not a claim somebody revised, it is bytes
that never arrived, now copied into two permanent files. The narrow fix refuses anything
but a change in characters the parse normalises, so a reworded claim is still refused.

The cheaper answer may be upstream: `add` and `ship` refusing a symptom carrying what a
failed encoding leaves, at the door, where this project puts every other check.

### §RK1475 The offer that knows what refuses it

Observed while shipping RK1454, on a throwaway project. One line, shipped with
`--decides`, and the ship prints:

    event  FB1  Block D  finished
           its last open line just left — `roadkeep block drop D` withdraws the heading

Run it and it is refused: the decisions file files FB1 under that heading, so removing
it would refile the decision. RK1454 made that refusal name the ending, which is the
repair a reader needs. It did not stop the offer that sent them there.

`removable` states the rule this breaks in its own docstring — "a finding naming a
command that then refuses is worse" — and holds it for the gate, where a doubled heading
is only reported where the drop would work. The ship's offer is the other reader of the
same question and never learned it.

The fact is cheap and already local. `ship --decides` writes the decisions file in the
same transaction, so the call that composes the offer knows an entry has just been filed
under that heading; more generally, `removable` answers per role and the offer is right
exactly where every declaring file but the ledger would give the heading up.

What is not obvious is what the offer becomes. Silence is one answer and loses the fact
that the block finished. Better is likely the ending RK1454 now prints on the refusal,
said at the ship instead — "the heading stays, which is how such a block ends" — so the
sweep gets its terminal state from the write that produced it and never runs the verb at
all.

### §RK1480 Adding a dep by restating the ones that were right

Measured adding a blocker to a line carrying six deps. The call has to name all seven,
because --dep given at all replaces the group - so six of the seven arguments exist to
say nothing changed, and each is a chance to drop one silently.

Then it fails. Deps are rendered into the line, the line's ceiling is shared with the
why, and the seventh dep took the why below what it already held: the refusal named the
why, which had not changed and was not wrong. The fix is to shorten a sentence the
caller never meant to touch, and the caller learns that only after composing the
seven-dep call.

Neither half is wrong on its own. Replacing the group is the honest primitive, and the
line budget is the whole point of the limits. What is missing is the narrow door:
--add-dep and --drop-dep, which name what changed and let the tool derive the group. It
knows the current deps, and show prints them, so the caller restating them adds nothing
but the chance of an error.

It would also let the refusal arrive about the right field. An add that makes the line
too long is a fact about the dep being added, and saying so beside that dep is what
makes the next call correct rather than a guess at how many words to cut from a sentence
somebody else wrote.

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

### §RK1472 The pre-flight that does not know about requirements

`budget` prices the line from what is known before the first word: the id, the marker,
the deps, the pointer. A requirement is known then too, and it is not counted —
`(requires: upstream)` is twenty-one characters of the same 320, and `budget` declares
no `--requires` to be told about one.

Measured on an adopting project, one draft, two answers:

    budget --block E --symptom … --why …
      why  185 of 200, 171 drafted, 14 left

    add --block E --requires upstream --symptom … --why …
      refused: why: 171 characters, limit is 164 [why.too-long]

Twenty-one characters, exactly. The caller did the thing the tool asks for, was told it
fit with room, and was refused anyway.

The refusal is what makes it worth a line rather than a note. It ends with

    foresee  roadkeep budget --why <draft>

which is the call that just gave the wrong number. A caller who follows it a second time
gets 185 again, and the only way out is to stop believing the pre-flight — which costs
more than never having had one.

Two fixes and they are not the same. `budget --requires <r>`, repeatable, matching
`add`, is the small one. The larger: nothing makes a new field on the line teach
`budget` about itself, so the next group added to the grammar arrives with the same
hole. Whether the structure figure can be derived from whatever composes a line, rather
than enumerated beside it, is the question this asks.

### §RK1473 The report that reads its own writes back

`unclosed` asks which open lines have commits naming them and no ledger entry, and
already knows one class does not count: the commit that filed the id, since `add` mints
it and nothing could name it earlier.

The same argument covers more than `add`. `amend`, `restate`, `status` and `section
amend` end with the caller writing a message naming the id, and all touch only files
roadkeep governs. None is a session that shipped code and forgot the line — each is the
tool's own write, made because it asked and staged the files it named.

On an adopting project, three of eight open lines were reported. Two were commits
changing one governed file and nothing else: a corrected `why`, a corrected rationale.
The third amended a rationale and a comment in `roadkeep.toml`. None was code.

A report and not a gate, so nothing broke. But a report whose entries are all false is
one a reader stops opening, and this one is loudest where a backlog is kept most
carefully: amending a line rather than letting it go stale is what generates every false
positive.

What separates them is on disk. A commit touching only files named in `[files]` is about
the backlog; one that touches code and names an id is what this verb was written for — a
filter over what `git show --stat` already answers, not a fact anybody has to record.

Worth weighing: a commit doing both at once is real, and would still be reported.

### §RK1476 The listing whose refusal is somebody else's

RK1455 gave the structure question a read that answers it and pointed the block filter
at that read. The half it could not close is the listing itself: `list --role changelog`
with no `--block` prints every entry, and on the project measured that was 117,815
characters — refused by the transport, after roadkeep had already composed and returned
it.

Which is why this is not RK1466. That one is `anchors` under the id scheme, where the
rows are addresses and the fix is live in full and retired as a count. Here the rows are
the ledger, every one of them is live in the only sense that file has, and nothing in
the answer is droppable — so a cap has to be a cap and not a narrowing.

The refusal is also nobody's here. roadkeep exits 0 having answered; the client is what
says the result is too large, and this tool never learns it. So a message about the
overrun cannot come from the verb that caused it, and the only thing that can is a bound
the verb applies to itself.

What that bound is, is the question. A row count is arbitrary; a character count is what
`cost --brief` already measures a read by, which suggests a `[reads] list` beside it and
an over-budget answer replaced by what `block list` prints. That is smaller than the
answer refused and closer to what was wanted — RK1455's own argument, which it could not
act on.

### §RK1477 The pair the window was waiting for

`NEAREST`'s own comment says the figure moves "only if a pair is ever found further
down". One has been. RK1456 was filed on 31 August against `budget`, and RK1190 had
shipped that behaviour on 16 August — `--why`, `--symptom` and `--body` all measure a
draft, exit 1 over, and the why row already names where the line binds. RK1456 was
retired as superseded, having been filed, designed and briefed first.

Ranked against Block C's 148 delivered symptoms, RK1190 comes **7th**. `delivered
--near` prints 5 and the rows an `add` volunteers are 3, so the entry that made the
whole line unnecessary was four places outside the window the write itself printed.

The two share their subject and almost no words. RK1190: "budget states the allowance
and cannot be handed a draft, so prose three words over is found by being refused".
RK1456: "budget says what a why is allowed and nothing measures the why about to be
written". `budget` is in most of that block, so its idf is near zero, and the words that
would have matched — draft against measures, allowance against allowed — are the
vocabulary a second author picks having not read the first.

Raising the window buys one rank at a time. The likelier fix is what is ranked: the
corpus is symptoms alone, and RK1190's `why` names `--why` and `--symptom` by their flag
names, which is what RK1456's design spent a paragraph asking for. Both fields is the
same reader with twice the evidence.

### §RK1479 The carry a budget has no word for

RK1458 named three departures and shipped one. `--retire` existed, `--ship` landed, and
`--defer` was left out because :class:`Budget` has no shape for what a pause does to the
field.

The other two are simple in the same way. A ship writes the author's whole sentence into
a fresh ledger line, so the room is the whole allowance; a retirement writes `abandoned:
` first, so the prefix is `derived` and the reason is what is left. A pause is neither.
`_as_paused` composes the store's `why` as the reason *wrapped* — an open marker, the
reason, a close marker — and the roadmap's own `why` after it, carried whole. The field
holds a wrapper, the author's new sentence, and the old one.

`Budget` can say `derived` — prose the tool writes before the caller's — and `replaced`
— whether the next write takes the field entire. Neither is true here: the carry is a
suffix, and it is somebody's prose rather than the tool's. Priced with the shapes that
exist, a `--defer` row would report either a prefix that is not one or an allowance that
ignores the design still sitting in the field.

What is missing is a third reading: prose the field keeps that the caller does not
retype. That is one attribute and one row, and it makes the pause's number honest — and
it is worth having beyond this verb, because the same fact is what `[limits.deferred]`
is measured against and what a `defer --reason` is refused by.

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

## Block D — The gate

### §RK1468 The note that reconciles one pair of three

RK1451 gave `engines` a row for the copy vendored under `.roadkeep/` and an exit code
that covers it. `lint`'s `engine.disagreement` note — the once-per-commit surface RK1238
put the same question on — still reads `running` and `plugin` and nothing else.

So the two answers disagree about one tree. In a project holding a vendored engine two
minor versions from the shell's, `engines` exits 1 and names both pens while the gate
that runs on every commit says nothing at all. That is the population the note was
written for: RK1440 measured it in a port that had just wired the served `lint` into its
local gate, where a version is a claim rather than an argument somebody typed.

The note's own shape is what makes this cheap. It already composes one clause per fact —
`working` for a modified checkout, `skewed` for a plugin at another number — and joins
them with `and`, so a third clause is a third fact and not a second sentence. What it
must not become is a note on every project: an absent `.roadkeep/` is the default, and
`Engines.split` is already the boolean saying a copy is both present and apart.

Open: whether the clause names a remedy. The plugin half offers `/plugin update`, and
these two are both pens — re-vendoring is one answer, not reaching past the launcher is
the other, and which is right is the project's call rather than the note's.

### §RK1478 The answer that only one side can see

RK1457 gave `non-goal.reaches` a way to be answered: the line's design quotes the
constraint's lead and the note falls silent. Clearing this repository's own two took two
`section amend --replace` calls whose whole content was a sentence saying *the rule
bounds nothing here* — and neither of them said which note they were answering.

So the record is silent in the direction a reader arrives from. Each clause read as a
stray remark about the subject it named; nothing said a gate row was open, that somebody
had read the constraint against the line, or that the silence depended on those words
staying. Both are already gone — RK1465 and RK1466 shipped within the hour, and each
ship deleted the design carrying one, unremarked.

The other governed answers do not have this problem, because each is a field: a dep is
annotated, a supersession is a marker and a pointer, a queue entry is a row. This one is
prose, matched by substring, and the whole mechanism is invisible from the file.

What is missing is not a second store — that is the field this task rejected, for
reasons that hold. It is that nothing *reports* the answers. `non-goal list` prints the
constraints and could print, per constraint, the lines whose design settled it: one
read, derived, naming both sides. Then the decision is greppable from the rule as well
as from the line, and a clause somebody is about to delete is one a command already
named.

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

## Block E — Adoption

## Block F — The plugin

### §RK1469 The order that is stated twice and read once

RK1230 exists because a session found its engine by listing a plugins cache and reached
a copy the project does not write with. `Engines.invoke` is the answer to that, and
RK1451 taught it a second rule: with no plugin registered, name the launcher of the copy
vendored under `.roadkeep/`, because that is what the guard and the served tools run.

Both rules re-derive an order the launcher already holds. `hooks/roadkeep-launch.py`
resolves `$ROADKEEP_HOME`, then `.roadkeep/`, then a sibling checkout, then the cache
clone — and it *probes* each, because RK1214 measured a sibling mid-refactor that
resolved, answered a version and then raised. `invoke` knows the middle of that list and
neither end.

So a project pinning `ROADKEEP_HOME` to a tree outside itself gets a line naming a copy
that is not the pen — the exact failure RK1230 was written for, one wiring further
along. The line is pasted, it runs, it does not fail, and it judges by rules the writing
copy does not hold.

What is unresolved is who owns the order. Copying `_candidates` into this package makes
two statements of one resolution, which is the drift the whole vendoring task refused;
asking the launcher costs a subprocess on a read that `lint` reaches. A third reading:
`invoke` answers the **bridge** an adopter commits — `.claude/hooks/roadkeep-launch.py`
— where one exists, so the order is resolved once, at the moment it is used, by the file
that owns it. Then `engines` never needs to know what the order is.

### §RK1470 The note that has the weaker of two readings

The served staleness note (RK155, narrowed by RK267 and RK1443) turns on `Engine.stale`:
this package's modules whose mtime moved after the process imported them. It is
calibrated for a developer editing the tree a server is running — the RK155 case was one
commit adding `[claims] held` to both `roadkeep.toml` and `config.py`.

RK1452 added the other reading and the note does not have it. `Engine.on_disk` says the
home now holds a **different version** from the one loaded — what `install --vendor`
leaves when it replaces `.roadkeep/` in place under a live server. To the mtime reading
that swap is a file being saved: every module is newer, so the note lists all of them.

The two are not the same claim and the remedies are not the same either. A file that
moved may or may not be the one that decided the call — RK267 spent a whole task
narrowing the note to the intersection with the traceback for exactly that reason. A
version that moved is not a maybe: the code answering is gone from disk, the
intersection is irrelevant, and restarting is the only remedy there is.

So the shape is likely a clause the note takes before it narrows anything — `swapped` is
already a boolean and `on_disk` is already the number. What must not happen is a second
paragraph: this note has been cut twice for being text a reader skips, and a third one
would undo both.

### §RK1471 The guard that has no version to compare

RK1235 put a guard in front of every governed write: a copy behind the pin a project
declared with `[install] enforced` is refused, because it does not fail — it agrees with
a rule that has moved and writes a line its own version thinks legal, reported
afterwards as the file's problem rather than the pen's.

RK1452 found a second copy in that state and did not guard it. A server whose home was
replaced in place runs code on no disk anywhere: its schema, its limits and its markers
are whatever they were at import, and the tree everyone else reads has moved past them.
That is the RK1235 failure with the pin removed — no version to compare, no flag to have
declared.

Whether it should refuse is the open half, and the launcher's own first rule argues both
ways. *Never block a turn* is why `roadkeep-launch.py` degrades to unenforced rather
than erroring, and a write refused by a condition only a restart clears is a wall with
no door — RK1235's refusal prints the copy to re-run through, and here there is none to
print.

The cheaper reading may be that this belongs to the note and not the guard: `swapped` is
a fact a session acts on once, and acting on it is restarting. The decision left is
whether a write under a swapped engine is worth saying so on, or whether saying it once
at the top of the session is the whole remedy.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
