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

### §RK131 A pre-flight is narrower than a transaction

RK116 made `save` refuse a write onto a file that moved, and RK6 says a transaction
writes all its files or none. Those two meet badly: `save` checking each file as it
reaches it would refuse the second write after the first had landed, so
`assert_all_current` asks about every target *before* any of them is written.

It asks, and then each `save` asks again. Between the pre-flight and the last write
there is still a window, and a writer that lands inside it produces exactly the
half-applied state the pre-flight exists to prevent — rarer, and not gone. The claim in
`Departure.save`'s docstring is accurate about what it buys and the mechanism is weaker
than it reads.

RK117's lock closes this for roadkeep against roadkeep, which is the case that was
measured. What is left is the case RK116 named as its own subject: an editor, a `git
checkout`, a hand edit the hook missed. For those the window is real, and the tool
currently states an all-or-nothing guarantee it holds only against writers that take its
lock.

Two honest directions. State the narrower guarantee where it is claimed, which costs
nothing and stops the docstring from over-promising. Or close it: write every file to
its scratch name first, check all the targets, then rename them in sequence — the
renames are the only steps that touch anything, and they are the ones already made one
step each by RK118.

### §RK133 The part is read and then dropped

RK121 taught the parser to read `SH96 (local half)`, and the two `deps.unknown` it was
filed for went to zero. Measured on the same tree immediately after: `id.duplicate` went
0 -> 6 and `id.two-files` 1 -> 3. Nothing in Shio changed; the ids simply became
readable, and every part resolved to the same base id. Four entries spell `SH348 (the
measurement)`, `(step 1 of 4)`, `(steps 2 and 3)` and `(step 4 - the sibling link)`: one
task delivered in four commits, which is the state RK121 exists to represent, now
reported as four answers to whether it is done. The `part` is parsed and then discarded
before anything asks what identity it confers. Two questions the fix has to answer, and
neither is obvious: whether `SH348 (step 1 of 4)` and `SH348 (step 2)` are one id or
two, and what `deps: SH348` means when three of four parts have landed. The corpus
already answers the second in prose - a line waits on the whole - so the cheap shape is
an id that is one identity with several entries, and a duplicate check that counts parts
as one. RK122 is the same question one file up.

## Block B — Authoring

### §RK120 Two branches spending one address

`renumber` was written on the observation that an id is an address and a merge can spend
one twice. It is the repair. Nothing makes the collision visible, and nothing makes the
merge that produced it survivable.

Two worktrees on two branches each scan their own tree, each derive the same next id,
and each append under the same block heading. Git sees two insertions at one line and
writes a conflict into a file whose only legal writer is this tool — so the resolution
is a hand edit of the format, which the hook denies and the gate refuses. Worse is the
case that does not conflict: two branches touching different blocks merge clean, and the
duplicate id lands silently for `lint` to find later.

The file is a schema, which makes a structural merge decidable where a textual one
guesses. Entries are keyed by id and grouped under declared headings, so a driver can
take the union of both sides, keep each side's line wherever the id is unique to it, and
single out only the ids both sides spent — moving one of those with `renumber`, which
already carries the section and the dependents along (RK113 first, or the merge inherits
a half-renamed subtree).

Registered per file in `.gitattributes`, it is opt-in configuration (L6), and it gates
itself: a merge whose output `lint` refuses falls back to the conflict markers rather
than writing a file nobody reviewed.

### §RK123 The prose of a live task is the one thing no door opens

`amend` reaches a line's `why`, `deps` and `ref`. `section drop` is refused while an
open line points at the anchor — correctly, since that section is `ship`'s to remove.
`section add` refuses an anchor that already exists. And the plugin's hook denies a
hand-edit to any governed file. The union is a gap: **the rationale of an open task
cannot be changed at all**, by anybody, until it ships and the section is deleted.

Found twice in one session on Shio, both times on a ⏳ line. An investigation eliminated
one of its two hypotheses and narrowed the other; the section still states both as open,
and the sentence that would have said so had nowhere to go. That is the ordinary case,
not an edge one: a design under a marker that is not ✅ is *expected* to change, and
partial delivery (RK121) is the shape where it changes most.

