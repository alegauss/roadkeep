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

## Block E — Adoption

### §RK445 The count that outlived the rule under it

RK439 narrowed what declares a block: a heading inside another's subtree is owned by
that region rather than being a second address for it, so Shio's eight `### Block K
follow-ups` are one Block K and the writes they used to refuse now land.
`Document.declaring` is where that rule lives and every gate and every write path reads
it.

`adopt` does not. Its estimate builds the block list straight off `document.headings`,
filtering on nothing but whether a heading carries a label, so the nested shape comes
back `B, B, B` — measured on a three-heading ledger, and Shio's own would report Block K
nine times. That line is the first thing an adopting project reads about its own corpus,
and it is the number a `[files]` declaration and a first `lint` are decided from.

It is the same defect RK439 fixed, one reader over: two expressions of "which blocks
does this file declare", one of which was narrowed. The repair is to read the one that
was — but the estimate wants the labels in file order and `declaring` answers about a
label already named, so what closes it is a walk that asks that question per label
rather than a second filter written here.

Open: whether the estimate should also say a label was grouped, since a corpus that
nests is one where a reader looking for a heading per block will not find them.

## Block F — The plugin

### §RK444 The only unconditional message points at the wrong engine

RK82 gave the session its resident line and decided on purpose that it would not repeat
the write path, a rule in two places being two places that can disagree. That holds.
What it did not separate is the rule from the route: the notice already publishes one —
`invocation()` — for the read verbs it names, on projects where `install` wired
`.mcp.json` and pre-approved the server. So the only message every adopting session
receives points at the shell on exactly the projects that have the tools.

The consequence is the shape of the door. The deny is already right, listing this
session's tools first and the shell second, under the prefix RK333 taught it to read —
but it fires only on a hand-edit. The agent that behaves, never touching the file and
reaching for a command instead, is the one that never sees the list. The skill carries
the same instruction and loads on a trigger, one sentence among two hundred and fifty.

What changes is one clause: where the tools are served the route named is the served
prefix, and where they are not it stays the invocation. `served` is already a field here
and already carries the `mcp__plugin_<plugin>_roadkeep__` form, so nothing new is read.
The write path stays the skill's — this states which engine answers, which is the same
kind of fact as which files are governed.
