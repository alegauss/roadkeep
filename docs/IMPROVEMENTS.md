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

### §RK1223 block add refuses where the heading is missing

Reopening a block that shipped is ordinary: a follow-up is filed under the block it
belongs to, and that block's heading survives only in the ledger, because `block drop`
leaves history the heading it was filed under.

So `block add J --title "…"` is the obvious move, and it answers `J is already declared
in docs/CHANGELOG.md: nothing to open` — and writes nothing. Which is true of the
changelog and false of the request: the roadmap, the one file the new line is about to
go into, has no heading for J at all.

The next call finds out. `add --block J` refuses with the exact command that works,
`--organise roadmap`, so the door exists and is well named. It is just behind a second
failure, and the verb that owns opening blocks is the one that sent you away.

`block add` already reads every file to decide what to skip. When the label is declared
somewhere but missing from a file that would take it, that is not nothing to open — it
is a heading to open, in the files that lack it. Either open it there, or refuse with
the same sentence `add` uses instead of a phrase that reads as "you are done here".

Worth checking whether the same shape hides in `--after`: it is documented as refused
per file, which is the same per-file truth answering a request that was about the block.

### §RK1229 A line the tool wrote and cannot repair

`amend --deps` accepted `FreeWilly DD133 (Docker drops its pipe mid-build)` and wrote
it. The rendered line put that value inside the derived `(deps: …)` group, so the inner
parenthesis closed the group early and the grammar stopped reading the line. `lint` then
reported `line.unparsed` at that line and `section.orphan` for the section it had
pointed at.

What makes it more than bad input is what came next. `amend`, `restate`, `retire` and
`defer` all answered *nothing there carries that id* — correct, since the grammar cannot
read the line. `repair` listed both findings as decisions with no complete command,
`lint --fix` names control characters as its one cause, and the hook refuses the
hand-edit.

So the tool wrote a state that none of its verbs reaches and its gate forbids repairing
by hand. The task had to be re-filed under a new id, spending one, and the invalid line
is still there.

The input check is where this closes. `add` and `amend` both promise validation *at
input* — "or nothing is written" — and a dep that cannot survive rendering is exactly
what that promise is for. Rejecting `(`, `)` and `→` in a dep would have cost a refusal
instead of a lost id.

Worth deciding whether `lint --fix` should also delete a line no verb can reach, since a
line outside the grammar is not a line any reader is served by.

## Block C — Query

### §RK1221 The flags one arm of a two-arm read never looks at

`_subject` has two arms. With an id the roadmap holds it returns that entry's task; with
anything else it composes one out of `--block`, `--dep`, `--marker` and `--symptom`. So
on the first arm all four are read and discarded: `budget RK12 --symptom "<a rewrite I
am weighing>"` answers about the symptom already on the line and says so nowhere.

That arm is right about the *file*: an id the roadmap holds has a symptom, and reporting
the caller's instead would answer about a line nobody has. What is wrong is the silence,
and RK465 named the shape — a narrowing flag nobody reads is worse than a refused one,
because the caller reads a number believing it narrowed it. RK1190 sharpened it:
`--symptom` is now a draft to measure, so passing one beside an id is what an author
weighing an `amend` does.

Three readings, and they are not equally good. **Refuse** it, as `answers` and `narrows`
refuse two subjects, which is consistent and costs the caller a second command to get
the number they wanted. **Honour** it — measure the draft against the line's other
fields — which is what the flag now means everywhere else and is what an `amend` is
about to do. **Say** it, leaving the answer alone and naming what was ignored.

The second looks right and wants checking against the arm's own claim: `--dep` and
`--marker` move the allowance too, so honouring one and not the others makes three flags
mean two things.

### §RK1225 A budget that omits a rule the gate enforces

`budget` answers width: characters left in a field, room on the rendered line, words
left under an anchor. It says nothing about how many sentences the field accepts, and
`why` accepts one. So a caller can compose a `why` that fits every number the budget
published and still be refused by `why.sentences` — which is the shape RK265 named,
arriving through a different door.

Observed while shipping a partial. The outcome needed two clauses; written as two
sentences it was refused after the prose existed, and the retry cost a second
composition of the same thought. The refusal itself is good: the second sentence does
belong in the section the line points at. What is missing is that the constraint was
knowable before a word was written, and the verb whose entire purpose is to say so did
not say it.

The fix is to publish the rule alongside the widths, per field: `sentences: 1` for
`why`, whatever the schema holds for the others. It is a constant, not a measurement, so
it costs nothing to derive and it makes the budget's answer complete rather than
partial.

Worth stating the same thing in the field's own help, where a caller reading `--why`
sees "one sentence, ending in a stop" but reading `budget` sees only 200 and the line
maximum. Two places that describe one field should not disagree about what binds it.

