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

### §RK257 A ship refusal names the missing block heading but not the verb that writes it

Shipping the first task of a block whose heading only `ROADMAP.md` declares is refused,
correctly: the ledger entry has nowhere to go. But the refusal reads

    no heading declares Block BU (declares: A, AA, AB, ... BT, C, D.1, ...):
    a heading invented by a write files the text where nothing looks for it —
    but B shares a prefix with BU, so check that the label reached this command
    whole before declaring a second heading over the first one's work

Three of the four things an author needs are missing. It does not say **which file**
lacks the heading — the roadmap plainly declares it, so the natural reading is that the
label is wrong. It does not name `block add`, the one verb that fixes it. And the 90-odd
labels it does print are the answer to a question nobody asked, while the prefix warning
argues the author mistyped.

The recovery is one command and the refusal knows enough to spell it: `block add BU
--title "<the roadmap's exact title>"`. Naming the file and the verb turns a refusal an
author has to research into one they can act on, which is the same standard `needs`
already meets for a missing section.

### §RK262 A section add writes a heading ship will later decline to delete

`add --section "<title>"` takes the title verbatim, and `add` is the one command that
already knows the id it just assigned. If the author writes a title without it, nothing
objects — and the binding `ship` needs is gone before anyone could notice it was there.

`ship` then reports:

    kept: "§LXVIII.4 names no task in its heading, so it is prose belonging to none —
    the reading `lint` makes when it declines to report it orphaned"

Every claim in that sentence is true and the outcome is still wrong twice. The rationale
for shipped work stays in `IMPROVEMENTS.md`, which is the one thing `ship` exists to
prevent; and `lint` explicitly will not report it, so the file is left in a state no
gate will ever mention. The recovery is `section amend --title "<title> (<id>)"` then
ship again — a sequence the author has to derive from a field named `kept`.

Two doors, either of which closes it. `add --section` could append the id when the title
omits it, since it is writing the heading and holds the id. Or the refusal could move
earlier: decline a `--section` title that names no task, the way `add` already declines
prose over budget — a limit reported before the words exist is the principle already in
force one field over.

### §RK280 The one write in the contract that nothing guards

Observed, not imagined. `a0c6f6c` ships RK244 and carries `document.py` +40 and `adopting.py`
+16, which are RK279's implementation. `767d3eb` ships RK279 and carries `test_authoring.py`
+40 and a `cli.py` hunk reading `"ref": insertion.entry.task.ref`, which is RK249's. Two
sessions, two commits, each holding the other's work, both green — so nothing failed and
nothing said anything.

RK117 locks a scan-to-save span and RK119 says who holds a line, and both did their job:
no governed file corrupted, no id spent twice. The gap is that `agents.md` makes the
commit part of the task contract — "one task → one commit, the instant it is validated"
— and that step is a `git add -A` in a shell script. The guard denies a hand edit to a
file this tool owns; nothing denies staging a file it does not.

`agents.md` names a remedy — "a tree holding unrelated work wants the task's paths
staged" — which is advice, where RK1's argument says advice does not hold. It also does
not survive this case: both sessions were editing the *same* governed files, so staging
by path stages the other's edit too.

What could hold: `claim` already knows who holds a line, and a claim could name the
paths a task expects to touch, so a second session's write to a file the first has open
is refused and not merged. That is RK119 widened from an id to a working tree, and the
only version of this that is a schema and not a warning.

## Block C — Query

### §RK200 The record with no way to read it

RK175 closed the symptom it was filed for: a governed file whose bytes no verb wrote is
named as the turn ends. What it did not give is a way to *ask*. The digest sidecar is a
temp file whose name is a digest, the comparison happens inside a hook, and the answer
reaches exactly one reader at exactly one moment.

That is the arrangement RK161 ended for claims, and the argument is the same one: L5
says every question is a command, and "which lines are claimed" had to be answered by
finding a temp file. Here it is worse in one way — reporting **re-baselines**,
deliberately, so a turn that ends is a turn whose evidence is consumed. A session asking
afterwards what happened has nothing to read, and neither has the next one.

