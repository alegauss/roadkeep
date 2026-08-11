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

### §RK1092 A budget met by having nothing left

`agents.md` stands at 8,392 bytes of 8,400 and 123 lines of 125. RK1091 added one rule
and paid for it by compressing the conformance paragraph and the skill paragraph, which
is exactly what RK203 says the budget is for — and the room it bought is gone.

The gate is working and the next edit is what shows the difference between a budget and
a wall. A wall refuses the next sentence whatever it says; a budget refuses the
*cheapest* sentence, which is the one whose removal costs least. Eight bytes cannot tell
those apart.

Three places the file could give. The Layout index is ~20% of the lines and grows only
when the package does, and RK203 already says to compress the prose instead — an
argument made when the prose had slack. The six laws are a compressed copy of §0.3,
which is authoritative, so a row here is a second statement by construction. And the
opening restates §0 of a file its own first sentence links.

What would settle it is asking what an agent actually reads. This file is loaded every
turn and nothing measures which paragraphs a turn uses — `budget --file` says what it
costs and nothing says what it buys. That is the gap `budget --tools` closed for the
served surface (RK464), one file over, and the read that would make the next compression
a measurement.

## Block E — Adoption

### §RK1093 The category that is a function body

`_gains` is four `if` blocks: the store off `[files]`, a prose file off `PROSE_ROLES`,
the non-goals off `[non_goals]`, the queue off a heading in the document. RK1089 built
the category to give the fourth somewhere to land and RK1090 landed it — by adding a
fifth block to a function that was already four.

The shape this project uses for exactly this is one file over. `referring.PAIRS`
declares which pairs exist and the gate walks it; `remedying._TABLE` declares which code
has which door and a test holds it total over what the gate emits. A gain is the same
kind of thing: a name, a predicate over what the project declared, and a sentence saying
what it has instead.

What a declaration buys here is the closure. Today nothing can ask *is every door this
format opens named among the gains* — the answer lives in a function body, so a fifth
door added to the tool is a fifth door the estimate silently does not mention, which is
precisely the failure RK1089 was filed about and RK1090 demonstrated one iteration
later.

The predicate is the part that resists: three read a config and one reads a document, so
the declaration carries a callable rather than a key. That is the same thing `_BOUNDS`
does in `serving.py` — a lambda over `Config` per field — and it is worth copying rather
than inventing, including its own rule that what varies is data and what traverses is
code.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