The verb is small — `section amend <anchor>`, the body on stdin, revalidated against the
width and the word budget exactly as `add` validates it. What needs deciding is whether
an amend that rewrites the whole argument should be refused in favour of a new task,
which is the same question `amend` already answers for `symptom`.

### §RK124 The ledger has an insert and a delete, and no update

`record` has two doors, `add` and `drop`. The roadmap has `amend` for exactly the reason
`record` does not: a `why` written under pressure is the field most likely to be wrong,
and the cost of being wrong should be one command.

Today it is two, and they are not equivalent to one. `drop` removes the entry and `add`
appends a new one under its block, so a correction **moves the line** — a ledger read in
the order work landed stops being one, and a reviewer diffing the file sees a deletion
and an insertion where a word changed. On a shipped entry the loss is worse, because
`ship` wrote it from a roadmap line that no longer exists to re-derive it from.

`record amend <id> --why` is the missing half, validated at input the way `add` is.
Whether it may also touch the block is the open question: an entry filed under the wrong
block is a real mistake and moving it *is* a move, so that half may honestly belong to a
separate verb rather than to a flag that pretends nothing happened.

### §RK126 The ledger's unit is the entry, and the damage is smaller than that

`lint` finds four line-level defects in Shio's ledger and describes them exactly: two
`U+0008` control characters inside an entry's continuation line, an entry naming a file
the repository no longer contains, a bullet with no `—` separator, and a duplicate id.
Shio's own rationale calls them "corruption rather than prose, and `lint --fix` does not
touch it" — which is true, and the reason is worth stating: **nothing can**.

Every write verb takes a whole entry. `record add` appends one, `record drop` removes
one, `ship` writes one from a roadmap line, `retire` writes a departure. The damage is a
character inside an entry somebody wrote correctly two years ago, and the only
expressible repair is to delete that entry and write it again — losing its position, and
requiring whoever fixes a control character to retype 900 words of history.

The guard makes it airtight: it denies `Edit` on the file, and the four commands its
refusal names are the four above. A guard that says "call these instead" has to be right
that one of them applies.

The smallest honest shape is `lint --fix` growing the cases that need no judgement — an
invisible control character has one correct reading, and a missing separator has one.
The link and the duplicate need a decision and should stay reported.

### §RK127 Two entries for one id are not always one entry twice

`record drop` removes "the later of two ledger entries for one id", and the guard's own
refusal text advertises it as the answer "when the ledger says it twice". That reading
holds when a duplicate is a slip — the same work recorded again.

Shio's `SH347` is the other kind. One entry records an unplanned fix (Spring's
context-cache ceiling raised to 64 after an unrelated test failed) and ends by saying
what it left open: *"the ceiling is silent"*. The other records exactly that, shipped
later, with the test that made the ceiling visible. Two true entries, two different
deliveries, one id — because the first was written by hand before `record add` existed
to give unplanned work an id of its own.

Dropping either destroys a delivery, and the verb picks the **later**, which here is the
entry that actually earned the id from a roadmap line. Running it on this corpus
produces the wrong file and reports success.

What is missing is a way to say *this entry is different work*: a renumber for the
ledger, the counterpart of the one the roadmap has. Related to RK121, and not the same —
that one is a task in halves under one id, this one is two tasks that were never one.

### §RK129 Retiring the rest is not a verdict on the half

RK121 gave `_depart` a completion path: a ledger entry carrying a qualifier is not a
second record of one decision, it is the first half of this one, so the entry is
replaced rather than added to. That is right for `ship`, whose entry describes the whole
of the work that the partial described part of.

`retire` reaches the same code with a different marker, and there replacing is a
deletion. Run against a task whose `✅ **RK1 (local half)**` is already in the ledger, it
leaves `🗑 **RK1** — abandoned: …` and nothing else: the sentence describing what
actually shipped is gone from the file whose whole job is to answer "what happened to
this".

The two are not the same decision. Completing says *the rest landed too*, and
superseding the partial's sentence is honest. Retiring says *the rest never will*, which
leaves the half that did ship as history — the kind `drop` refuses to remove even when
the id is stated twice, because removing the only record of a decision is deleting
history rather than de-duplicating it.

