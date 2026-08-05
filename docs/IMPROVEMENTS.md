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

### §RK310 The rationale a task was filed on decays, and nothing records that it did

A design section is written when a task is filed and read when somebody claims it, which
can be a year apart. In between the codebase moves, and the section does not: it keeps
arguing from whatever was true when it was written.

Measured in one block of eleven tasks, twice. One section proposed a `from` field for a
redirect and argued for it at length; the implementation found that using the post's own
friendly URL removed a lookup, a uniqueness rule and a shadow rule, all of which already
existed. Another dismissed an on-demand image-resize endpoint as "a new subsystem and a
cache-invalidation question" — and that subsystem had shipped two blocks earlier, so two
of its three options were about building something built.

Both times the task got smaller and better once the section was checked against the
code. Both times `ship` then deleted the section with no trace that its reasoning had
been wrong, so the next reader of the ledger sees an outcome and no warning that the
file does this.

What would help is small: a way for `ship` to record that the design was superseded, and
by what. It is not a new document — the ledger entry is already the one place both the
section's address and the outcome meet. The value is that a *pattern* becomes visible:
if a third of claimed sections turn out stale, that is a fact about how far ahead this
tool should let anybody design.

### §RK311 Pricing a body that already exists

Filing thirteen tasks in one session produced **fifteen** `body.too-long` refusals.
Three asked for one or two words. Each refusal discards the whole body, so shaving one
word means re-sending about 250 — roughly 3,750 words re-transmitted to remove 85 words
of overage.

`add`'s own docstring names the principle: a limit reported after the prose exists is a
limit discovered too late to save the tokens it was meant to save. That is what the body
limit does. `budget` prices the ceiling before a word exists, which is the right half;
the missing half is any way to price a draft that already exists short of attempting the
write.

The asymmetry is what makes it expensive. A refusal over `symptom` or `why` costs a
phrase. One over `--section-body` costs the whole rationale, and leaves the author
counting words by hand against a number the tool has already computed exactly.

Three candidate fixes, cheapest first. An `add --check` that validates and writes
nothing, so a body is priced at the cost of a read. Or the refusal reports the count per
paragraph, so the author knows where to cut rather than only that a cut is needed. Or
`--section-body` accepts an over-long body under `--trim` and reports what it dropped.

The measurement is the argument and it reproduces: any session filing more than a few
tasks pays it.

### §RK312 A required argument nothing helps you compute

On an outline-scheme project, `add` refused with `ref: every task points at its
rationale section [ref.missing]`. The refusal states the rule and names nothing that
answers it. `anchors --family XVII` answers it exactly — free addresses under a family,
which is the number `--ref` wants — and there was no way to learn that from the refusal.

Two reads were needed instead. Which family holds a block's prose is derived nowhere:
the mapping came from globbing existing pointers per block, `list --block Q | grep -oE
"§[IVXL]+"`, repeated for four blocks. Then the next free number under that family came
from grepping the prose file for `^### XVII\.` and reading the tail. Both are questions
`anchors` was built for, and one of them — block to family — it does not answer at all.

This is roadkeep's own standard applied to itself. A refusal that states a rule without
naming the verb that satisfies it is the shape the project rejects everywhere else, and
it is worse here than usual: `--ref` is required, unguessable, and wrong silently if a
caller picks a number some heading already spent.

Two fixes, and the first is a string. `ref.missing` should name `anchors --family <the
block's>`, with the free address in the message when the family is derivable from the
block. Second, `anchors` should be able to report per block, since a caller reaching for
it already knows which block the task is in and not which numeral its prose lives under.

## Block C — Query

### §RK303 First match, at the one door that had not learned it

RK172 taught resolution that a pointer addresses every governed prose file, and RK186
taught `show`. Two roles declaring one anchor is the ambiguity and not a first match:
`_rationale` answers *"§X is declared by both: one anchor names one section, and a
pointer resolving to two resolves to neither"*, and `lint` reports `section.ambiguous`
at both headings.

`body_budget` (RK283) resolves the role by walking `PROSE_ROLES` and taking
`declaring[0]`. Reproduced on a project holding §IX.1 in both files: it answers
`improvements, 2 written, 248 left` while `show` refuses the same anchor. So the read
built to state a limit before the prose exists states one for a section the author
cannot address — and the number is right about a file that was picked rather than named.

It reaches two commands: `budget --anchor`, and the `section` field every `budget` now
carries (RK301), where the anchor is the line's own pointer and the caller never typed
it.

The direction is the one every other reader took, and the refusal already has its words.
What is worth deciding is whether `--role` stays the way through — it is the caller
naming which of the two they mean, which is the only thing that resolves the ambiguity
without a verb choosing.

## Block D — The gate

## Block E — Adoption

### §RK305 A majority that measures the backlog, not the file

RK288's guard is right about the alarm it silences and wrong about how it decides. It
prints `--ref-scheme <other>` only where the other scheme accounts for more headings
than the declared one — a proxy for *this file is really addressed the other way*.

The proxy holds on a static file. It does not hold here. This repository's rationale
file carries a permanent preamble anchored `0.1`-style and one `RK<n>` section per
**open** design, and a ship deletes the second kind. So the ratio falls with every task
delivered, and at the moment the open designs stop outnumbering the preamble the tool
tells a fully conforming file to be read the other way. Measured while shipping Block B:
five and five, one ship from the alarm, on a file reporting every heading conforming.

What the count cannot see is that the two kinds of heading are not competing readings of
one file. One is prose the project keeps and the other is a queue. A file whose declared
scheme parses **every** heading it was asked about has no minority reading to report,
whatever the ratio — which is the condition RK288 was actually written about, and the
one the majority was standing in for.

## Block F — The plugin

### §RK313 Doubt an agent cannot resolve

Two staleness warnings reached one session from two directions. The MCP `add` refused
and appended: this server imported roadkeep before `__init__.py`, `cli.py`,
`provenance.py` and `serving.py` changed on disk, so the refusal is what the code it did
import answered and restart if the harness has not reloaded. Separately the SessionStart
hook reported the project's copy of `skills/roadkeep/SKILL.md` had drifted from the
checkout answering, and that `install` refreshes it.

Both messages are honest and neither is actionable inside the session that reads them.
An agent cannot restart its own harness, and it cannot know whether the four named files
are the ones that decided its particular refusal without reading them. The outcome here
was to abandon the MCP surface and drive the CLI for all thirteen filings — which
worked, and left the protocol path untested for a whole session of real use.

That is the cost worth naming: the surface most likely to be stale is the one an agent
is most likely to be driving, and the advice for it is the one thing an agent cannot do.
A patch bump per commit (RK153) is the mechanism that should make this rare, and it did
not here.

What would help is a narrower claim. The server knows which files changed and can
compare them with the modules the refused verb touches, so a refusal the drift could not
have affected should say so rather than casting doubt on itself.
