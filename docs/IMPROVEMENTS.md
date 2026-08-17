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

### §RK1231 The heading the tool wrote is the one it does not renumber

`add --section` composes the rationale heading itself, appending the task's id:
`sections.py` builds `f"{title.strip()} ({task.id})"`. The id in a heading is the tool's
own writing, not a convention an author chose.

`renumber` does not maintain it. It moves the line, its deps and the section — but the
section only `if entry.task.ref == task_id`. Under an outline ref scheme the ref is an
address like `XXVI.14`, never the id, so that branch is skipped and the heading keeps
the number the task no longer has. The comment beside it is right about the anchor: an
outline heading is not this line's to move. The title is a different question, and one
the tool already answered when it wrote the id there.

Seen for real. `renumber SH9001 SH789` in an adopting project returned `section: null`,
the line and its pointer moved, and `IMPROVEMENTS.md` kept `### XXVI.14 … (SH9001)` — a
heading naming a task that does not exist. The repair was a second command,
`section-amend --title`, and finding it meant reading `section: null` as a signal rather
than as "no section was involved".

Two candidate fixes, and the cheaper may be enough. Rewrite the trailing `(<id>)` on
renumber, leaving the anchor untouched. Or have `lint` report a heading whose id no line
and no entry carries, which also finds the ones already written.

## Block C — Query

## Block D — The gate

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

### §RK1232 The worker count that leaves the machine usable

`-n auto` resolved to `os.cpu_count()` — every logical core, with nothing left over.
Here that is 28 workers on 28 threads, and the run RK457 made the default became the run
that makes the machine unusable while it goes: an editor, a language server and a second
session all wait behind a pool that asked for the whole processor.

The count was never what made the suite fast. RK457 measured 5m07s serial against 41s
parallel and attributed it to a long tail of process spawns and filesystem work — which
is what parallelism answers, and what stops answering once every core is spoken for.
Each worker also imports this suite's `conftest`, which fingerprints the checkout and
copies the governed files (RK263, RK315), so the twenty-eighth worker pays that setup to
win contention against the twenty-seventh.

Measured on the full suite at 3,828 tests, both runs green:

    -n 28 (what auto answered)   174.3 s
    -n 14                        176.4 s

Half the pool costs two seconds — inside this suite's own run-to-run noise — and hands
back fourteen threads. So `auto` halves: floored at two, so a two-core CI runner keeps
both rather than dropping to the single worker RK462 measured as worse than none, and
capped at the cores there are, so a one-core box is not asked for two.

The narrow path is untouched. A caller naming one file still gets no workers at all,
which is RK460's answer to a different question: there the cost is the spawn, and here
it is the contention.

## Block E — Adoption

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
