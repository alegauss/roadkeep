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

### §RK1234 The block that finished and nobody closed

RK1228 reports a coincidence: this change touched a path an open task's section names,
and the line is still open. It is a note, deliberately, because a path named in a
section changes for a rename or a neighbouring fix as readily as for the task.

What it cannot see is the block. The incident it was filed from surfaced *two blocks
later*, when a block that should have been finished still counted one open line. The
design named the stronger reading and left it: **a block whose every open line has had
its paths touched by this change.** One line moving is ordinary; every line in a block
moving while none shipped is a block somebody finished and did not close.

Two things to settle first. Whether it is a second note or the same one aggregated —
saying the per-line thing five times and then again about the block is noise, so the
block reading probably *replaces* its members, which is the shape `_collective` already
has.

And what "every" means where a block holds a line whose section names no path. Counting
it unsatisfied makes the signal unreachable on any block with one prose-only task;
ignoring it makes a block of one such line report on an unrelated edit. The honest
reading is probably that a block qualifies only where every open line names a path and
all of them moved — narrow on purpose, because this should fire rarely and be worth
reading when it does.

## Block E — Adoption

## Block F — The plugin

### §RK1235 The write a stale copy should not make

RK1230 gave a shell caller the copy to invoke and left the write unguarded, which its
design said out loud: *worth deciding whether a stale copy should refuse to write at
all.*

The failure is quiet. A copy behind the wired one does not fail — it agrees with a rule
that has moved and writes a line its own version thinks legal, which the project's gate
then reports. `engines` exits 1 on the disagreement, and nothing consults it before a
write.

What makes it hard is that most disagreement is legitimate. A developer runs a checkout
on purpose; CI runs the action at a pinned ref; `install --vendor` exists so a project
can hold a version. Refusing every write from a copy that is not the registered plugin
breaks all three, and a refusal firing on correct setups gets routed around.

So the question is not *whether* to refuse but *what* on. Two candidates, to measure
first.

**Behind, not merely different.** `engines` already tells `behind` from `unpinnable`,
and only the first claims one copy's rules are older — leaving the modified checkout,
which is where a developer lives, untouched.

**And only where the project asked.** `[install] pinned` (RK1192) exists for a project
that has chosen its version. Declaring it is that project saying which copy is right,
which is the standing such a refusal needs and the only thing keeping it from being a
guess.

Either way it names `engines --invoke`, or it is a wall with no door.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
