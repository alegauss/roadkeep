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

### §RK1463 The evidence for a boolean, printed whether or not it fired

Measured starting a task in an adopting project: `brief` with no id answered about 4,000
tokens, and the line, the rationale, the non-goals and the done-when together were under
a fifth of it.

The rest was `deps_resolved`. Every dep came back with a `settled_since` block holding
the shipping commit's sha, short sha, date and full subject, and the same four fields
again for the revision it was compared against — six deps, twelve commit records, all of
them saying the same thing: shipped, and long before this task was written.

That reading exists for a real signal. A dep that shipped *after* the rationale was last
revised is a design written against a world that has since moved, and a caller starting
the task should be told. But the check is a comparison and its answer is a boolean, so
printing the evidence for it whether or not it fired is what makes the payload what it
is.

Keep `settled_since` where the shipping commit is newer than the revision, which is the
case it was built to surface, and collapse the rest to the word `detail` already
carries. A caller who wants the history has `origin`, which is the verb for it and
answers one task at a time.

### §RK1466 The listing that now names everything it counts

RK1450's finding was that the wide read stated 88 addresses and offered no way to see
them: under `ref_scheme = "id"` there is no family register, so the summary that stands
in for the rows (RK264) is empty and the substitute is a sentence about `add`. The fix
prints the rows there. It has no ceiling.

Measured by composing this repository's own 960 addresses as a project with no families
— which is the state every id-scheme project is in:

    payload   175,384 bytes, 960 rows
    printed    52,655 characters, 961 lines

Against a handshake whose whole tool surface is 64,333 units and a `[tools] characters`
ceiling of 2,800 for one tool's description. A read three times the size of the surface
that published it is not a bounded answer.

The two halves of Block C's criterion come apart here: the answer fits no tool result,
and it does not say what it left out, because it left nothing out. Retired addresses are
what grows — one per shipped task, unbounded by anything the project can prune — while
the live ones are bounded by the open backlog.

So the shape is likely live rows in full and retired as a count that names the flag
which lists them, which is the door RK1450 was actually missing. What must not come back
is the count with nothing behind it. **No effort or size field.** is about a slot on a
task line and this is about a payload's, so the rule bounds nothing here.

### §RK1467 What a requirement withholds beyond itself

`[requirements]` is a property of a line: `pick` withholds it whole from a caller that
has not declared what it names. That is right where the requirement is what the work is
— a Terraform module for a provider nobody holds an account with is not half-writable.

It is wrong often enough to notice. In one project a line carried `requires: upstream`,
declared as the ability to land a workflow and a secret in a second repository. `pick`
set it aside with every ready line and answered "nothing to pick". What the work needed,
once somebody read past that, was a step in an action already in the repository the
caller did have; the upstream half shrank to a pin bump. The line that would have led
anyone there was the one withheld.

`ship --part` is the idea this is missing, arriving after the fact. It already knows a
line can land in halves: it records the one that did and leaves the rest open with a
`why` of its own. Nothing says so beforehand, so the split is a discovery a caller makes
by disbelieving a refusal — the opposite of what a refusal is for.

What the fix is, is the open question. A second `why` per requirement is prose that will
go stale beside the first. Cheaper: the refusal already names the requirement, and
printing that requirement's own declared sentence beside it would let a caller weigh the
cost in the line they are already reading.

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

So the record is silent in the direction a reader arrives from. Six months on, that
sentence in §RK1465 reads as a stray remark about `py.typed`; nothing says a gate row
was open, that somebody read the constraint against the line, or that the silence
downstream depends on those exact words staying put. Delete the clause while tidying and
the note comes back with no clue as to what removed it.

The other governed answers do not have this problem, because each is a field: a dep is
annotated, a supersession is a marker and a pointer, a queue entry is a row. This one is
prose, matched by substring, and the whole mechanism is invisible from the file.

What is missing is not a second store — that is the field this task rejected, for
reasons that hold. It is that nothing *reports* the answers. `non-goal list` prints the
constraints and could print, per constraint, the lines whose design settled it: one
read, derived, naming both sides. Then the decision is greppable from the rule as well
as from the line, and a clause somebody is about to delete is one a command already
named.