The obvious shape is the one `claims --prune` has: a read that says which governed files
are attested, which are not, and where the record lives — without moving the baseline,
because a query that changes the answer to the next query is not a query. Whether the
`Stop` block should stop re-baselining once such a read exists is the second question
and not this one.

What to check first is whether anybody wants it. The claim registry earned its read
because `pick` stepped over ids and could not say whose; this record has one consumer
and may not need a second.

### §RK245 The remainder is a budget too

RK185 published every aim in words, RK190 moved the read before the sentence, and RK201
put the surplus of an overrun in words as well. One number was skipped, and it is the
one an `amend` is actually bounded by: `Share.left`.

The line `budget RK244` prints is `symptom 120 of 120, 61 written, 59 left  aim 18
words`. `aim` is derived from `allowed` and describes the *whole* field, so beside a
partly written one it answers a question nobody asked — while `left`, the figure that
decides whether the correction fits, is in the unit RK185 established an author cannot
measure. Read together they are worse than either alone: "18 left, aim 30 words" invites
the reading that thirty words are available when about three are.

So `left` gets its word figure the way `allowed` did, and it **floors** — `left` is an
allowance and not a surplus, which is the opposite rounding from `words_over` and the
same argument RK201 made from the other side. `budget --json` gains the field beside
`left` rather than replacing it, because the characters are still what refuses.

Where it also has to land: `brief` prints the `why`'s share of the line it hands over,
so whatever `Share` grows is what a task started through `brief` is told, and the two
cannot be allowed to state it differently. The MCP `note` publishes the ceiling and not
the remainder, so it is untouched.

### §RK247 A retired anchor is invisible

On `ref_scheme = "outline"` an anchor is retired when `ship` deletes its section, but
the changelog entry that cited it keeps the pointer. Reopening that family is a real
move — a block whose work resumes — and the caller has to pick the next free number with
nothing to read: `section add`'s refusal lists the anchors that *exist*, which after a
fully-shipped family is none of them, so \"the next one\" looks like .1. Observed on a
project where §XXXVII.1 through §XXXVII.16 were all retired and all still cited: the
safe number was found by grepping the ledger by hand. Two fixes compose. Have the
refusal list retired anchors beside live ones, sourced from the pointers history still
carries. And let `section add` derive the next free child of a family the way `add`
derives an id — one past the highest ever used, not one past the highest surviving.

### §RK264 A distribution is six numbers, and this one arrives with its whole sample

L5 is that a question is a command, so answering costs no context. Measured on this
repository: `weight --json` is 23,741 characters, of which the `weighed` array is 22,714
— 95% — to deliver `low`, `p25`, `median`, `p75`, `p90`, `high` on two axes, per block.
Scoping does not fix it: `--block F` is 4,793 characters and still 89% records. The
question the command exists for is "what did a comparable cost", and the percentiles are
the whole answer; the per-task list is the evidence for it, which a caller wants when it
disputes the figure and not when it is deciding whether a line is two lines. The
precedent for the shape is already here twice. `brief` reports `non_goals_elided`, so a
caller knows the list it read was cut. RK10's argument is the other half: a listing that
looked complete is the whole symptom, so an elision has to be named rather than silent.
Together they give the design — report the distribution and the count, name what was
left out, and ship the records under a flag, which is also the honest place for
`co_shipped` and `unresolved` to stay. What must not happen is a cap: a top-N would make
the p90 a statement about a sample nobody chose, and the figure is the one thing this
command may not get wrong. Discovered by calling it unscoped for a question it does not
answer, which is how the cost was noticed at all.

### §RK265 The pointer budget cannot be told about

`budget` derives every number from the id, the marker, the deps and the pointer — all known before the
first word exists. Under `ref_scheme = "id"` that holds: the pointer is derived, and roadkeep's own
backlog counts 40 characters of structure against 320. Under `ref_scheme = "outline"` the pointer is
*chosen by the author*, `budget` has no flag to be told it, and it counts the structure as if the line
carried none — 30 against the same 320.

