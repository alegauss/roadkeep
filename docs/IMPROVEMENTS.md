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

### §RK201 The one surface RK185 did not reach

RK185 made the case in one sentence: a model has no characters, so a limit published
only in them is a target reached by trial. It then published the word aim on every
surface an author reads *before* composing — the MCP field schema, `budget`, `brief`,
the skill.

The refusal is the surface they reach after, and it still says "delete 9 characters".
That is exact and it is unactionable in the same way the ceiling was: the author
subtracts a number they cannot measure, and the observed loop is five retries against
one gate in a single session of this repository's own work.

The correction is small and it is not a second opinion: RK184 already computes the
surplus, and stating it as words alongside is the same conversion `budget` makes, from
the same constant. "Delete 9 characters — about two words" is a sentence an author can
act on without re-composing.

Two things to be careful of. The word figure here is a *surplus* and not an aim, so it
rounds the other way: rounding down would name a cut that does not clear the gate. And
the refusal must keep the character number first, because that one is exact and the word
one is an approximation of it — an author told only "two words" and given a 9-character
overrun would be back to guessing, with a smaller number to guess against.

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

### §RK214 The door a ledger's own shape closes, discovered by being refused

`retire` is the door for a task decided against, and it refuses in any project declaring
`[ledger] marker = false`: a retired entry cannot be told from a shipped one when
neither writes a glyph. The refusal is right and it writes nothing, which is also right.

What it leaves behind is a project with no recorded exit for abandoned work. Measured in
Claude Code Tray, whose ledger declares no marker because 163 of its entries were
reconstructed from git history before this grammar existed. A task there was measured,
the premise did not survive the measurement, and there was nowhere to record that — so
the reachable alternative was `ship` with an outcome saying it was decided against. A ✅
against work nobody did is the ledger lying that `marker = false` was declared to
prevent.

Nothing warns in advance. The skill names `retire` among the verbs, and the refusal
arrives at the moment somebody has already done the work of deciding.

Two shapes. Let `retire` write without a marker, distinguished by the sentence it
carries — the ledger already tells its entries apart by what they say, and *decided
against* is a sentence. Or refuse earlier: a project declaring no marker is told once,
at `init` or by `lint`, which door it has closed, rather than at the moment it needs to
walk through it.

### §RK215 Refused by the writer for a state the gate calls clean

`section amend XXII --body '<nine words>'` was refused in Claude Code Tray with *934
words, limit is 300 with its subsections*. That anchor's own prose is two sentences; its
three subsections are the other 900.

The intro had gone stale in the ordinary way — it described a budget as full that a
shipped task had since emptied — and its subsections were live, so `drop` refuses as
well, and the guard denies the `Edit`. Every door closed, and the file left saying
something untrue. That is RK141's deadlock one level over.

The sharper half is that `lint` does not agree with `amend`: the same file passes the
gate. So the limit enforced at the writer is not the limit the project is held to, and a
writer is refused for a state nothing else calls a problem.

The measurement `amend` wants looks like the one `add` already makes — a section's *own*
prose against `section`, with each subsection measured as itself. RK166 unblocked the
top level for `add` on the argument that a heading merely missing is one the author can
add; the same argument covers a heading whose prose is merely wrong.

Worth deciding with it whether an anchor carrying subsections should be amendable at
all, or whether its intro is a section like any other.

### §RK216 A diagnosis that sends the caller to the wrong file

`ship T226 --why '<four sentences>'` refused twice with *no heading declares Block A in
ROADMAP.md (declares: AG, AE, AB, AC, AI, AJ, G, D, N, E, S, Q)*. T226 is in **AJ**,
which that very list contains. The same command with a short `--why`, and later with the
full text passed through an environment variable instead of typed inline, succeeded.

So the cause is most likely argv reaching the parser differently — this was PowerShell
5.1, whose native-argument handling is its own subject — and the tool wrote nothing
either time, which is the half that worked.

The finding is the message. `A` is a prefix of `AJ`, and a refusal naming a prefix of
the caller's block, drawn from a list containing the caller's block, cannot be acted on:
it tells somebody to declare a heading that already exists under a letter they never
typed. Whatever mangled the input, the label the resolution used was never checked
against the label the id itself carries.

Two things worth having. The refusal could quote the id's own block beside the one it
resolved, which turns an impossible sentence into an obvious one. And where a `--why`
arrives empty or partial, say so rather than proceeding to a lookup with whatever is
left — the second attempt ran with a short `--why` and shipped it, which is how a
placeholder reaches a ledger that `amend` then refuses to correct.

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

## Block D — The gate

### §RK210 The cost of the root that cannot reach the tree

RK192 was right that a config handed out for a pinned corpus must not reach the
checkout: `document` and `lint` were ordinary calls that read this afternoon's bytes,
and the answer looked like a result. What it did not price is the one check whose
subject is **outside** the governed files.

`path.missing` asks whether the repository holds an artefact a shipped entry names, and
it asks the tree. Through the pinned config the tree is a temporary directory holding
the governed files and nothing else, so `lint` reports six artefacts absent that both
corpora carry: `../package.json` and two `../agents.md` in Shio, `./package.json` and
two `docs/` files in Turing. Every one is false, and each was silent before because the
root was live — which is to say the leak was also what made this check answer.