## Block E — Adoption

## Block F — The plugin

### §RK1462 Stale, behind, refresh — in one direction only

`lint` reported `install.stale` on both of this project's surfaces on every run, and the
finding names its remedy: `roadkeep install` rewrites them. Running it removed RK1446
from `.claude/hooks/roadkeep-launch.py` — the Windows branch that runs the server as a
child instead of `execv`ing it — and wrote back the version whose `mcp` mode exits 0 and
serves nothing: a session told by its own hooks to call tools the harness has already
dropped.

Nothing misbehaved by its own account. The engine answering here is the vendored 0.2.4
under `.roadkeep`; the committed surfaces were written by a far later one.
`install.stale` says the surface is behind the roadkeep answering, and it was — behind
in the sense of different, which on this file meant ahead.

So the comparison is the defect, not the copy. `install --check` asks whether the bytes
differ and never which side is newer, and it and the finding speak in one direction:
stale, behind, refresh. A project whose engine is older than its surfaces is offered a
downgrade in the vocabulary of an update, once a session, until somebody takes it.

The engine knows its version and generates the surfaces, so the version that wrote one
could travel with it. What to do when the surface is the newer side is the open
question: refuse, or name which way the write goes and let the caller answer.

Worth weighing: `--vendor` exists for this and points the other way. Naming it in the
finding is most of the fix.

### §RK1464 Vendor, then generate — and it is the other way round

`install --vendor` does two things in one run: it writes the surfaces, and it replaces
the engine those surfaces are generated from. It does them in that order, so the files
it wrote are the outgoing engine's.

Measured here. `.roadkeep` held 0.2.4; the machine could reach 0.2.60. One run reported
`updated` on the launcher and the skill, then `vendored 0.2.60`, and `answers 0.2.60, as
chosen`. The launcher on disk afterwards was 0.2.4's — the one without RK1446's Windows
branch, which is a project whose MCP server exits 0 and serves nothing. `install
--check` immediately after exited non-zero on both surfaces, and `lint` reported the
same `install.stale` the run was called to clear. A second `install`, with nothing else
changed, wrote the right bytes and both went quiet.

So the one run that is supposed to move a project forward moves it backwards first and
lands it in the state its own `--check` refuses. Nobody reading that output would know:
`vendored` and `answers` are the last two lines, and `updated` is above them, which
reads as the new engine's work.

The order is the whole of it. Vendor, then generate — the flag exists to change which
engine ships the surfaces, so writing them from the one being retired is the one order
that cannot be what was meant.

Worth weighing: a caller who ran it once and committed has a tree that looks installed
and is a downgrade, which is worse than the failure it was fixing.

### §RK1465 The probe that costs what it protects

Measured on Windows 11 against this checkout, five runs each, `initialize` written to
stdin and the first response line read back:

    scripts/roadkeep.py mcp        283 ms min, 315 ms median
    hooks/roadkeep-launch.py mcp   646 ms min, 677 ms median

The difference is one `python scripts/roadkeep.py --version` — a whole interpreter start
and a whole `roadkeep.cli` import, 287 ms of the 363 ms the launcher adds. It buys one
thing: that a candidate found on disk will run, which RK1214 added after a sibling
checkout mid-refactor answered a `section add` with an `ImportError`.

That reason is POSIX's. `_serve` on Windows no longer `execv`s (RK1446) — it runs the
child with stdio inherited and hands back its exit code — so the parent this probe was
protecting is still there when the child fails, and the failure it predicts has already
happened in front of it.

What it costs is not the milliseconds here. It is that connecting is the engine's time
plus a second cold Python start, on the one path a client puts a thirty-second ceiling
on. RK1449 moved the cliff out of `initialize`; this is the floor under it.

The forwarded verb keeps its probe: it may write, so trying the next candidate could
repeat a half-done write. That hazard is what makes the two callers different. **No
supported Python API.** is about what this package exports; a Python interpreter start
is a cost, so the rule bounds nothing here.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