Measured in a repository that uses the outline scheme: `budget --block AI --symptom
'…108 chars…'` answered `why 182 of 200`. The `add` that followed, identical but for
`--ref XX.2`, refused at 188 characters against a limit of 174. The difference is
exactly ` → §XX.2`, eight characters, and the refusal costs the author a second
composition of the same sentence — which is the whole of what `budget` is for: "a limit
reported after the prose exists is a limit discovered too late to save the tokens it was
meant to save."

The shape of the fix is the flag `add` already takes. `budget --ref` under the outline
scheme, counted into the structure the same way the derived pointer is; and with no
`--ref` given, the honest answer is not the pointerless one — either the widest anchor
the file already holds, or a stated assumption, so a number that cannot be exact is at
least never optimistic.

### §RK283 The one line budget speaks for

`budget`'s own docstring states the principle: every number is derived from what is
known before the first word exists, "so the budget is a fact about the line you are
about to write rather than a verdict on one you already wrote". It is served for the
task line, and for nothing else.

Two other writes carry prose limits, both larger than the line's. `non-goal add --why`
is capped by `[non_goals]`; `section add` and `section amend` cap the body in words.
Measured against Shio on 2026-08-04, filing four tasks after a block emptied: the
non-goal took two refusals — 286 characters, then 234, against 200 — and the section
amend one, 366 words against 300. Each refusal is precise and arrives after the body
exists, which is the cost this verb exists to save, and it is larger here because a
section body is the longest thing an author writes. This section was itself refused
twice before landing, which is the report and its evidence at once.

The shape is the same: both limits are facts about the file and the role, known before a
word. `budget --non-goal` answers one; `budget <anchor>`, the way `budget <id>` already
answers for a line, answers the other — and an amend is where it matters, since there
the author has a body in hand to fit inside a number nobody has stated.

What this is not is a `--dry-run` on the write verbs. The point is to be answerable
*before* the prose.

## Block D — The gate

### §RK239 The state every verb refuses and the gate does not report

Measured while shipping RK232, and the number is the argument: Turing at `f08304fcb1`
declares thirteen anchors in both `IMPROVEMENTS.md` and `STRATEGY.md`. One is pointed
at, and `lint` reports it. The other twelve are reported by nothing.

Four readers already treat that state as unresolvable. `show` and `brief` refuse to pick
(RK186), `ship` keeps the section rather than choose which of two a line meant (RK196),
`defer` reports the ambiguity instead of naming a file (RK229), and `_pointed_at`
charges own prose because the gate does (RK232). So the tool has a settled opinion — one
anchor names one section — and the only check that says it out loud fires from the
pointer end, which reports the state when a task line happens to reach it and stays
silent otherwise.

That is the wrong end. The claim is about the prose files: `_declared` already builds
the index, and a finding at each of the two headings is what an author can act on.
`--fix` cannot repair it, which of the two is the design being editorial (RK16), and it
has to stay separate from `ref.ambiguous` rather than replace it: a pointer resolving to
two is what a reader of the roadmap hits, and that is worth saying at the line as well.

Worth deciding with it whether this is one finding or one per heading. Two is the shape
`id.duplicate` uses, and it is the one an editor can act on twice.

### §RK263 The suite that judges the tree cannot say the tree moved under it