Three shapes, and the measurement is which. The materialised root could be a git
repository with the pinned tree's file *names* committed, which makes `Tree` answer
without carrying anyone's content. The projection could take the checkout for path
resolution alone, which is two roots in one config and needs saying out loud. Or the
corpus config could declare the check off, which is honest and loses the only assertion
this repository makes about that check on a real ledger.

### §RK211 A refresh whose price is assumed

RK188 is right that the write which stales the block is the write that owes it, and the
transaction is the right place. What it did not do is measure the addition. Every `add`,
`status`, `amend`, `ship`, `defer` and `renumber` now reads the counted roles it is not
already holding, builds a `Census` for each, runs `pick` over the whole backlog and
splices two target files — on a repository where building the CLI parser once per
message rather than once per process was worth RK202.

The costs are not obviously alike. Reading a governed file the transaction does not hold
is a parse this project already pays elsewhere; `pick` is a graph walk over every open
line; the splice is two file reads that produce no write on the common path, because
most writes move no count.

So the number is what decides whether anything is owed here at all. Measure a write on
this repository's own `docs/` and on the larger of the two pinned corpora, with and
without the refresh, and read the difference against what a command already costs. If it
is inside the noise, this line retires with the number in the ledger, which is a better
outcome than a cache nobody needed.

### §RK212 The anchor a shipped line stops carrying

RK206 named what `ship` breaks at the moment it breaks it, and that is the half a verb
can do. The other half is what a reader meets afterwards, and the measurement says it is
not decidable: `as_ledger` drops the pointer, deliberately and for a good reason — the
section is deleted when the task leaves, so a pointer to it could not resolve. The
consequence is that `§XVIII.12` in somebody's prose is either a design that shipped or a
typo, and no file holds the difference.

Counted: 37 such references across this repository, claude-tray, Shio and Turing, in
files whose prose is correct. That is why RK206 added no finding.

The obvious move — let the ledger keep the anchor — is a slot on a line the ledger's own
grammar removed, and it re-opens a question RK6 closed. The narrower one is a
**cross-reference the tool understands**: a citation that names the task rather than the
anchor resolves in the changelog for as long as history exists, which is where a shipped
design's record already lives. That would be a format decision, so it is an idea and not
a design: it changes what prose may say, and this tool has never told an author how to
write a sentence (L4).

### §RK213 The artefact the repository produces and deliberately does not track

Measured in Claude Code Tray. Its ledger's T151 entry names
`bin/Release/net10.0-windows/win-x64/ClaudeTray.exe` while explaining why that project's
CI job builds rather than publishes — a correct sentence about where the build output
lands. `bin/` is the first line of its `.gitignore`, and its roadkeep workflow is
`actions/checkout` followed by the action, with no build step at all.

So `lint` exits 1 on every push and 0 on the machine of anyone who has just compiled. It
went unnoticed for both reasons at once: invisible locally, and in CI it is the only
finding, so the job has simply been red.

`anywhere()` widened this rule once already, because six of Turing's eight findings
named artefacts the repository has. This is the next shape along — an artefact the
repository *produces* and deliberately does not track — and the docstring names the
discomfort itself: the finding points at history, and the remedy its wording implies is
editing what already happened, which `amend` refuses for a shipped id by design.

Three candidates, and the choice is the tool's rather than the adopter's: consult
`.gitignore` and withhold a finding for a path it covers; treat a token under a
conventionally ignored directory as not a claim about a tracked file; or make it
advisory when the token resolves nowhere and names a directory no tree has ever tracked.

`baseline` does not answer it here. That project commits to `main`, so `origin/main`
makes the rule vacuous exactly where it runs.

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

### §RK205 A typed package nobody may type-check

Every module in `src/roadkeep/` is annotated, and several carry `from __future__ import
annotations` for the sake of it. None of that reaches anybody who installs the package:
PEP 561 says a checker must ignore inline annotations in a distribution that does not
ship a `py.typed` marker, and `pyproject.toml` declares none.

It surfaced from the other side. RK199 wanted the 5.6ms `typing` costs at every startup
and dropped a `TYPE_CHECKING` re-export block, on the argument that no external checker
reads this package anyway. That argument is true, and it is true of the other
thirty-five modules too — which makes it a fact about the distribution rather than a
licence.

Two coherent answers, and the wrong one is doing neither. Ship the marker: one empty
file, one line of package data, and every annotation already written starts paying off
for a consumer. Or decide the package is a CLI whose Python surface is not a promise,
and say so where somebody looks — which is a smaller claim than the annotations
currently imply.

What tips it is whether `from roadkeep import Schema` is a surface this project intends
to support. `__all__` says yes and nothing else does: no documentation names it, no test
outside `tests/test_packaging.py` depends on it, and the whole tool is shipped as a
plugin and a console script. Answer that first; the marker is a consequence and not the
question.

## Block F — The plugin
