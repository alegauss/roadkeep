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

### §RK1014 The heading the two queue verbs each leave to the other

Reproduced on a fresh `init`, and again here while putting a task at the front of the
order. `priority add` answers *no priority heading — add `## Priority` above the
blocks*, and `priority migrate` answers *nothing is waiting to move: `priority add`
writes the first entry*. Each names the other and neither writes the heading.

What that leaves is a hand edit of a governed file, which is the single act this tool
exists to own and the guard denies by name. The workaround taken here was three steps
and a fourth file: declare the queue in the config, migrate it into the roadmap, then
delete the config line the gate then reports as `priority.config`.

The shape of the answer is already in the tree. `block add <x> --title` opens a block
heading in every governed file organised by one, written for exactly this — the moment a
write refuses with *no heading declares*. A queue heading is the same act with no title
to choose.

What must not change is which file wins: the section beats the config wherever both
exist, and a project that never wanted a queue must still get no heading.

What proves it: `priority add` on a project with neither writes the heading and the
entry in one transaction, the refusal that sent a caller to an editor is gone, and a
project that never calls it still has no section.

## Block C — Query

## Block D — The gate

### §RK1012 The two the backstop register found

RK1004's rows are three answers, and these are the only two of the third kind. `section
add` refuses a body with no prose and a heading with no title; a file carrying either
lints clean, measured on a fixture whose line points straight at the heading.

Neither is cosmetic, and the pointer is why. A line renders `→ §<id>` and the gate holds
that the address resolves — so a heading with nothing under it satisfies that check
while giving the reader none of what the pointer promised. `show` prints the section and
`brief` hands it to whoever starts the task: both answer with a title and a blank.

The five rows beside them are a different answer and stay silent: a heading is one line,
so a newline in a title is about an argument, and an address this scheme cannot read is
not parsed as a section at all, so the heading is prose. Those are not holes, and a code
for them would be a red nobody keeps.

The gate already walks every section for its budget and its query, so this is that walk
asking two more questions of what it holds — and both are the door's own rules, which is
what keeps the wording one sentence rather than a second judgement.

What proves it: a file carrying either exits 1, the register's two rows move to a gate
code, and prose under an unreadable address is still clean.

### §RK1015 The half of a door a caller outside this process cannot read

Met building the problems panel. A remedy carries `kind` and a list of doors, and
`deps.unknown` is one `decide` holding two: `gaps`, which answers a question and changes
nothing, and `amend <id> --dep …`, which writes. The kind is the remedy's, so it says
`decide` about both.

What a reader outside this process needs is per door: whether pressing it changes the
files. The client written here could not ask, so it does the only safe thing — shows
whatever came back and re-reads the gate, which is one extra run of a command on every
read door and a refusal to promise the caller anything about what they just pressed.

`Remedy.runnable` already draws almost this line for `repair`: a `read` is *not*
runnable there, because its command is safe and useless inside a repair loop. That
reasoning is about the kind, and the same sentence one level down is what a door is
missing — the loop and the panel want the same fact and only one of them can get it.

The shape is a field on the door and not a second table: the argv is already there, and
what it does is a property of the verb the tool itself parses.

What proves it: every door says which it is, `repair` reads that instead of the kind,
and a remedy holding both kinds is still one decision with two doors.

### §RK1016 The half of the index nothing holds

RK203 made the Layout index a gate rather than a habit — but only over `src/roadkeep`.
The lines under it name the other surfaces by hand: the gate's three, the plugin's five.
Nothing checks those, and the count in the prose is now wrong — `editor/` and
`scripts/build_vsix.py` shipped this week and the index mentions neither.

The failure is the one RK203 named. An index that silently stops being an index is worse
than no index, because a turn reads it and concludes the thing is not there — and a
surface is exactly what a turn looks for before deciding where a change goes.

What makes it more than an edit is the room. `agents.md` is at 125 of 125 lines and 98
bytes, so naming a sixth surface is a compression decision and not an append, which is
the shape RK493 already had once and the reason that file's budget exists at all.

The check is decidable the same way the module one is: a top-level entry this repository
carries that the index does not name, over a declared list of what counts as a surface —
a directory a manifest or a workflow reads, which is not every folder in the tree.

What proves it: a surface added tomorrow with no entry is red, the two that shipped are
named, and the file is still inside the budget it declares.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

### §RK1010 Where the client lives, and what proves it

The action, the pre-commit hook, the plugin, the skill and the stdio server all ship
from this tree, and each is declarative: a YAML file or a Markdown file, no build, no
dependency tree. A packaged editor extension is not that. It is a compiled language, a
lockfile, and a publisher account, in a repository whose stated cost is zero runtime
dependencies.

The argument for keeping it here anyway is the one that decided the stdio server: the
failure to avoid is a second implementation of the rules, and the only thing that keeps
a client honest is a test that runs the client against the command that answers it.
Across two repositories that test belongs to neither, and the client grows a Markdown
parser the first time a round trip feels slow.

So: a subdirectory with its own manifest and its own job, gated on this repository's own
`docs/`, and a Python side that gains no dependency and no build step. The split stays
cheap on purpose — a client that never parses the file is a few hundred lines with
nothing to port — so if the publishing cadence turns out to fight a version this
repository bumps every commit, moving it out is a decision made later with evidence
rather than now without.

### §RK1017 The read that is about the tool and not about the backlog

Counted from what the view does: every save re-runs `list`, `engines`, `lint` and one
`deps` per open line. One of those answers a question that did not change. `engines`
asks git which commit the package's files are at — a fact about the *installation*,
which moves when somebody upgrades and not when a line is edited — and `provenance` says
so: it is asked at most once per process and never on a path that writes. A CLI
invocation is a process, so a view that shells out per save asks it per save.

Readiness is not the same defect: `deps` answers about the file, so re-asking it after a
write is the point. What is re-asked wrongly is the half about the tool.

The cost is a subprocess and a git call on a keystroke somebody makes without thinking,
in the one surface whose whole argument is that it costs nothing on the sessions it does
nothing in.

The shape of the answer is the one this package already uses for the same question:
cache it for the life of the window and re-ask it when the thing it is about could have
moved — a refresh somebody asked for, and nothing else.

What proves it: a save runs the reads about the file and not the one about the
installation, an explicit refresh runs both, and the row still names the copy that
answered.
