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

### §RK1418 The pointer the fixer could write and the report says it cannot

Measured on a throwaway tree configured by `init --existing`, with one line and no `→ §`
on it. `lint` reports `ref.missing` with the cause *the scheme cannot derive this
pointer, so the anchor is the field you name*, and the door `amend RK1 --ref …`. The
project's `ref_scheme` is `id`, where the anchor **is** the id: the sentence is false
there and the only value the flag accepts is the one the schema would have written.

`ref.mismatch` already varies on exactly this question — `_varied` turns it from a `fix`
into a `compose` where the scheme is not `id`, because there an address is not
derivable. This is that same row pointed the other way and it never got the mirror, so
the strict half of the pair is stated on both projects.

What it costs is the two verbs that exist to spend nothing: `lint --fix` and `repair`
reach only what is derived, so both print the finding and close nothing, on the
commonest scheme and on the first gate run of an adoption.

The shape is `_varied`'s: `fix` under `id` and `compose` under an outline. Worth
checking before writing it is what the fixer should then do about the section — writing
the pointer makes the finding `ref.unresolved`, which is a different and correct report
about a design nobody has written.

### §RK1419 A verdict from a verb that also writes

RK271 split a **fault** from a **verdict** so that `lint` exiting 1 with a finding stops
carrying two lines about roadkeep possibly being wrong. The test is `not faulted and
code == EXIT_GATE and _only_reads(args)`, and that last clause is a proxy: it asks
whether the command writes, not whether the exit code is an answer.

Two verbs fail it. `lint --fix` repairs the derived and exits 1 while anything is left,
which is the same verdict the read gives about the same files. `repair` runs every
complete argv and exits 1 for the same reason — and it is the verb the report tells a
reader to reach for, so the offer lands at the end of the busiest correct answer this
tool gives.

Measured on a tree with one `ref.missing`: `lint` closes with the finding, `lint --fix`
and `repair` close with `report --symptom … --why … -- lint --fix`. The three answered
identically about the files.

The shape to argue about is whether the seam is a per-parser declaration — a verb saying
*my `EXIT_GATE` is a verdict* the way `reads_only` says what it locks — or the narrower
reading that `EXIT_GATE` is by definition a verdict and only a fault ever earns the
offer. The second is smaller and removes the flag rather than adding one; what it needs
checking against is every other verb that returns that code.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
