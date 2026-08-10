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

## Block D — The gate

### §RK489 Subjects and narrowing flags, declared once

`_budget` names its four subjects in a list, refuses two of them together, then checks
each narrowing flag against the subject that actually answered. That code is right, and
it is twenty-five hand-written lines of it, for one verb out of eighty.

Every other multi-subject verb either repeats the shape or does not have it. RK465 found
`--role` swallowed beside three subjects; RK466 found two commands taking two answers
and printing one; RK467 added a sweep over boolean pairs, which is a backstop and says
so — it finds the next one after it has been written, never before.

The facts are declarable at `add_parser` time: which flags are subjects of a verb, which
flag narrows which subject, and what the refusal says when two arrive or when a
narrowing flag stands alone. Declared there, one dispatcher enforces them for every
verb, argparse's own mutually-exclusive group covers the pair it can express, and the
sweep becomes a property that cannot fail rather than a search that has to keep running.

This is the tool's own thesis turned on itself: the saving is the analysis, not the
characters. A sweep reports after a flag has been added that nothing reads; a
declaration refuses before a subparser exists that can swallow one.

### §RK490 A remedy row derives what its finding already knows

`_TABLE` is total over the codes the package can emit and the suite asserts it (RK421),
so no finding reaches a caller without a door. What each row *states* is held to
nothing: the argv, the sentence describing the defect and the sentence describing the
repair are three strings an author wrote beside each other.

So the failures are per-row, and each is found by example. RK468: a row whose sentence
named one verb and whose remedy named another. RK470: a section remedy that omitted
which prose file the finding was in, visible only on a project declaring two. RK472: a
door `block drop` refuses, dispatched by `repair` anyway, because runnability was a
property of the row's kind instead of the finding's state.

Three different rows, and none of them the last one. What binds them is that a row
repeats what the finding already knows — its subject, its file, its verb — rather than
deriving it. Substitution reaches `{id}`, `{line}` and `{label}` and stops, which is why
`{first}` and `{role}` sat named and unsubstituted for years.

The repair is to make a finding carry the fields its door needs and the row name them,
so the table states only what is genuinely per-code. Then the agreement between a row
and the finding it closes is one property over the whole table, instead of a defect
discovered one row at a time.

### §RK491 The invariants this package holds, declared as a set

RK421 asserts the remedy table is total over the codes `linting` and `schema` emit.
RK467 sweeps every boolean pair a read takes, for the flag that answers as neither half.
RK474 checks that every complete door is an argv the CLI accepts. Three tests, in three
files, written weeks apart, each performing the same act: a rule about the *whole*
surface, held by enumeration rather than by example.

Nothing records that they are one family, so the question that matters cannot be asked —
which rules does this package state, and which does a property reach? They are stated in
quantity: in module docstrings, in the six laws, in this file's prose. Three are
reached. The distance between those two sets is where the defects of the last fifty
commits lived, and it is unreadable today, which is why each was found by being tripped
over.

The deliverable is that set declared in one place: each row naming the invariant, the
surface it quantifies over, and the property that holds it. A rule nobody holds is then
a row with an empty holder rather than an absence nobody can see, and a new invariant
costs a row and a property instead of a test somebody has to think of first.

It is this tool's own argument one level up. `lint` is the backstop for prose; these are
the backstop for the package — and a backstop nobody enumerated has its gaps found the
way this repository has been finding them.

## Block E — Adoption

## Block F — The plugin

### §RK488 One renderer for a message that offers a call

`provenance.invocation` answers how a shell reaches this engine and `provenance.serving`
answers which prefix this session's tools arrive under. Both are central, and neither is
what an emitter needs: what a module prints is a sentence *around* a command — a route,
a demotion, an offer, a refusal — and that composition lives at each site. So a fact
that changes shape, as the tool surface did, is applied by visiting every printer.

The count today: guarding spells a command thirteen times, provenance ten, serving nine,
capturing six, linting five, installing five. RK444, RK447, RK448, RK475, RK477 and
RK479 each moved one site, and nothing ever said how many were left — a literal command
inside an f-string is not something the suite can enumerate.

`remedying.Door` is the shape that already works: argv plus what it does, rendered as a
shell line or as a tool call by whoever prints it, with `foreign` for the door another
tool owns. What is missing is that every other emitter goes through it, and a property
that no module outside the renderer spells a command at all — the same total-domain
assertion RK421 makes about codes, which is what turned the remedy table from a
convention into a schema.

Then a seventh surface costs one change, and the tool's own L1 holds where it currently
does not: enforced where the text is created, rather than found afterwards one message
at a time.