### §RK1226 A partial has two halves and one of them is an inference

`ship --part` records the half that landed and leaves the line open, which is the right
shape: the ledger gains an entry qualified by what shipped, and the roadmap keeps a task
whose sentence is still partly true. What nothing holds is the other half.

The qualifier names the landed side. Reading the ⏳ line later tells you the problem is
not solved; reading the ledger tells you what was done. Neither tells you what remains,
so the remainder is reconstructed by subtracting one from the other — across two files,
from prose written for different purposes, by whoever picks the line up. That
reconstruction happened here several sessions after the partial, and it needed the
improvements section read in full to recover a remainder that the person shipping had
known precisely.

`brief` is where this belongs, because it already joins the line, the section and the
ledger. Surfacing the recorded qualifier on a partial would make the subtraction
explicit instead of implicit, and it costs a lookup the verb already performs.

The stronger version is to let `--part` name the remainder as well, so the open half is
data rather than an inference. That is a field on the entry, which is a change to the
model and not only to a report, so it is worth deciding whether the qualifier is one
string or two.

Either way the property to keep is that resuming a partial should not require reading
the rationale to learn what is left.

## Block D — The gate

### §RK1217 The ledger's paths are checked against the wrong tree

Turing's `T759` entry names `frontend/apps/site/scripts/emit-model-catalog.mjs`, a
script that existed when the work shipped and was later extracted into its own
repository along with the model catalog. The entry is accurate. The file is gone. `lint`
reports it every run, and will keep reporting it.

`_candidates` already forgives a path that moved **within** the repository —
`tree.anywhere` catches a rename — but one that left it entirely has nowhere to be
found, so the rule reads a correct statement about the past as drift.

What makes it worse than noise is the door. The remedy composes `amend --why`, which
replaces the entry's whole sentence under `[limits] why` at 200 characters — while
`[limits.changelog]` lets that same entry run to thousands, and `T759` spends about
1,500 of them on what was built. The offered fix for a stale path is to delete the
as-built record that made the entry worth keeping. Nobody takes that door, so the
finding stays forgiven by baseline forever.

The tree the question is about is the one the entry was written against, and git knows
it: the revision that added the line, or failing that, whether the repository ever held
the path at any revision. Either reading answers `T759` and still catches what the rule
is for — a path this repository never had.

If walking history per entry is too slow for a hook, ask the working tree first as now,
and only for a token that fails ask whether history held it.

### §RK1222 The half RK1216 named and left to the gate

RK1216 gave `remaining` the words: a pathspec that reached no file is named on the
headline and published as `unmatched`, so a query that never ran no longer reads as a
migration that finished. That fixes the *read* — and the read is asked by whoever is
continuing the migration, who does not have the typo in front of them.

The gate is the other half, and RK1216's design named it without taking it: a declared
query is a claim in a governed file, and a claim nothing answers is what `lint` refuses
everywhere else. A dangling pointer is `ref.dangling`, a dead queue entry
`priority.dead`, an unreadable fence `remaining.format` — which this sits beside. A
pathspec matching no file is that same statement. It is not *work outstanding*, which
the gate is right to stay out of; it is a query that cannot answer.

What has to be settled first is the false positive, and it is real. A migration whose
sites are *deleted* rather than rewritten ends with its pathspec matching nothing, and
that is the query working — the same zero, honestly. A finding would fire on the
finished migration it was meant to tell apart from the typo: RK1216's confusion with the
sign flipped.

Two ways through. Fire only where the pathspec has **no glob metacharacter and names an
extant directory**, which is the shape both measured cases had. Or make it a note rather
than a finding, so nothing fails and the report still says it.

### §RK1228 The check that a section moved has no mirror

`lint --since` already checks the shape where prose moved and the line did not: a
rationale section edited without its task line is RK36's Note. The mirror is unchecked.
Source can change under everything a task's section names, the tests for it can pass,
and the line stays open with nobody told.

Observed here across a working session. A task's section named the component and the
library module it needed; both were rewritten, a dozen assertions were added and passed,
the outcome was reported as delivered — and `ship` was never called. `lint` said clean,
because the files it governs were internally consistent, and they were: the entry simply
did not exist. It surfaced two blocks later, when a block that should have been finished
still counted one open line.

The signal is already computed. `show` resolves the paths a section names, and `--since`
already has the diff. A Note is the right tier — a path named in a section changes for
plenty of reasons that are not the task, so refusing would produce a gate that gets
bypassed. Saying it once at the moment of the commit is the whole value.

The narrower version is cheaper and catches the same case: a block whose every task's
paths were touched by this change while at least one line is still open. That is the
transition `block.emptied` almost describes, from the other side.

## Block E — Adoption

### §RK1224 The retry that pays for the body twice (RK1224)

