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

### §RK121 Partial completion is a state the model does not have

Every id is in exactly one of two states: open in the roadmap, or recorded in the
ledger. Work that lands in halves is neither, and the projects using this have all
invented the same escape — a parenthetical on the ledger id.

Shio has seven: `- **SH96 (local half)** —`, `- **SH275 (partial)** —`, `- **SH84 (the
SH22 half)** —`. It reads perfectly to a person and is invisible to the parser, which is
worse than either half alone. An id it cannot parse is an id that is **not in the
changelog**, and that is a different statement from "not done": two Shio lines declare
`deps: SH96 ✅` and `lint` answers that SH96 is in neither file.

**And the qualifier is write-only.** Five of the seven name a task that has since
completed — nothing removes it when the second half lands, because `ship` deletes a
roadmap line and never touches an entry already in the ledger. So the corpus carries five
statements that were true when written and are now false, in the file whose whole job is
to answer "is this done".

Two directions. Teach the ledger grammar an optional qualifier after the id, or give
partial completion a first-class form — an entry declaring which part shipped, with the
line left open for `ship` to complete later. The second is more work and is the one that
can be *maintained*, because only a verb can know when the qualifier stops being true.

## Block B — Authoring

### §RK113 Half a subtree renamed, and written

Reproduced in a scratch project: a roadmap carrying `RK1`, a prose file with `§RK1` and
a `#### §RK1.1` under it, and one `renumber RK1 --to RK9`. The line moved, the pointer
moved, `§RK1` became `§RK9` — and `§RK1.1` stayed exactly as written, nested under a
heading naming a different task and claiming one that no longer exists.

`_section_document` calls `find`, which deliberately returns the **subtree**, and then
rewrites a single line: `section.first - 1`. One heading of the several the section
owns. That asymmetry is the whole defect — the function that knows the subtree is the
one renaming only its root.

Two things earn it a line rather than a fix in passing. The write is not a round-trip
failure, so L3 does not catch it; and `lint` reported the result **clean**, which is the
second finding filed beside this one. The tool renamed half a subtree, wrote it, and the
gate agreed.

`ship` and `defer` do not have it: one deletes the subtree whole and the other carries
it whole. `renumber` is the only door that rewrites an anchor in place, which is why it
is the only one that can leave two spellings of one task under a single heading — the
silence RK112 closed, one verb over.

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
