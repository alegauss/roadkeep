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

### §RK1062 A number that can be improved by moving text out of its view

`budget --tools` sums `descriptors(config)` and nothing else. The handshake is the other
thing a session is handed before its first call: `instructions()`, which carries the
engine line and — since RK1060 — the counting caveat that used to sit on 13 properties.

So the read has a blind spot exactly where an author will push. RK1060 took 3,159 code
units off the tool list and put roughly 390 back in a place this does not count, and the
verb reported the gross figure as though it were the net. The saving was real and most
of it survives; the point is that the same edit could have saved nothing and measured
the same, which makes this a number that can be improved by moving text rather than by
cutting it.

It also leaves `[tools] characters` guarding one half of a session's cost while the
other half has no ceiling and no reader — which is the state RK464 described about the
whole surface, now true of a corner of it.

The fix is small and the decision is what to report. A second figure beside the total is
honest and leaves a caller adding two numbers; one total with the split under it is what
the per-tool ranking already does, and reads as the one answer the verb exists to give.
Either way the instructions are per session, not per call, so they are counted once —
the same footing the tool list is on.

## Block D — The gate

### §RK1061 A gate that costs more than the thing it guards

RK1059 put a ceiling on what one served tool may cost, and paid for it on the wrong
path. `_served` calls `descriptors(config)`, which builds every subparser and renders 52
tool schemas — measured on this repository at **201 ms with the budget declared against
80 ms without**, so the check is two and a half times the rest of the gate put together.

`lint` is not a command run once. CI runs it, `.pre-commit-hooks.yaml` runs it, and the
Stop hook runs it on every turn that touched a governed file — which is the surface RK22
made cheap on purpose. A guard that costs a fifth of a second there is a guard somebody
turns off.

The guard is already narrow in the right way: a project declaring no `[tools]` pays
nothing, because the config is read before the import. What it is not is narrow in
*when*. The schema changes when this package changes and not when a roadmap line does,
so the answer is probably a cache keyed on something that moves with the source —
`provenance.engine()` already resolves the commit and whether the tree is dirty.

Worth deciding whether it belongs in `lint` at all. The number it holds is a fact about
the package, not about the repository being linted, so a check that runs where the
package is tested would catch every regression this one does and cost an adopting
project nothing.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
