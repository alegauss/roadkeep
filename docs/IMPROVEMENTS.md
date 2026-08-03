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

### §RK179 The half of a sentence the parse never held

RK157 gave `Entry` a span and used it where a write inserts or removes, and left
`replace_task` on the first line deliberately: every field the schema renders was read
off that line, so replacing the whole span with one rendered line would delete prose no
task holds.

That argument is right about an id and wrong about a sentence. Reproduced on a
three-line entry: `record amend SH1 --why "It works now."` wrote the new sentence on
line one and left `on a second line, and finishes` / `on a third one.` beneath it, so
the entry states an outcome followed by the tail of the problem it replaced. The command
printed the first line and called it amended, which is the report that hides it.

The parse is the root: a wrapped entry's `why` is only as much of the sentence as fits
on one line, so the field the author is shown and the field the file holds are different
lengths. `_one_entry_twice` inherits it, calling two entries the same when only their
first lines match.

Three shapes, and choosing is the task. Refuse the correction on a wrapped entry, naming
the lines the tool cannot reproduce — loud, and leaves Shio's 146 uncorrectable. Or read
the whole span into the field, so the sentence the file holds is the one the schema
charges. Or take the span and the new text together, so a correction says how many lines
it replaces.

### §RK180 Half a derivation is a heading in the wrong place

RK166 made the level of a *new top level* the file's own, and left `NESTED_LEVEL = 3`
for everything under it — stated as being what every caller already got, and out of
scope there. It is the same defect one level down.

Reproduced on a file whose top level is `###` and whose designs are `####`, which is the
shape a project gets by nesting its rationale under a `##` part heading: `section add
XXI.6` wrote `### XXI.6`, a *sibling* of `### XXI`. Nothing refused it and the answer
reported a section placed.

A heading at the wrong depth is not cosmetic, because depth is what says where a section
ends (RK115). `find` no longer owns it, `nested` does not report it, the budget charges
the parent for prose it no longer contains, and `section drop XXI` takes the parent and
leaves this one behind — an orphan under whatever precedes it, which is the outcome RK9
calls worse than deleting too much.

The narrow fix is the one already written for the top level: read the depth off the
sections this file declares at the same number of segments, and fall back to one under
the parent that was found. Both facts are in hand at the moment of placement —
`_extended` has already resolved the parent's heading, and that heading's level plus one
is the answer no default can be right about.

### §RK181 One address for a file, and three spellings of it

RK14 fixed the form of a report: name the place as `file:line:column`, so the reader
acts on the address rather than on the consequence. `lint` does, and `config.relative`
is the one function that renders it — every refusal on the line files goes through it.

The prose file's refusals do not. `NoSuchSection`, `SectionClaimed`, `SectionOccupied`
and `AnchorClaimed` are handed `str(document.path or "")`, which is absolute, while
`_placement` hands `UnknownBlock` a bare `document.path.name`, which loses the
directory. Three spellings of one address, in one module, and the widest of them is what
an agent reads first — measured while shipping RK169, where the refusal ran past the
terminal width on the path alone.

None of the three is wrong about the file. What they cost is the thing RK14 bought: an
address that pastes into an editor, is stable across machines, and is the same string
the gate reporting the same file will print a moment later.

The obstacle is real and is why it stayed: `drop` takes a `Document` and not a `Config`,
so it cannot relativise anything. So either the caller renders the address and passes it
in, the way `ship` already passes `claimed`, or the refusals carry the path and the CLI
renders it at the boundary where a `Config` exists.

## Block C — Query

### §RK174 One parser, fifty-two times

Measured: 26 tools, 52 `build_parser()` calls, 165 ms for one `tools/list`. Half of that
is RK168's derivation — `descriptor` resolves the subparser for the schema and
`Tool.writes` resolves it again — and the other half was already there, because
`_subparser` has always built the entire CLI to reach one subcommand.

It is the first message a client sends, so the cost lands on every session that loads
the plugin, and it buys nothing: the parser is a pure function of the code. Nothing here
is *wrong* — the schema and the hint are both derived, which is what RK24 and RK168 were
for — so this is only about paying for the derivation once.

The shape is a parser built once per `descriptors()` call and indexed by subcommand
path, which is what `_subparser` walks to anyway. Two things to keep while doing it:
`descriptor(tool, config)` is public and called with one tool in tests, so it cannot
require a prepared index; and nothing may cache across calls, because `mcp` re-reads the
config per message on purpose and a memoised parser is the one thing that would stop a
mid-session edit from being described.

Worth measuring afterwards rather than assuming: if the remaining cost is the parser's
own construction, the number to report is one build, not fifty-two.

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

### §RK146 A control character with a rendering

`suspect` is defined by Unicode category rather than a hand-kept list, which is the
right call: a format character nobody has met yet is caught too. It also catches U+0009,
because a tab is `Cc` — and the message it prints is *"invisible in an editor, so every
other diagnosis of this line names the consequence instead"*, which of a tab is simply
untrue.