Observed while shipping RK261: one run reported six failures, and re-running the same
source reported 1940 passed with one genuine fix between them. The six were
`test_packaging`'s two version checks, `test_plugin`'s manifest and launcher checks,
`test_provenance`'s commit check and one whose set I had actually left stale. What ran
beside them was `git worktree add` and `git worktree remove` against the same
repository, for the interleaved benchmark that measurement needed. The mechanism is not
established and this line does not claim one: what is established is that five failures
were not about the code, and nothing in their output said so. These tests exist
deliberately. This repository is the format's conformance fixture, and `test_packaging`
asserting that `pyproject.toml`, `__init__.py` and `plugin.json` state one version is
the check that keeps RK153's patch bump honest — moving them to a `tmp_path` copy would
assert about the copy. The precedent for the answer is in the file already:
`test_this_checkout_reports_the_commit_it_is_at` calls `pytest.skip` where git cannot
place the tree, because a machine without git is not a defect. The same reasoning covers
a tree that is being written while the run reads it. What to weigh: a session-scoped
fixture that records the tree's state and skips the checkout-reading tests when it
moves, against the risk of a skip that hides a real failure — which argues for reporting
the movement loudly rather than passing quietly.

### §RK268 A process-lifetime cache in a per-test world

Six functions in this package are `lru_cache`d, each for a good reason: they answer a
fact about the process — where the package lives, what a shell reaches it by, what a
stored command must say, which root a server discovered, how a line parses. None of
those change inside one run, and `invocation` in particular is read on the deny path,
the one place a repeated `which` scan would be paid for over and over.

A test that monkeypatches what such a function reads is therefore editing a value that
outlives it. The suite handles this by calling `cache_clear` by hand, at the call sites,
before and after — eleven such calls across three files, every one a thing a future test
has to remember. The failure mode is not a wrong assertion: a test raising before its
trailing clear leaves a `tmp_path` pytest has already removed cached as this machine's
launcher, so the *next* tests fail, in another file, about a path nothing in them
mentions. That is RK263's shape again — a failure indistinguishable from a defect —
reached by a different route.

An autouse fixture clearing all six is the obvious answer and the one to check rather
than assume: it makes every test pay six calls, and it hides the case where clearing is
itself the assertion. The alternative is a fixture the patching tests request by name,
which keeps the coupling visible and only helps the tests that already remembered.

### §RK269 The transition only the console saw

`ship` computes something no other verb does: whether the block it just emptied still
holds open work. It says so — `event T282 Block AI empty` — and that is the end of it.
The next verb cannot ask, and `lint`, which runs at the turn's end and is the gate an
author actually trusts, reports a clean tree either way.

Measured in a repository that keeps a per-block index beside its ledger, with an
`(active — see ROADMAP)` marker per row. Two ships emptied one block and two adds
reopened it across four commits. Each time the row had to be flipped by hand, and each
time `lint` passed on the wrong one; the discrepancy was caught by that project's own
test suite, which asserts the index against the roadmap because roadkeep does not. An
author who trusts `lint` ships the wrong row.

What is open is whether roadkeep should know about a block index at all. Three shapes,
in order of how much they claim: `lint` reporting the transition as an observation
rather than a violation; a query verb answering "which blocks are empty" so a project's
own check can be written against roadkeep instead of against a regex; or roadkeep owning
the index row the way `block add` owns the heading. The first costs almost nothing and
would have caught all four. The last is the one that needs the design.

### §RK271 An offer that cannot tell a verdict from a fault

RK86's reasoning holds: an agent that meets a limit it thinks is wrong otherwise has one
move left, which is to work around the tool quietly, and that loses the sessions with
the most to say. So every failure closes with the capture command, and the affordance
rides the exit code rather than being remembered at twenty refusal sites — one place,
which is why it is right.

What it cannot tell apart is a refusal *about the caller's prose* from a verdict the
gate was asked for. `lint` exiting 1 with `ref.unresolved 1` has already said
everything: the finding names the file, the line and the rule, and the next move is
`--fix` or an edit. Two further lines saying roadkeep itself may be wrong are the tool's
highest-traffic output — the action runs `lint`, the pre-commit hook runs `lint` — and
in neither is there a session to capture before the end of.

The split is available without a new judgement. `report`, `guard` and `mcp` are exempt
by name already, and the parsers declare which commands only read; a verdict is what a
read-only command returns when it found something, a fault is everything else. Against a
name list: the exemption is the wrong shape at three entries and would be the wrong
shape at six. What stays true either way is that a *validation* refusal keeps the offer
— that is the case RK86 measured, and the one where the limit really might be wrong.