The narrow answer is a refusal: a task with a recorded part cannot be retired until
somebody says what to do with the entry that exists. The wider one is a second entry,
which `lint` reports as `id.duplicate` today and which RK127 is already about. Either
way the choice belongs to the author, and the current behaviour makes it silently.

### §RK130 The middle state is loud, and has no door

RK118 ordered a departure's three writes so that every state a crash can leave is loud
and lossless: the ledger goes first, so stopping after it puts the id in two files,
which `lint` reports as `id.two-files`. Nothing is lost and the gate names it. What
RK118 did not establish is a way out.

Three commands look like the way out and none of them is. `ship` sees an entry the
ledger already holds and raises `AlreadyRecorded`. `Closure` (RK62) exists for exactly
this shape and is unreachable, because `_already_recorded` requires the roadmap line to
carry ✅ or 🗑 — the marker that says it was already treated as gone — and a line a crash
left behind still carries 📋. `record drop` refuses unless the id is recorded **twice**,
which it is not.

So the author is left with the edit the hook denies, on the file the tool exists to own.
That is the shape of every defect in Block B: a state the tool can produce and cannot
undo.

The condition to widen is `_already_recorded`'s, and widening it is not free — its
current narrowness is what stopped `ship` from closing Shio's live `⏳ SH238` and
deleting a real task with a 224-word section. What separates the two is the *ledger*
side rather than the roadmap's: an entry written by this tool for a line still open is a
leftover, and an entry naming a half is not. Which is the distinction RK121 just made
representable.

## Block C — Query

### §RK119 One backlog, two workers, one answer

Tier 1 is the reason `pick` is not simply "lowest": a 🛠 line says someone started, and
picking around it leaves work half-done. That is exactly right for one worker and
inverted for two — the second agent to ask is handed the line the first is holding, with
the tier name saying so, and starts it.

Tiers 2 and 3 are no better. They are pure functions of the file, so N callers reading
an unchanged file get N identical answers. Nothing in the current design is wrong; it
answers a question that assumed a single reader.

What the backlog cannot express is *taken*. The marker set can say in-progress, which is
about the work, not about who holds it or whether the claim is still live. A claim is a
write — flip the marker inside the same serialised transaction that answers, so the
answer and the claim are one step and the next caller reads a file that already moved.

Two things this must not become. A claim held by nobody is a task nobody can pick, so it
needs an expiry a later caller can see and step over, rather than a lock nobody can
break. And an owner field would be a schema change carrying a fact that lives outside
the repository — what is durable is *claimed*, and the identity behind it belongs in the
commit.

## Block D — The gate

### §RK104 The block the gate does not read

RK39 made the README's status table derived rather than restated, on the argument that a
README which repeats a backlog it cannot re-read is stale from the first ship. The
derivation shipped; the gate over it did not. `lint` reads the four governed files and
the every-turn budgets, and never opens the README at all — so a commit that ships a
task and forgets `export --readme` leaves a table contradicting the ledger, and the gate
passes.

What catches it here is `test_this_repositorys_readme_is_current`, a pytest fixture in
this repository. An adopting project installs the plugin, not the test suite, so it has
the command and nothing that runs it. That is the arrangement RK39 was written against,
one file over: a restatement whose currency depends on somebody remembering.

The check is cheap because the write already exists — splice the derived block into the
file in memory and compare. Equal is silence; different is one finding naming the
command that repairs it, which puts it in `--fix`'s territory rather than the
editorial's, because the block is derived by definition.

Measured on this repository across four commits: the generated block stayed correct
every time, and the hand-written paragraph beside it went stale three times. So the gate
wants the marked block, which is checkable, and the prose around it is a different
question that a word budget and not a diff would answer.

### §RK105 A property test over somebody else's working tree

L3 is proven over real files, and the two live corpora are what make that more than a
self-test: they supply the dep kinds, the outline scheme and the marker sets this
repository's own docs never exercise. The tests read them where they live, and skip
where they are absent, which is what lets CI run the same suite.

What that misses is the third state. A corpus that is present *and changing* is read
mid-edit: one run this session failed on a Shio pointer resolving to nothing, and the
same test passed alone, before the change, and on every run after. Two other tests began
skipping in the same window, for the opposite reason — Shio's roadmap now conforms, so
there is no adoption cost left to estimate.