RK126 then had to withhold it from `--fix` for a reason that is also right: the
indentation of a nested line is read off the file and written back verbatim (RK49), so
deleting a tab re-parents somebody's task. The two correct decisions leave a project
that indents with tabs holding a `char.invisible` per line, permanently, cleared by no
command — a standing finding, which is what teaches a reader to stop reading the report.

What separates a tab from the rest of `Cc` is that it **renders**, and the gate already
knows that distinction: `removable` was written to name it. So the report should read it
too — either by exempting a tab from `suspect` outright, or by giving it a finding of
its own that says what is actually wrong (a tab where the format writes spaces) and can
be fixed where the line's `indent` is empty. Which of those is right depends on whether
any live corpus indents with tabs, and that is a measurement this task should take
first.

### §RK147 The limit the writing door does not read

L1 is the project's first law: the schema is enforced **where the text is created**, and
`lint` is only the backstop. RK50 made the limits declarable per file,
`[limits.improvements]` beside `[limits.changelog]`, and `Config.schema_for` is what
resolves them.

The section write path does not call it. `sections._check` reads `config.schema` — the
project's top-level numbers — while `linting._budget` charges
`prose.schema.section_max`, which came from `config.document(role)` and therefore from
`schema_for`. So a project that declares a *tighter* rationale budget gets it enforced
only after the paragraph exists, which is the exact failure L1 names; and one that
declares a *looser* one has `section add` refusing prose the gate would accept, which is
worse, because a refusal on legal text is a refusal an author routes around.

Neither half was visible here: this repository declares `[limits] section` and no
per-role override, so both readings return the same number and the fixture proves
nothing. That is the finding as much as the bug is — the conformance corpus has no file
whose own limits differ, so one has to be added with the fix, or the next per-role
declaration will find the same seam.

The fix itself is one argument threaded through: `_check` takes the role, or takes the
schema the caller already loaded the document under.

### §RK172 A pointer addresses a governed prose file, and the gate knows one

Measured adopting Turing. Six open lines in its GEO block carry `→ §X.3` and `→ §X.4`,
and the block's own preamble says what they mean: "`→` pointers are STRATEGY §X." Both
exist — `docs/STRATEGY.md` declares `### X.3 Content calendar` and `### X.4 Measurement`
— and `lint` reports `ref.unresolved` on all six, because it resolves a ref against the
improvements file and no other.

**The seventh line shows the cost.** T354 carries `→ §X.1`, and an unrelated `§X.1` exists in
the improvements file — "Why bypass Spring AI for some features". So instead of a false
`ref.unresolved` it gets a silent false *match*: `_budget` charges a **pointed** section with
its whole subtree, so that one is billed 365 words for prose about a GEO task, and splitting it
into four subsections moved the number *up* by five. A finding that cannot be cleared by doing
what it asks is worse than a missing one.

Nor can the six be cleared honestly: the only ways to satisfy them are to repoint a line
at an unrelated section, or to move positioning prose out of the file the config
declares for it.

`[files]` already declares strategy as a governed role, so a pointer addressing it is in
the model — the gate is the only part that does not know. Resolve against every declared
prose role, and let T354 say what to do when two roles declare one anchor: name the
ambiguity, never read the first and bill it.

### §RK173 A path is relative to something, and the root is a guess

Measured adopting Turing. Eight `path.missing` findings, and six name files that are in
the repository: `./package.json` and `scripts/prerender.mjs` resolve under
`frontend/apps/site/`, `references/return-policy.md` and `scripts/rma.py` under
`frontend/apps/showcase/skills/returns-rma/`, and two more carry a `#L35` line anchor
that is part of a GitHub URL rather than of a filename. Only two are genuinely gone.

A monorepo entry writes the path its reader is standing in — the frontend app, the
showcase skill — because that is the path a developer pastes from a terminal already
inside it. The check resolves from the repository root and reports the difference as a
missing file, so the signal-to-noise is 2 in 8 and the finding class stops being read.
Worse, it points at history: these are shipped ledger entries, so the remedy the wording
implies is editing what already happened.

Two candidate fixes, and the cheap one may be enough: treat a path as satisfied when it
resolves anywhere the repository declares a module root, or let `[paths]` declare the
roots to try. Stripping a `#L…` anchor before the existence test is separate, smaller
and unambiguous. Either way the class needs to distinguish "the entry is wrong" from
"the entry is relative", which today it cannot.

### §RK182 A property test is only as wide as its corpus

The round-trip property is the tool's ownership test (L3), and it is a property test
over real files precisely because the corruption it guards against is the case nobody
thought to write an example for. `FOREIGN` lists two files: Shio's roadmap and Turing's.

RK157 was in neither. Its shape is a bullet that wraps, and a governed roadmap has none
by construction — the format has no multi-line task line. Counted while fixing it: 146
of Shio's 290 ledger entries wrap, and 3 of Turing's 801. So the one place the shape
occurs at scale is the one kind of file the corpus does not read, and the property
passed on every file for as long as the defect existed.