## Block E — Adoption

### §RK285 The number that decides an adoption, taken under the wrong reading

One file, three readings. Shio's live roadmap under the defaults: `0 conform, 65 would
change`, `deps.format 96`, `id.format 63`, `ref.mismatch 63`, and "63 line(s) do not
round-trip: the tool would refuse to write this file until they are rewritten by hand".
Under `--prefix SH`: the id and dep findings go, `ref.mismatch 63` stays. Under
`--prefix SH --ref-scheme outline`: `63 conform, 2 would change`.

The backlog was conforming the whole time. Two non-goal bullets are over a limit. What
an adopter sees first is a file that has to be rewritten by hand, and RK18's argument is
that this number is taken *before* the commitment — so it is the number that decides
there is none.

Half of this is solved already. The prefix mismatch prints `also 63 id(s) spell SH,
unread here: --prefix SH if it is a track of this backlog` — misconfiguration named,
flag named, judgement left to the reader because whether a foreign prefix is a second
track is not the tool's call (L4). The scheme has no such line, though `ref.mismatch` on
**every** line is its signature and `Estimate.ref_scheme` already says "under the wrong
one a file of 151 sections yields 0".

So the shape is settled by precedent: the same sentence, one field over. What is not
settled is the round-trip line, which states a refusal absolutely while resting on a
reading the report has just questioned — the one claim here an adopter cannot discount,
and it was wrong.

## Block F — The plugin

### §RK267 A note that knows more than it says

RK155 made the MCP server say when its own modules moved after it imported them, because
a config key added in one commit made every write refuse `unknown key` while the CLI
accepted it. The note works. What it does with the relevance question is hand it back:
it lists every module `Engine.stale` found and closes with "re-run only where the
changed files are the ones that would decide this", which is the reader being asked to
know the call graph of a refusal they did not raise.

Measured while shipping RK255: a `why.too-long` refusal — decided by `schema.py`,
unchanged — arrived naming `cli.py`, `merging.py` and `provenance.py`, three modules
that could not have decided it. The note was 450 characters of correct and irrelevant
text on a refusal that had already said everything actionable in one line, and it fires
on every error in every session that edits this package, which is every session that
develops it.

The module that raised the refusal is knowable: the exception has a traceback, and the
frames above the server are this package's. Intersecting that with `Engine.stale` turns
the note from an inventory into a judgement — say nothing when the sets are disjoint,
and say which module when they are not. The risk is a refusal raised in one module
because a helper in another changed, which the intersection misses; that argues for
narrowing the sentence rather than suppressing it, and for keeping the full list behind
the one module that is named.

### §RK275 A check the agent it was built for cannot call

L5 is that every question is a command, so answering one costs no context. `merge
--check` is exactly that shape: it writes nothing, reads two facts, answers in three
lines. The MCP server exposes the query surface — `list`, `brief`, `budget`, `deps`,
`weight` — and not this one, so the agent the plugin exists for reaches it by shelling
out or not at all. In practice, not at all: nothing prompts the question, and an unwired
driver is silent until the merge it was registered for.

The reason it is absent is that `merge` is git's driver contract. Three positional
paths, a `--path`, an exit code git reads — none of that belongs in a tool an agent
calls, and the server was right to leave the verb alone. But `--check` is not that verb
sharing a name; it is a different command wearing the same subparser, which is why it
needed a flag.

The shape to decide: whether the server grows a tool for a flag — one subparser per task
is the mapping, and this the first exception — or whether `--check` becomes its own
subcommand, `merge check`, picked up by the rule the server has.

The second was argued for as cheap "before it is load-bearing". It no longer is: RK272,
RK273, RK274, RK277 and RK278 each put behaviour behind that flag, so the rename moves a
documented command with five decisions in it. Not an argument against — the measure of
what an exception would hold.
