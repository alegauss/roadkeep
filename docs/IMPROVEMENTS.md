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

### §RK1233 The remainder as data, not as a subtraction

`ship --part` records the half that landed, and RK1226 put that qualifier on the brief
so resuming a partial no longer means reading the design to recover what is left. It
made the subtraction *explicit*. It did not make the remainder *data*.

The open half is still an inference: a reader is handed `landed the parser half` beside
a symptom describing the whole, and works out the rest — better than reading two files,
and still a reconstruction, done by whoever picks the line up from prose written for
another purpose.

What would make it data is `ship --part` naming both sides. That is the decision RK1226
declined to take, and it is the one to settle first: whether the qualifier is **one
string or two**.

Two shapes, differing in which file carries the remainder. A second field on the ledger
entry keeps both halves in one record and makes the ledger state something about work
that has not happened — the one thing a ledger has never done. Or the *roadmap* line
carries it, amended in the same transaction: an open line already claims what is left,
so narrowing its own sentence is a shape the format has, and `record amend --part` stays
the door for the landed side alone.

The second looks right and wants checking against L4: `ship --part` may not compose a
`why` it was not given, so the remainder is an argument the caller passes — a flag on
`ship`, never a derivation.

## Block D — The gate

## Block E — Adoption

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
