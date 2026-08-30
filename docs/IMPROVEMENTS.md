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

## Block C — Query

### §RK1432 The count that cannot say what is startable

A project using this tool reported twenty open lines. Six of them could not be begun at
all: they waited on a console, a signing certificate, a CI runner or a second toolchain,
and no task in that repository will ever supply one. The number a reader meets first
said twenty.

THE DISTINCTION IS ALREADY MODELLED, WHICH IS WHY THIS IS SMALL. RK's own [requirements]
table exists for it, `pick --have` consumes it, and `brief` prints "absent RK63 is ready
and requires msvc-qt-webengine". Every part is there except the one that reaches a
reader who is not picking a task - the count.

SO THE ADOPTER WROTE IT THEMSELVES. That project added a flag to its own application
that reads ROADMAP.md, groups the open lines by the requirement each waits on, and
prints fourteen startable against six waiting. That is a hundred lines of C# re-deriving
what `pick` already knows, in a repository whose whole discipline is that the tool owns
the backlog and nothing else parses it.

WHAT WOULD ANSWER IT is a split in `stats`: the open count, then how many of them
nothing absent is holding up, and the rest grouped under what they wait for. `--json`
carries the same, so a project that wants the line in its own gate has it without a
parser.

A line naming two requirements is one line and not two, which is the arithmetic a count
built from requirements rather than from lines gets wrong.

## Block D — The gate

### §RK1433 Declared for the question, never asked

[criteria] is declared with its reason written into the config that opts in: "a number
that only leaves zero at the finish cannot tell half done from not started". A
partially-shipped line is precisely that state - the marker means some of it landed and
some has not.

A PROJECT USING THIS TOOL HAD SIX PARTIAL LINES AND CRITERIA ON ONE. The table had been
declared, used where the problem was noticed, and left empty everywhere else. Nothing
said so: lint validates every governed line and never asks whether a partial one carries
a definition of done, so the omission read as a file in good order for months.

WHAT WOULD ANSWER IT is a lint code over one relationship the tool already has both
halves of - the markers it validates and the criteria lists it writes. Where [criteria]
is not declared the question does not arise and the code never fires; where it is
declared, a partial line with no list of its own is what it names.

THE ADOPTER WROTE IT THEMSELVES, in their own test suite, reading ROADMAP.md for the
partial marker and for the per-task heading this tool writes. That is a project parsing
the file the tool exists to own, to check a rule the tool exists to enforce, and it is
the second time in one session that happened.

Where it lands is a judgement this line does not make: a lint code, or a row in `stats`.

### §RK1434 Two well-formed halves that contradict

A project added the non-goal "no local patch to the vendored C" while a line sat open
and ready whose entire content was editing two vendored C files. The roadmap forbade
work it listed as startable, and both halves passed every gate: the non-goal is a
well-formed bullet, the task is a well-formed line, and nothing compares them.

IT SURVIVED BECAUSE THE TWO ARE VALIDATED SEPARATELY. lint checks a non-goal's shape and
a task's shape, `pick` reads deps and requirements, and neither asks whether a
constraint reaches a line. The session that wrote the rule and the line that
contradicted it were the same session, minutes apart.

WHAT IT COST was a session picking that task meeting a rule that, read honestly, stops
it. The fix there was a clause naming the exception, which is fine prose and invisible
to every check: the next project to do this gets no more warning than the last.

WHAT WOULD ANSWER IT is narrower than it sounds. A non-goal is a lead and a sentence; a
task is a symptom and a why. Where a non-goal's lead names something a live line's
symptom also names, that is worth one advisory row - not a refusal, because a constraint
that bounds a task without forbidding it is ordinary and common.

An advisory is the right strength. The judgement of whether a rule reaches a line is a
reader's, and a gate that refused on a shared noun would be turned off in a week.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