Both are correct readings of a file that moved. The defect is that the suite reports
them as a verdict on this commit. A gate whose red is sometimes about another repository
is a gate whose red gets re-run instead of read, which is the failure `lint` already
names for findings nobody can act on.

The material is already there: the corpora are git checkouts, so a read at a pinned
revision is a read that cannot move underneath the run, and `lint --baseline` (RK84)
established that this tool can read a file as it was at a revision. Reading the live
tree stays worth doing — as an advisory run, not as the assertion.

### §RK114 The sub-anchor the ownership check cannot see

`_owners` decides who a section belongs to by matching its anchor against the project's
id pattern. Under `ref_scheme = "id"` that pattern is `RK\d+`, so `§RK34.1` does not
match; its title names no id either, and the section comes back owned by nobody.

That is deliberate for `§0.1`, and written down as such: prose belonging to no task is
nobody's orphan. The cost is that the rule cannot tell the two cases apart. A sub-anchor
under the id scheme is *derived from* an id — `RK34.1` is `RK34`'s subsection and the
anchor says so — but the check reads it the way it reads an outline heading, which is to
say not at all.

The consequence is measured rather than argued: after `renumber RK1 --to RK9` left
`§RK1.1` behind, `lint` reported the file clean, two sections. Neither side sees it. No
pointer resolves to a sub-anchor, so `_pointers` cannot; `_owners` exempts it, so
`_orphans` does not.

What the anchor already spells is the fix's whole input. The parent of `RK34.1` is
`RK34`, which `_extends` reads segment by segment for `section add` today — the question
is asked one module over and never here.

### §RK122 The gate reports the one project that did not hide it

`id.two-files` says "open and recorded as gone are not both true". For a task delivered
in halves both *are* true, and the finding has no way to be told so.

The evidence is one corpus, read twice. Shio's SH238 is ⏳ in the roadmap and carries a
bare id in the ledger, which is the honest way to write a half — and it is the only one
`lint` reports. Six others are in the same state and are silent, because their ids carry
a parenthetical the parser cannot read (RK121). The gate therefore reports **precisely
the entries written correctly** and passes the ones that defeated it.

That inversion is the argument for doing this with RK121 rather than after it: a finding
whose only avoidance is a syntax error teaches the syntax error. Whatever form partial
completion takes, this rule has to read it and stay quiet, and stay loud for the case it
was written for — a line somebody shipped and forgot to delete.

### §RK132 The write that has no document behind it

Every write to a governed file now asks whether the target is still the file that was
read (RK116) and lands in one step (RK118), because every one of them goes through
`Document.save`. `export --readme` does not. `_splice_into` opens the README, splices
the projection between the two roadkeep markers and writes the result, and the only
thing it shares with the mechanism is `write_atomically`.

The window is small — a read and a splice — and it is the same window the whole of RK116
is about, on the one file this tool edits that it does not own. A README is also the
file most likely to be open in an editor while a command runs, which is precisely the
writer a lock does not order.

Nothing here needs a `Document`: the README is not governed, its lines are not task
lines, and parsing it would be claiming a format it does not have. What is needed is the
same question asked by hand — remember the bytes that were read, compare them before the
rename — which is three lines and the refusal the CLI already renders for `StaleFile`.

This is not RK104, which is about the gate: that a stale README passes `lint` is a
different failure from a fresh README overwriting somebody's edit. They share a file and
nothing else, and fixing either leaves the other exactly as it is.

### §RK134 Two readers of one fact, disagreeing

Reproduced minimally: a heading `### II.1 Shared design (ZZ1)` whose only named id has
shipped, with two open lines carrying `-> II.1`. `lint` reports `section.stale` - "ZZ1
is in the changelog and this rationale is still here" - and `section drop II.1` refuses,
naming ZZ2 and ZZ3 as the lines whose pointers would stop resolving. Both are behaving
as written: `_unowned` reads the ids in the title (RK61) and `drop` reads the pointer
index. Shio's `VI.1` is the live case, where SH22 shipped and SH44-SH47 are still open
against the same design, and the only way out was to retitle the heading by hand so the
pointers and the title agreed. RK64 already settled this question for `ship`: a section
another open line points at is kept, and the reason is reported. The gate never learned
it. A finding whose remedy the tool refuses is worse than no finding - it is the shape
RK16 splits mechanical from editorial to avoid - so the fix is to give `_unowned` the
pointer index it already builds, and to say "still pointed at by" rather than "survived
a hand edit".