Filing one Shio task took four calls. The first was refused for a missing `ref`, the
next three for `why` — 176, 171 and 170 characters against a limit of 167. Each refusal
was correct, each named the exact overflow, and each threw away the 250-word
`--section-body` that had travelled beside it.

The cost worth measuring: the field that failed was **three characters** too long, and
the payload re-sent to fix it was two orders of magnitude larger. `budget` answers
before a word is written and is the documented remedy, but it answers about *limits*,
not about a sentence somebody has composed — so the shape of the work is compose, call,
shave, call again, with the body riding along every time.

The all-or-nothing transaction is right and is not what should change: a task whose line
validated and whose section did not is the half-written state `add` exists to prevent.
What is missing is a way to say *the body is unchanged*.

Two shapes. A **draft handle** — a refusal returns a token naming the payload it already
holds, and the retry passes the token plus the corrected field. Or `add --dry-run`
taking the real fields and answering about all of them at once, which is `budget`
pointed at a draft rather than at a schema, and would have collapsed those four calls
into two.

The measurement this needs first: how often a refusal is the second or third for one
filing, which the tool sees and nobody counts.

### §RK1227 The anchor a rationale cites and nothing resolves

Found in Shio, filing SH763. Its rationale cited `§XVII.100` — an anchor a task had
removed when it shipped — and `roadkeep section amend` wrote it without complaint. The
failure surfaced two commits later as a **red JS gate** in that project, from
`improvements-debt.test.mjs`, on a docs-only commit that had touched nothing else.

The write validated everything about the prose except the one thing prose can be wrong
about mechanically. Length: checked. Paragraph shape: checked. Whether `§XVII.100`
resolves to a heading in the file being written: not asked, though the file is open and
the answer is a lookup.

Three properties make this worth fixing here rather than in the adopting project. It is
**decidable** — an anchor either exists in the governed file or it does not, which is
the same question `lint` already answers for a task line's `ref`. It is **cheap** — the
section index is built to insert the section at all. And the alternative discovery path
is the worst kind: a gate in somebody else's repository, red for a reason whose cause is
three commits back in a different file, reached only by running the suite.

The shape to copy is `add --ref`, which resolves before it writes and refuses naming the
free anchors. `amend` should ask the same question of every anchor reference in the body
it is handed, and refuse with the same list.

Worth checking on the way: whether `add --section-body` has the same hole.

## Block F — The plugin

### §RK1218 Two commands to file one task

Filed from fourteen sessions driving another project's backlog, where every task cost
the same two commands: `add` writes the line and prints that the pointer it just wrote
resolves to nothing, then `section add` writes the prose it points at. Between them the
roadmap is in a state this project's own lint calls ref.unresolved.

The window is short and nothing was lost in it, so the cost is not corruption. It is
that the tool says it has left the docs wrong and then asks you to fix that yourself,
once per task, forever. A caller interrupted between the two commands - or who forgets,
which is why the warning exists - leaves a dangling pointer for lint to find later.

The separation is defensible: a line is a claim and a section is an argument, and being
made to write them apart is what stops a one-line symptom standing in for a rationale.
That is worth keeping. What is not worth keeping is that the defensible order is the
only order, when the caller already holds both halves at the moment they run `add`.

So let `add` take the section with it, by the same `--title` and `--body-file` it would
be given next, and write both or neither. The two-command path stays for the caller who
wants to think between them. The budget refusal has to apply to the combined form too,
or this becomes a way to smuggle prose past the limit `section add` enforces.

### §RK1230 The copy a shell command should invoke

The MCP tools always reach the right copy. The shell does not, and a session that needs
the shell — `lint --fix` is withheld from the tool surface, so any repair goes there —
has to know which copy to invoke. Nothing says which.

Observed across one long session. Commands were run against
`~/.claude/plugins/cache/alegauss/roadkeep/0.1.886/src`, found by listing that
directory, while the engine this project actually writes with is
`~/.claude-pessoal/plugins/cache/alegauss/roadkeep/0.1.922/src` — a different plugins
root entirely. `installed_plugins.json` under `.claude` lists 0.1.886 for this project,
which is what made the wrong copy look confirmed rather than guessed.

The only signal was one line inside an unrelated `lint --fix` report: *this gate is
0.1.886 and the plugin wired to this project is 0.1.922*. Everything before that ran on
the wrong engine and answered plausibly, which is the part that matters — a stale copy
does not fail, it agrees with a rule that has moved.

`engines` answers the question exactly, and it was found only after the disagreement was
noticed. Two things would have closed the gap earlier: a refusal rather than a note when
a shell invocation is not the wired copy, and a one-line way to print the path to invoke
— so a caller composing a shell command has somewhere to read it that is not a directory
listing.

Worth deciding whether a stale copy should refuse to write at all, since a write from
the wrong rules is the failure the note describes and does not prevent.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
