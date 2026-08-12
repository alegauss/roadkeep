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

### §RK1110 The contents is a projection, and the paragraph beside it is not

RK1107 made the two unanchored regions addressable and stopped there, deliberately: an
address is what an author needs to edit prose, and half of a contents is not prose.
Reading the two live files says which half. Shio's `## Table of contents` is 21 lines of
`- [§X. Title](#slug)` — the anchor, the heading text and a GitHub slug, every character
of it already in the file it lists. claude-tray's is the same table plus a blockquote
saying which families are gone and that numbers are never reused, which no derivation
could produce.

So the row is a projection and the paragraph beside it is the author's, and the
machinery for exactly that split is already here: `exporting` replaces what is between
two markers the author put there, `refreshes` carries the write inside every transaction
that touches a governed file, and `export.stale` is the gate code with a remedy. A
`ship` that drops a section would rewrite the contents in the same commit that made it
wrong.

What has to change to admit it. `DEFAULTS` maps a flag to a literal path, and this
target's is the project's own `[files]` improvements — so it stops being a constant.
`Projection` is built from the three counted roles and knows no prose headings, so the
derivation is a second one. And the block sits inside a file `Document` round-trips,
which is the property to hold first: a splice that broke L3 on a governed file is worse
than the staleness it fixes.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1108 The environment the plugin never reaches

The plugin is the whole install on a developer machine, and there is one environment it
never reaches: Claude Code on the web reads settings and files committed to the
repository and installs no marketplace plugin. The hooks and the server never load, the
guard is absent, and an agent falls back to editing the governed files by hand — the
drift this tool exists to stop, in the environment with the least supervision.

Shio answered it with a committed `.claude/hooks/roadkeep-launch.py` that resolves an
engine at runtime and stands down where an installed plugin is present, so nothing
double-fires. That file is where the defect was measured: it looks under
`~/.claude/plugins` alone, so where `CLAUDE_CONFIG_DIR` moves the harness's real config
directory it finds a stale copy, defers to it, and no guard runs at all. A hand edit of
`docs/ROADMAP.md` and `docs/IMPROVEMENTS.md` passed.

`provenance.installed` already resolves that pair — the environment variable or
`~/.claude` — which is the whole argument for moving the launcher here: *which copy
answers* is this tool's own question, `engines` already reports it for three copies, and
a project re-deriving it gets one of them wrong quietly. What `install` writes is the
surface to put it on. Whether the fallback may clone over the network is a separate
decision and probably a no.

## Block G — The editor surface (the backlog where the file is open)