### §RK135 The dead draft no check can see

Shio carried `XV.21` and `XV.22` under the same title - "A raster is still the only
answer to most of 'looks wrong' (SH265)" - one an earlier draft of the other. SH265
points at `XV.22`. `section.orphan` did not fire, because the id in `XV.21`'s title is
an open line; `section.duplicate` did not fire, because the anchors differ;
`ref.unresolved` did not fire, because the pointer resolves somewhere. Twenty-three
lines of superseded design lint clean, and the only reason it was found is that a reader
happened to compare two adjacent headings. Reproduced minimally in four lines of
fixture. The check that is missing is cheap and already has both halves in hand: a
section whose title names an id, where that id's pointer resolves to a *different*
anchor, is a section nothing can ever reach. It is not the same as an orphan - the task
is alive - and the remedy is different too, because one of the two is the design and the
other is history, which is a reading rather than a deletion.

### §RK136 A budget for prose, applied to a table

`sections.words` is `len(body.split())`, so every cell of a Markdown table costs what a
word of argument costs. Measured while adopting Claude Tray: its `III` is 269 words of
which 230 are the measured-baseline table the file keeps *because it is data, not
design*, and its `XVI.3` is 293 of which 72 are a timing table. Both are under 250
counting prose alone. The remedy the finding offers - "this is two sections, or a
paragraph that belongs in the commit" - is advice about prose, and neither applies:
splitting a six-row measurement in half helps nobody, and the rows are the evidence the
design rests on. The adoption ended by declaring `section = 300`, a number that
describes two tables rather than budgeting anybody's prose, which is the outcome L6 is
supposed to prevent. What the limit is for is an agent's attention on an argument, so
the honest count excludes what is not argument: a table, a fenced block, a blockquote of
somebody else's words. `sections.structural` already knows how to recognise the first
two.

## Block E — Adoption

### §RK103 The marker slot that holds two tokens

`- [ ] **C40** · …` is GitHub's task-list syntax, which is what a Markdown backlog looks
like when nobody chose a format. The parser reads the bullet's first
whitespace-delimited token, which is `[` and never `[ ]`, so the line matches no marker.
Neither guard that catches a line claiming the task shape then fires: one wants the bold
id second, and `[ ] **C40**` puts it third; the other wants the bullet to open with the
bold. So the line is prose — counted by nothing, rejected by nothing.

Measured on cursarei: 16 such lines, **0 entries and 0 rejects**. That is the shape of
Shio's 920-bullet changelog, the miss the reject list was built to end, reappearing one
shape further out.

The answer is a reject and not a reading. Declaring `[ ]` in `[markers]` is the wrong
door: the slot is one token by construction, and widening it to two makes every two-word
prose bullet a candidate. What is owed is a reason — a bullet whose first token opens a
bracket its second closes, with a bold id after, is a task line in another convention,
and saying so costs no grammar.

`adopt` then names it as it names a table row: counted, and inside what would change. A
backlog this tool cannot read is a fact an estimate has to state, because the one answer
it may not give is the answer an empty file gets.

### §RK107 Adopted, and ungated

RK21 shipped the configuration to two more projects and stopped there, which both
configs say out loud: *NOT WIRED INTO CI, AND NOT READY TO BE*. That was honest at the
time and it is the half that matters least — a declaration nothing checks is the
convention this tool was built to replace, one file further in.

The two are not the same job. **Dumont** reports 9 findings, all `id.format`, so it is
one task away from a clean gate and then the action this repository already ships runs
green from day one. **Turing** reports 407, and a repository cannot adopt a gate it
fails on the first commit — which is what `lint --baseline REV` (RK84) exists for: the
same gate over the difference alone, so 407 standing findings become an exit code about
the commit that introduced the 408th.

