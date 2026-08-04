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

### §RK229 The guess the ship stopped making

RK196 taught `ship` to resolve an anchor across the declared prose roles and to report
the file it actually wrote. `defer` was not in that commit and is the same sentence one
verb over: it deletes nothing, so no prose is lost, but it prints `carried §X.1 kept in
IMPROVEMENTS.md` for a section `docs/STRATEGY.md` holds.

Narrower than RK196 by exactly one thing — there is no write to send to the wrong file,
so this is a report that misdirects a reader rather than a transaction that misses one.
It is still the one line in the answer whose job is to say where the design stayed, and
RK96's whole argument for carrying the section is that a reader can go and find it.

What it needs is not `ship`'s resolution: `pause.carried` is a string derived from the
pointer and never a document, so the role has to be resolved somewhere. Either
`deferring` answers it and carries the role beside the anchor, as `Departure.prose` now
does, or the CLI asks — and the second is the shape RK196 argued against, a caller
restating a rule the writer already applied.

`resume` is worth reading in the same pass. It is the return direction and reports the
section coming back; whether it names a file, and which, is the same question with the
arrow reversed.

### §RK230 One transaction, or the pointer RK93 closed

RK93's argument is that a line and the design it points at are one write: given
separately, the roadmap gains a pointer resolving to nothing and the author learns the
follow-up from the gate, which is the inversion L1 exists to prevent. `--section` is
that transaction.

It writes to `improvements` and to nothing else. On a project declaring only `strategy`
— legal under L6, and the shape RK172, RK186, RK196 and RK197 each taught one more
reader about — the call is refused with `NoProseFile` and the only route left is `add`
then `section add --role strategy`, which is the two-command shape RK93 was filed
against. So the door exists and the projects that most need it cannot reach it.

RK197 already resolved the *follow-up*: it names `--role strategy` where that is the
role a section would go into, which means the answer to "which role" is now computed and
this verb could ask the same question. That is the cheap version.

What needs deciding is whether `--section` should take a role at all. `add` deriving it
matches every other placement in this tool, and a project declaring both roles has a
real choice that only the author can make — while a flag on `add` is a second place the
role can be said, and `section add --role` is already the first.

### §RK231 RK123's deadlock, for work that was set aside

Found by a test written for RK215 that failed for the wrong reason, which is why it is
filed rather than described: the refusal is reproducible, and it arrives before the
check the test was about.

`section amend` validates through `_check`, which asks `_task_for` whether an id-shaped
anchor names an open task. That function reads `config.document("roadmap")` and nothing
else, so a task in the deferred store is not open by its reading — and the refusal says
*no open task RK1 points at this section: add the line first*, about a line that exists,
in the file `resume` restores from.

The state is one the tool creates on purpose. RK96's argument for the store is that a
pause keeps the id, the deps, the symptom **and the section** a departure deletes, so
the section is live work's design. Correcting it is the ordinary case RK123 opened this
verb for: a paused design is at least as likely to go stale as an open one, nothing
being written against it.

Which makes this RK123's deadlock displaced. `drop` refuses while a pointer claims the
anchor, that pointer is in the store, `amend` refuses because it reads a different file
than the pointer lives in, and the guard denies the `Edit`.

The fix looks like RK215's for the neighbouring question: ask both live roles, which is
what the gate reads and what `_pointed_at` now asks. Worth deciding with it whether
`anchor.unknown` should tell *paused* from *absent*.

### §RK232 The corner RK215 left, named by the commit that left it

RK215's claim is that the writer charges a section exactly what the gate charges it, and
the scope of that claim is one condition short. `lint` builds its `pointed` set from
refs whose anchor **one** prose role declares — an anchor two files declare is charged
as pointed at by nobody, because which of the two a line meant is what `ref.ambiguous`
asks the author, and billing one of them the other's subtree is the silent half of that
defect. `_pointed_at` does not ask, so on such an anchor the writer charges the subtree
and the gate charges the prose.

Filed as an idea because the first thing it needs is a reason to exist. The state is
narrow: an anchor declared in both the improvements and the strategy file, pointed at,
and over the limit only with its subtree. `lint` already reports `ref.ambiguous` there,
so the file is not clean and the author has a finding naming the real problem — which is
an argument that this disagreement is unreachable in any tree somebody is working in.

Against that: RK215's whole finding was a writer refusing a state the gate calls clean,
and "narrow" was the reason nobody had counted it. The honest version of this task is
the count — does any corpus carry an anchor two prose roles declare? — and then either
the condition, or a `retire` naming the measurement, as RK195 did.

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

## Block E — Adoption

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
