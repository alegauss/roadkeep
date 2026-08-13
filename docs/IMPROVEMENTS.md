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

### §RK1168 A namespace is a migration, not a config key

`section move` is the model to copy: it re-addresses a section and takes its subtree and
every `→ §<anchor>` naming it, or it takes none of them. Declaring `[refs]` is the same
kind of event at file scale — every heading in that file changes address at once — and
it carries nothing.

Measured adopting it on Viglet Turing, where two prose files had 13 doubled addresses.
`[refs] strategy = "S"` re-addressed 48 headings and put `section.ambiguous` at 0, and
left 28 of that file's own citations behind:

    7   became ref.dangling — the address exists in neither space
    21  kept resolving, into the OTHER file's section of the same address

The second half is the dangerous one: both files declared that address — which is why
they collided at all — so the citation still resolves and `lint` says nothing. Repairing
all 21 moved the total from 46 to 46.

Two asks, and the first is worth little without the second:

- **Carry the citations.** When a namespace is declared or changed, re-address
  that file's own citations in the same transaction, as `move` does for the
  pointers at a section. A body it cannot rewrite should refuse the call whole.
- **Report the ones that cross.** A citation resolving into a different prose
  file, where the citing file declares that same address, is a finding — a
  reference the author cannot see is wrong.

Without them, adopting the config key means a hand-rolled classifier and one `amend` per
section, which is the migration the key looked like it was.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1165 A run is one fact, said once

`gaps` on this repository prints **503 lines**, and 499 of them are one fact. Every row
of the run reads the same way — *never carried: the whole history mentions it nowhere* —
with only the number changing, from 501 through 999.

Measured: the never-carried ids are a **contiguous run of 499** plus exactly two singles, at 80 and
224. The run is a numbering jump — this backlog restarted its series at a thousand — so it is
permanent, unactionable, and 499 rows on every run for ever.

The two singles are the signal: each is a number the counter spent and no commit ever
carried, which is the reading RK95 built. They are findable today only by paging past
the jump.

This is RK1143's rule one command over — a row that is never the next step makes the row
beside it unread — and the shape is already in the format: a **range** is how this tool
spells many ids at once. One line for the run, rows for the singles.

What needs deciding: whether a run is collapsed by size or by *reason*. A jump in the
series and five ids somebody burnt in one afternoon are both contiguous, and only the
first is permanent.

Worth stating because it decided the prose above: naming those ids here is refused
(`body.promise`, RK431), an id in this prefix that no line carries being read as spent.
The rule found this section, which is the rule working.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