So the outcome is two green checks and no rewriting: Dumont on the plain gate once its
ids are legal, Turing on a baseline pinned at its adoption commit. Neither asks anybody
to fix a line, which is the property that makes a late gate adoptable at all.

What it proves is the claim RK21's ledger entry stops short of. Four projects carrying a
config is four projects that agreed; four projects failing a build on the format is four
projects that cannot drift from it, and only the second is a standard.

### §RK110 The delta the estimate does not name

`adopt` on Dumont's roadmap reports `id.format 5`, and one line above it reports the
prefix the ids actually spell — `also 5 id(s) spell RK, unread here: --prefix RK if it
is a track of this backlog`. That second line is the shape the report already has for a
config delta: a count, and the key that would close it. `undeclared` does the same for
`[markers]`, naming the tokens sitting in the marker slot that the project has not
declared.

The id shape has no such line, so the five findings arrive as five defects rather than
as one unwritten key. Confirming that `[ids] pad = 2` clears them, and clears nothing
else, meant loading the config, `dataclasses.replace`-ing the schema and diffing two
lint runs by hand — for Dumont, 9 findings to 0; for Turing, 4 of 361 to 0. That is the
throwaway script RK99 already names as the thing the estimate replaces, written again
for a different column.

What the estimate can say without a model: how many ids carry a leading zero and at what
widths, and how many end in a lowercase letter. Both are counts over strings it has
already parsed. Whether a corpus that pads *sometimes* should declare a width is a
judgement, and stays the reader's — the report says what the ids spell, as it does for
the prefix, and never that the project should therefore declare it.

### §RK125 The declaration that makes a file parse removes a verb

`[ledger] marker = false` exists so a ledger written before this tool can be read at all
— Shio's 234 entries carry no marker, and declaring it is what lets 96 deps resolve
instead of reading as "in neither file". It is adoption working exactly as designed.

The cost is undeclared and total: `retire` refuses every id with `status:
status.unrepresentable`, because `🗑` cannot be told from `✅` in a file with no marker
column. So a project that adopted the tool the recommended way loses the ability to
record a line leaving without shipping — one of the three doors RK's own design says the
roadmap has, and the two undocumented ones were the reason `retire` was written.

The refusal is honest and it is a dead end: it names the config and stops. At least
three ways out, and the choice is a design decision, not a patch — carry the marker on
retired entries only, since a file with no markers has nothing to be inconsistent with;
or write the retirement to the roadmap rather than the ledger; or refuse at `adopt`
time, so a project learns the cost before it inherits it rather than the first time it
retires a line.

### §RK137 The one fact the skill still gets wrong

`install` states its own contract: every byte is a translation of what the plugin ships,
"the launcher's path being the only substituted fact". The skill is the one surface
where it is not substituted. `skills/roadkeep/SKILL.md` says "`roadkeep` is the
installed entry point - `python -m roadkeep.cli` when it is not on PATH", and for a
project wired to a checkout both are false: the package is not installed, and the entry
point is `<path>/scripts/roadkeep.py`, which the same command already computed and wrote
into `.mcp.json` and into three hook entries. Verified on a real adoption: `roadkeep`
resolves to nothing on the machine, so every shell example in the copied skill is a
command that fails. The MCP tools carry the write path, so nothing is broken until an
agent falls back to the shell - which is exactly when the skill is being read. The fix
is the substitution the module already performs three times, applied to the one line
that spells the entry point, and `--check` then holds it in step like the rest.

### §RK138 A wiring with no way out

Claude Tray was wired to a sibling checkout and then moved to the plugin, which is the
ordinary path: an early adopter develops against a checkout and switches once the plugin
is installable. There is no verb for the second half. `.mcp.json`,
`.claude/settings.json` and `.claude/skills/roadkeep/` had to be removed with `rm`, and
the only reason that was safe is that `install` had *created* all three, so the
pre-existing state was "absent". Had the project already declared another MCP server or
another hook, the correct edit would have been to remove this project's entries and keep
everything else - which is precisely the surgery `install` performs on the way in and
refuses to describe on the way out. `--check` makes the asymmetry plainer: it reports
what would change and exits non-zero, so the tool can already see the difference between
wired and not. What is missing is the verb that acts on it, with the same rule the write
path has - the declarations keep everything that is not this project's entry, and a file
that is not a JSON object is refused rather than replaced.

