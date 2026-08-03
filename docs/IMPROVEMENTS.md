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

### §RK193 The half RK179 did not reach

RK179 closed `record amend`: a correction on a wrapped entry is refused until `--lines`
says how many it replaces, and the whole span is then rewritten. The completion path was
left out of that commit deliberately, as work for an id of its own, and this is it.

`ship <id>` completing a partial replaces the entry in place — dropping the qualifier
and writing the outcome — through `replace_task`, which reproduces the first line and
nothing below it. So the same failure: the entry states the whole delivery followed by
the tail of the half's sentence, and the command reports a completion.

Measured rather than assumed, on the corpus that motivated RK179: **10 of Shio's 12
partial entries wrap**, so this is the majority case there and not an edge of it. Turing
has 3 partials and none wraps.

What makes it a separate decision from RK179 and not a copy of it: a completion is not a
correction. The caller asked to finish work, not to rewrite a sentence, so demanding a
count is a flag on the wrong verb — and refusing outright would block a legitimate ship
until the entry is repaired. Which of "refuse and name `record amend`", "take the count
here too", or "replace the span, the entry being this transaction's own" is right is the
task.

### §RK195 The same door, on the file the corpus says is clean

`amend` and `restate` rewrite a roadmap line's prose through `replace_task`, which is
the first line alone. On a wrapped entry that is RK179's defect exactly, one file over.

It is filed as an idea and not as a defect because the measurement says the opposite of
the ledger's. Both pinned roadmaps carry **0 wrapped entries** — Shio's 48 and Turing's
37 — against 146 and 3 in their ledgers, and `test_document.py` already asserts that
zero as a property. The format has no multi-line task line, `add` refuses one, and a
roadmap is the file this tool governs first, so the population that could hold the shape
is exactly the adopted backlogs nobody has read yet.

So the work is a count before it is a fix: is there an adoptable roadmap whose lines
wrap? cursarei and Dumont are on this machine and neither is in `corpora`. If the answer
is none, the honest outcome is a `retire` naming the measurement, not a guard on a door
nothing reaches — and RK133 is the precedent for closing a line that way. If the answer
is some, the fix is RK179's, already written, moved one module over.

### §RK196 The other half of the reader that did not learn

RK172 taught the gate that a pointer addresses every governed prose role and RK186
taught the reader. `shipping._dropped` is the third, and it is the one that *writes*: it
opens `config.document("improvements")`, finds no `§X.1` there, and reports "nothing
dropped" while `docs/STRATEGY.md` keeps the section the departing line pointed at.

Measured on a project declaring `strategy` under `ref_scheme = "outline"`: `lint` is
clean before, `show RK1` resolves the pointer into `STRATEGY.md` (RK186 working), `ship
RK1 --why …` prints `kept nothing dropped: no §X.1 section in IMPROVEMENTS.md`, and
`lint` exits 0 afterwards with the section still there.

Both halves are wrong and only one is visible. A section outliving its line is what RK6
exists to stop — the prose file becoming a second changelog — and the gate is why nobody
noticed: `section.unreachable` should report a design no line points at, and it is not
asked of every declared role either.

The fix is the shape RK186 used and not a second one: resolve the anchor across the
declared prose roles, drop from the file that declares it, and let the multi-owner
report (RK64) and the nesting refusal (RK78) work against that file rather than a
hardcoded role. The `no improvements file` early return becomes the "no prose role
declares it" the reader now states.

To decide while doing it: whether the gate half is this task or the separate finding it
looks like.

### §RK197 The follow-up that names work already done

The write path's own half of RK186, and the one that costs prose rather than a read.
`authoring._unresolved` asks `config.has("improvements")` and calls `find` on that
document, so on a project declaring strategy an `add --ref X.1` prints `needs section
add X.1 --title …  (the pointer above resolves to nothing until then)` — for an anchor
`docs/STRATEGY.md` declares and `lint` resolves.

Measured on the same project RK196 was: the roadmap gains a legal line, the follow-up
names a command that would create a *duplicate*, and an author who runs it gets
`ref.ambiguous` from the gate — one anchor in two roles, which resolves to neither. So
the cheapest outcome of obeying the tool is a design written twice and a line that now
points nowhere.

Worse than the read half it mirrors. `show` denying a design costs a file read; this
invites 250 words of prose the project already has, which is the exact spend L1 and the
word budget exist to prevent — and the sentence it invites is the one the tool cannot
write, so the cost lands on the author.

Narrow: `_unresolved` is four lines, and the question it asks is now
`PROSE_ROLES`-shaped. What needs a decision is the *absence* message beside it — a
project declaring several roles has more than one place a section could go, and `add
--section` writes to improvements, so the follow-up has to name the role it means rather
than the first one declared.

## Block C — Query

## Block D — The gate

### §RK188 A gate held against a file no verb maintains

RK104 was right that a README restating the backlog has to be held by the gate that
reads the files it came from: a projection nothing checks is a second source of truth
with a grace period. What it left is that **nothing writes it except a human remembering
to**.

Measured over one block. Every one of ten tasks went the same way: `claim` moved a
marker from 📋 to 🛠, the block carries markers, and `lint` reported `export.stale` on
`README.md`. Ten more after each `ship`. Every run of this repository's own conformance
test failed on it, on a file the task did not touch, and the fix was the same command
twenty times. A finding that appears after every write and is cleared by one command no
write runs is not a gate — it is a chore with an exit code.