What extending it costs is the reason it was not done in that commit. A ledger written
before the tool needs the rules that hold a `why` to one sentence turned off for the
role, so the schema each file is read under stops being one line in a list. And RK105 is
already open about foreign trees turning this suite red for a change nobody here made —
two more files is twice the exposure.

Which makes the honest order visible: RK105 decides how a foreign file is read at all,
and this one is what that decision is worth doing for.

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

### §RK148 The fifth surface nobody is told about

RK100's whole argument is that a vendored surface nobody keeps in step is worse than
none, and `install` exists so an adopting project gets every one of them derived from
what the plugin already ships. RK120 then added a fifth: a git merge driver, registered
per file in `.gitattributes` and per checkout in `git config`, opt-in because it is
configuration (L6).

Opt-in is not the problem. Being unmentioned is. An adopter runs `install`, reads its
report, and is told about the server, the guard, the skill, the workflow and the
`CONTRIBUTING.md` line this tool will not write — and not that a driver exists. The
failure lands later and looks like the tool's fault: two worktrees spend one id, git
writes conflict markers into the roadmap, and the resolution is the hand edit the guard
denies.

The narrow shape is a line in `install`'s `skipped` report, beside `CONTRIBUTING.md`, naming
`merge --register` and why it is not run — the `git config` half writes outside the files this
tool was given (L2), so it is named there for the same reason. The wider one is `install
--register-merge` doing both halves for a caller that asks, which is a decision about somebody's
git configuration and should stay a flag rather than a default.

## Block F — The plugin

### §RK175 The half of the boundary that asking does not close

RK128 gave the guard three options and took the second: match a governed path in a
`Bash` command, and answer `ask` because `deny` would refuse `git add docs/ROADMAP.md`.
That closes the *silence* — an agent reaching for `sed -i` is surfaced instead of
passing unnoticed.

It does not close what the third option was about. Once the user approves, the only
thing left is `review`, which runs `lint` narrowed to the lines the turn changed. A
hand-edit producing a **conforming** line passes: the annotations are right because
nothing was inserted, the pointer resolves because the anchor existed, and a reworded
`why` is a legal `why`. The file changed, no verb wrote it, and every gate agrees it is
correct.

The third option was to compare the governed files against `git` and refuse a change no
verb made. That needs what the process does not have: a record of which verbs ran. Every
write prints an `event <id> Block <x>` line (RK38) and `capturing` (RK85) replays a
session's facts, so the material may exist — whether a turn-scoped ledger of verbs is
worth holding is the open question.

Worth deciding against the honest alternative: that this is what `ask` is for, and a
user who approved a `sed` made a choice the tool should not re-litigate at the end of
the turn. That reading is defensible, and is why this is filed rather than built.

### §RK176 The tax RK128 agreed to pay unmeasured

`Bash` was kept out of the `PreToolUse` matcher on one sentence: matching every shell
command to catch one `sed -i` "is not a barrier, it is a tax on every command". RK128
overruled it for a good reason — the refusal claimed a boundary it did not hold — and
paid the tax without weighing it.

What is now paid per `Bash` call, in a fresh interpreter the harness spawns and waits
for: importing `roadkeep` (which pulls `serving`, and so `cli`, through `guarding`), one
`Config.discover` walking up from `cwd`, a TOML parse, and a few substring tests. The
tests are free; everything before them is not. RK174 measured the analogous cost on the
other surface and found 165ms where nobody suspected it, so the number here is worth
having rather than assuming.

If it is material, the answer's shape is a cheap exit *before* the expensive import — a
command with no path separator in it cannot name a governed file, and that is a string
test the hook can make alone. Whether the launcher can reach that decision before
importing the package is the part to check first: `scripts/roadkeep.py` puts the
plugin's copy on `sys.path` and calls the CLI.

Measure before changing anything. A guardrail removed for being slow is worse than one
that is slow, and a guess about which half costs is how the first version got its
sentence.

### §RK177 The schema that varies and the client that cached it

RK111 opened `add`'s id where a project declares a shape the counter cannot spell, and
named the cost: a tool schema that varies by config. RK24 already had a milder version —
`maxLength` and `enum` are read from `roadkeep.toml` — but a *bound* changing is a value
a client refuses wrongly, while a *field* appearing is a call it cannot make at all.

The server does its half right: the config is re-read per message, so the next
`tools/list` describes the file as it is now. What is missing is the message that makes
a client ask again. The protocol has one — `notifications/tools/list_changed` — and this
server sends no notifications, so a session that edits `roadkeep.toml` keeps validating
against what the handshake handed it. The refusal a caller then gets is `no such
argument task_id`, which RK111 made say *why* the field is absent — and on a config that
now declares a suffix, that sentence is wrong.

The cheap correction is to send the notification when a config read yields a different
descriptor set than the last one answered. That means holding one thing between
messages, which this server deliberately does not — a hash is small, but "holds no
state" is a claim to break on purpose rather than by accident.

The alternative is to accept it and say so in the refusal: a field this project declares
may want the session restarted. Cheaper, and it makes the wrong sentence a right one.