### §RK139 The half of the roadmap the estimate does not read

`adopt` exists so the cost is known before the commitment: it reads the lines, names the
longest field against its limit, and never fails, because "an estimate that exits 1 is a
gate". It reads one of the roadmap's two kinds of bullet. Measured on Claude Tray:
`adopt` reported 18 lines over on `why` and `line`, the adoption was decided on that,
and `lint` then produced nine findings nobody had been shown - two bullets with no
parseable lead at all, one lead at 72 characters against 60, and six reasons over 200,
the worst at 1,100. That is a third of the work, discovered after the config was
written. `[non_goals]` is opt-in for RK66's reason, which makes measuring it *more*
useful rather than less: the number an adopter needs is what the limit would cost, and
today the only way to get it is to declare the table and run the gate. The estimate
already has the parser - `scoping.read` - and the same shape of answer to give: how many
bullets parse, the longest lead, the longest reason, and what would change.

### §RK140 A gate that is red before it is read

The workflow is written once and then the adopter's, which is right - it takes a
`directory:` and a `baseline:` this command cannot know it wants. But the default it
ships is the strict one, and the projects that most need the gate are the ones with the
most standing debt. Shio is the case: after a session of repair it still holds nine
sections over budget and three findings that are this tool's own open defects, so the
workflow as written would be red on every push from the day it lands. The workflow
committed there sets `baseline: origin/main` by hand, with a comment saying which
findings it is deferring and when to drop the line. `install` can tell the difference
without being told: it can run `lint` while it writes, and a project that is already
clean gets the strict workflow while one that is not gets the baseline plus a comment
naming the count it deferred. That keeps the recommendation honest in both directions -
a red nobody reads is the failure mode, and so is a baseline nobody remembers to remove.

## Block F — The plugin

### §RK111 An id the deriver never mints

`serving.py` whitelists what an agent may set, and `add --id` is deliberately outside
it: it "would let a caller choose an id the tool derives, which is the one thing a
schema cannot then check". That reasoning held while every legal id was one the counter
could produce.

RK106 broke it. A sub-letter is never derived — `spell_id` counts, and `T24b` is a split
of a number already cited in commits and issues. So on a project that declares `[ids]
suffix`, the write path an agent is told to prefer cannot produce a legal id, and the
skill's own instruction for a split is a CLI invocation the MCP surface has no tool for.
The declaration is readable by the gate and writable only by a human at a terminal,
which is a split between the two surfaces this project does not otherwise have.

The check the original reasoning wanted already exists twice over: `add --id` refuses an
id any configured source mentions, and `id_pattern` refuses one this project's shape
does not admit. What stays unchecked is only whether the caller *should* have chosen
rather than derived — and where a sub-letter is declared, deriving is not on offer.

Narrowly, expose `id` only where the project declares a shape the counter cannot reach;
bluntly, expose it always and let the two refusals do the work. Which is right is the
open question, and the narrow one has the cost that a tool schema then varies by config.

### §RK128 The boundary the guard defends has one side open

`guard` reads a `PreToolUse` payload and denies a governed path with a refusal naming
the verb to call instead. It matches on the tool: `Edit` and `Write` carry a
`file_path`, so they are checked. `Bash` carries a `command`, and the payload is
answered with silence.

Verified against this project's own hook on Shio: an `Edit` payload naming
`docs/CHANGELOG.md` is denied with the four-verb refusal; a `Bash` payload whose command
writes the same path returns nothing at all. Any agent that reaches for `sed -i`, `python
-c`, or a heredoc rewrites the ledger with no refusal, no record, and no lint until the
`Stop` payload — which reports the damage as findings rather than preventing it.

This is not an argument for parsing shell. It is an argument for the guard **saying**
what it does not cover, because the refusal it prints reads as a boundary rather than as
a filter over two tool names — and an agent told "roadkeep owns its writes" will believe
it.

Three options, cheapest first: name the gap in the refusal text; match a governed path
appearing anywhere in a `Bash` command and deny on the suspicion, since a read is served
by `brief` and `show` anyway; or let `Stop` compare the governed files against `git` and
refuse a change no verb in this session made.
