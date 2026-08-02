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

### §RK109 Two readers of one id shape

RK106 put the shape on the `Schema` — `id_pad`, `id_suffix`, and the one `id_fragment`
every regex is built from. The *parsing* half did not move with it. `backlog.number_of`
and `family_of` are free functions over `prefixes` plus a `suffix` boolean, and they
answer a different question from the pattern they are supposed to agree with: under `pad
= 2`, `id_pattern` refuses `D1` and `number_of("D1", ("D",))` returns 1.

Nothing is wrong today, because the four call sites were all updated in the commit that
added the flag. That is exactly what makes it worth a line: correctness rests on four
callers remembering an argument, and the near-miss was real — `picking` sorts on
`number_of(...) or 0`, so a `T24b` it cannot read counts as zero, and zero is *first*.
The split task a project deliberately numbered after `T24` would have been offered ahead
of every line below it.

The module docstring of `schema.py` already states the rule this breaks: a rule that
lives in two places is a rule two places can disagree about, so the schema lives in
exactly one. The shape is now in one place and its reader is in two.

What is wanted is a single parse on the schema — family, number, sub-letter, or nothing
— that both the pattern and the ordering are derived from, so a caller cannot hold half
of the declaration. The ordering helpers stay public; `pick` still orders numerically,
and a second implementation of *that* is the defect this is not.

## Block B — Authoring

### §RK112 section drop deletes a section an open line points at (RK112)

Found by using the tool, in Shio: `section drop VIII.11` succeeded, and the next `lint`
reported `ref.unresolved` for **SH197**, an open task whose pointer named exactly that
anchor. The section was stale by every other measure — both tasks in its title had
shipped — and an open line still owned it.

**RK78 already decided this must refuse.** Its guard asks who points at a section *nested* under the
anchor, and its own docstring names the counterpart: "the multi-owner check `ship` already makes
about the anchor it was given — that one asks who else points here". That check lives on the ship
path. The standalone `section drop` never makes it, so the verb whose whole job is removing one
section is the one that can strand a pointer.

The consequence is RK78's own words about what it closed: *"`lint` named the damage
immediately afterwards, by which point the only remedy was `git checkout` on the file"*.
Here it was worse: the drop was one of seven in a triage pass, so reverting would have
discarded six correct ones, and the fix was to hand-write SH197 a new section — the
state this tool exists to keep an author out of.

Refuse before the write, in the same message shape: name the anchor, name the owners,
say the remedy is to repoint or to ship the line that claims it. `ship` keeps dropping
its own task's section, which is the case that is always right.

## Block C — Query

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