The projection is derived, wholly, from files the verb already holds open. So the verb
is where it belongs: a write that changes what the block would render refreshes it in
the same transaction, which is what makes it derived in the sense the annotation and the
pointer are. The alternative — leaving it to `--fix`, which repairs only what is derived
— is defensible and weaker, because the gate still fails first and the author still runs
a second command.

Whichever, RK187 is the write this goes through, and its all-or-nothing rule is what
stops a refresh from half-writing a transaction.

### §RK189 A widening whose cost is an argument, not a number

RK173 was measured going in: six of Turing's eight `path.missing` findings named
artefacts the repository has, because a monorepo entry writes the path its reader is
standing in. The answer was to ask whether the repository holds a file whose path *ends*
in the token, which is the question RK51 already says this check is asking.

It was not measured coming out. The tail index admits a one-segment match, so
`./package.json` resolves — the case that motivated it — and so does any bare
`index.ts`, `README.md` or `main.py` a ledger names, against a file of that name
anywhere in the tree. The reasoning for allowing it is real: a repository holding a
`package.json` does satisfy "the repository has package.json", and a bare token with no
slash is already unreportable. The reasoning for suspecting it is equally real: a file
*moved between modules* now resolves, and that is a rename the ledger did not follow,
which is the one true finding this check has produced.

What is missing is a count. Run the check over both pinned corpora with and without the
tail rule, and read the difference line by line: how many findings it removes, and how
many of those a reader would call true. If a one-segment tail buys nothing over a
two-segment one, requiring a slash is a smaller widening for the same six. An idea
rather than a design, because which of the three it is depends entirely on that number.

### §RK192 A helper that is safe only by convention

`corpora.config` parses the corpus's own `roadkeep.toml` **at the pin** and then roots
the `Config` at the working tree. Every caller today is careful with it: each passes
`corpora.document(corpus, role)` explicitly and uses the config for the declaration
alone, which is the discipline RK105 established. Nothing enforces it.
`config.document(role)` and `lint(config)` are ordinary calls on an ordinary `Config`,
and both read the file as it is this afternoon.

The failure is silent and reads as a result. A count taken that way is a true statement
about somebody else's uncommitted afternoon and a false one about the revision the test
names — the exact shape RK105 was written to remove, arriving through the helper that
was written to remove it. It was hit while measuring a retirement:
`lint(corpora.config(SHIO))` returned five findings, which happened to agree with the
pin and would not have to.

Two directions, and the second is the one this repository's own laws point at. Give the
corpus a config whose paths resolve to the pinned bytes — materialised once per revision
under a cache — so a read through it cannot reach the tree. Or make the type say what it
is: a declaration, not a config, with the roles it can answer and nothing that opens a
file.

Either way the live read stays available and stays named, because the advisory in
`test_corpora.py` is the one that finds a parser defect in content nobody here authored.

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

### §RK185 Validate in characters, publish in words

An LLM does not have characters. The tokenizer exposes tokens, so "200 characters" is a
target reached by trial, and every retry in the observed loop was a re-guess. Words are
different: they survive tokenization well enough that "one sentence, at most 25 words"
lands inside 200 characters on the first attempt, with margin — 25 words at the corpus
average of 6 characters is 150.

That makes the unit a publishing decision rather than a validation one. Validation stays
in characters: `line_max` is a real bound on a real string, and a word count cannot
express it. What changes is what the author is given before composing — the `maxLength`
in the MCP field schema and the two rules in the skill — where a character count is a
number nobody can act on directly.

The two are not in conflict, because the word figure is an aim and the character figure
is the gate. Publishing both is what makes a first attempt land: the aim is hit reliably
and sits inside the bound with slack, so the gate stops being reached. Deriving the word
figure from the effective prose budget is why this waits on RK183 — a target computed
from the published 200 would inherit the overrun and aim at prose the line has no room
for.

Nothing here writes prose or grades it (L4): a word budget is a number, stated in the
schema the client already reads, and what fills it is still the author's.

### §RK198 The half of the parser cost RK174 left

RK174 took `tools/list` from 58 builds and 195 ms to one build and 3.4 ms, by building
the parser once per `descriptors()` call and indexing every subcommand path off it. It
fixed the first message and only that.

Measured after it: one `argv(tool, arguments, config)` calls `build_parser` **twice** —
once in `_subparser(tool.command)` for the actions it renders arguments through, and
once more inside `_companioned`, which reaches `prose_of`, which resolves the same
subcommand again. 6.7 ms per call, on the path every `tools/call` takes.

Smaller than what RK174 removed and the same defect: reaching one subcommand builds the
entire CLI, so a caller with two lookups pays for two. A session making twenty writes
spends about 130 ms rebuilding a parser that is a pure function of the code.

The shape is already there — `_parsers()` exists and `_subparser` takes an index — so
this is threading it through the call path: `argv` builds one and hands it to
`_companioned`, which hands it to `prose_of`. `prose_of(command)` is public and
`tests/test_serving.py` asks it about every tool one at a time, so the index has to stay
optional there for the same reason `descriptor` keeps its default.

What to check rather than assume: whether `call` resolves anything else per message, and
whether the remaining cost is one build — the number to report is what a call pays
after, not what it saved.
