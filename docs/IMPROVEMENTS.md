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

### §RK1459 The flag the price used, and the flag the write wanted

`budget` is the read this tool asks callers to make before a write, and the write it
prices does not take the argument it took.

Pricing a design section is `budget <id> --body-file <p>`. Filing that section in the
same transaction as the line is `add … --section-body-file <p>`. The path is the same
path and the content is the same content; only the flag changed, and a caller moving
from the price to the write in one step is refused by the argument parser for the name
it was told to use one call earlier.

The refusal is well written — it lists what `add` declares, right flag included, so the
cost is a turn and never a wrong write. But it is a turn every time, and it lands inside
the loop this tool most wants taken: price it, then write it. A read whose arguments do
not survive into the write costs more than going without one.

Both names are right where they are. `section add` takes `--body-file` because a body is
the only thing it writes; `add` takes `--section-body-file` because there the body is
one of two, and the prefix says which. So this is an alias and not a rename: `budget` is
the verb asked about both subjects, and it can accept either spelling of an argument it
already understands.

Worth weighing: an alias that is never printed is one nobody finds, so the help and the
refusal are half of it.

### §RK1460 Where the evidence for a run goes

`ship` prints every criterion the task carries under `unmet`, and that is the whole of
what it says about them. Where they are checked by running something, the list is
indistinguishable from a real gap. Shipping quickshell's QS116 printed two: *the window
shows what a session printed* and *an idle window issues no draw calls once it is
drawing at all*. Both had been checked — the first against a running client, with a
screenshot of a shell prompt in it, the second against its suite's idle assertions — and
there was nowhere to say so, so the ledger records a finished task beside two criteria
reading as open.

`evidence` is the neighbouring verb and is not this one: it runs a `roadkeep-evidence`
block of `<pathspec> :: <regex>` against the tree, so it answers for criteria a source
file can satisfy. A criterion whose own `why` says *checked by a running client* has no
pathspec. The run is the evidence, and it happened in a session about to end.

What is missing is small: a way for the call that ships to name a criterion and say how
it was checked, kept beside the ledger entry, so one nobody mentioned is told from one
somebody verified. Presence-not-enforcement survives — the sentence is its author's
claim, as `--why` is — and the value is `--why`'s: work finishing is the only moment its
evidence is in anybody's hands.

Falsified when a shipped task's checked criteria are indistinguishable from its ignored
ones.

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

## Block C — Query

### §RK1456 The field budget cannot measure

`budget` answers what a field is allowed and nothing measures what is about to go in it.
A section already has both halves: `budget --anchor <id> --body-file <path>` measures
the draft against the same limit and writes nothing, which is the refusal's own advice.
A line's fields have only the first half.

So a caller counting a `--why` has two moves, and both cost. Counting UTF-16 code units
by hand is what an agent does, badly, and the binding limit is not the published 200 but
the rendered line minus the symptom and the structure. The other move is to send it and
be refused: self-correcting, and a round trip per attempt. Measured on 31 August 2026
across three ships in one session, each hand-counted to avoid that round trip.

The gap closes with `--why` on `budget`, and `--symptom` already being there is the
argument for it: that flag exists because what the symptom takes is what the why loses,
so the asymmetry is not a design, it is the half nobody needed yet. Same for the two
`add` writes a line has.

What it should answer is what a refusal answers, before there is anything to refuse:
what the field takes, what the line leaves it, and how many to delete. A caller who can
ask that never sends a field that overruns, which is the whole point of validating
before writing.

### §RK1458 One field, two limits, and only one of them askable

Two limits govern one sentence and they are different numbers. The `why` on an open
roadmap line is held to one; the `why` a `ship` writes to the ledger is held to another,
because the two lines carry different structure and what is left for prose differs.

`brief` knows this and says both — it quoted `why 171 on this line` and, on the next
line, `why 190 on the ledger line a ship writes`. `budget` knows only the first. Asked
with `--why "…"` it priced against the line the task is on today and not against the
write the caller is about to make. `--ship` is not a flag it declares, so there is no
way to ask.

The cost is the one this verb exists to remove. Pricing a ship sentence means reading
the number out of an earlier `brief`, or trusting `budget` and writing to the stricter
of the two — spending characters that were there — or to the looser, and spending a
refusal.

What is missing is a subject and not a number. `budget <id>` prices the line the id is
on, and it could be askable for the line a departure would write instead: `--ship`,
`--retire` and `--defer` are the three, and each moves the sentence to a file with its
own structure around it.

Worth weighing: an id already in the ledger has no open line to price, so the
departure's line is sometimes the only one to answer about.

### §RK1461 The one field the price is never told about

`add --requires <word>` puts `(requires: <word>)` on the line, and `budget` has no way
to be told that is coming.

The gap is exact. Pricing a task with `budget --block C --symptom … --why …` answered
`why 165 of 200`. The same sentence, written with `add --block C --requires upstream
--marker 💭`, was refused: `why: 158 characters, limit is 144`. The difference is 21, the
width of `(requires: upstream) ` — structure the write adds and the price was never told
about.

`--marker` is already a flag here, and it is the same kind of fact: something that
changes what surrounds the prose rather than the prose. So this is not a new idea about
what `budget` is. It is a field nobody gave it when `[requirements] declared` arrived.

What makes it a line rather than a shrug is which callers meet it. A requirement is
written by somebody filing work they cannot do — a server they do not have, an upstream
repository they cannot push to — and that is the moment the sentence is longest, because
it has to say what is missing as well as what is wrong. The price is least reliable
exactly where it is most wanted.

Worth weighing: `--requires` is repeatable on `add`, and two of them cost two words and
a separator. A flag that takes one word here would answer the common case and quietly
mis-price the rest, which is the failure being removed rather than a smaller version of
it.

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
is the count with nothing behind it.

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

## Block D — The gate

### §RK1457 A read note with no answer

`non-goal.reaches` fires when an open line shares a word with a constraint's lead. It
says a constraint may bound a line without forbidding it and nothing here decides which,
and its remedy names `non-goal amend` to narrow the rule or `retire` to take the line.

MEASURED ON A REAL PROJECT. One rule there is "No local patch to the vendored C". Two
open lines name "vendored": one deletes the libraries the rule's argument exempts, the
other ports call sites and may keep the C untouched. Both decisions were made and
written into the rule's paragraph by name, in two separate tasks. Both are still flagged
on every lint.

SO THE REMEDY DOES NOT CLEAR THE NOTE. There is nowhere to record the answer: a non-goal
is a lead and a why, and the why is prose this check does not read. A project that has
done the reading is indistinguishable from one that has not, and the second task to do
it had no way to tell the first had.

WHY IT COSTS. That project runs `lint` inside its local gate, so those two print beside
four `install.stale` rows and one `engine.disagreement` - seven lines on every commit,
none answerable. A note nobody can clear is a note nobody reads, and a real one arrives
in that company.

WHAT WOULD SETTLE IT is somewhere the check can see the answer: an exemption the
constraint carries as a field, or the note falling silent where the rule's paragraph
names the line.

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
repeat a half-done write. That hazard is what makes the two callers different.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
