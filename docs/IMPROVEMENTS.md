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

### §RK1021 The inventory L5 has been waiting for

L5's row in the register says what it needs, and says it is a task rather than a test: a
property over *the questions somebody asks* has nothing to sweep until those questions
are written down. L6 was in the same state and RK1000 moved it, which is the whole
reason the row carries a sentence instead of a blank.

What exists is the converse, and a converse is not the rule. RK167 holds that every
command this surface publishes is one the CLI parses; nothing holds that a question a
maintainer has is answered by one. A tool can publish forty verbs and still send
somebody to an editor for the one thing they wanted.

Measured before proposing: the CLI declares 27 read-only verbs and the skill's query
section names 21 in prose. The six it does not are `stats`, `audit`, `guard`, `mcp`,
`replay` and `report`, two of which are questions a maintainer plainly asks. The
inventory is half-written already, in the file every adopting project loads, and nothing
joins it to the parser.

The bound has to be honest, which is what makes this checkable at all: not every
conceivable question, but every question this project has written down. That is the same
bound the register already accepts about the six laws, stated there rather than
pretended away.

What proves it: each declared question names a command the CLI parses and only reads, a
verb that answers none is named, and L5's row carries a holder.

## Block D — The gate

### §RK1020 The imports nothing spells

Swept once, with the `__all__` re-exports excluded because those are a module's own
statement of what it publishes: six names across four modules — `guarding`, `linting`,
`remedying` and `shipping` — are imported and never spelled again.

None of them breaks anything, which is why they accumulate. What they do is make a
module's import list a false answer to the question a reader asks it: what does this
need. This package spends more care on that question than most — the deferred imports
RK260 argues for, the one-way edge `verbs/` was split to keep, the two modules
`test_configured` exempts because a default is declared there — and every one of those
arguments is read off the imports.

Nothing reports one, and nothing can today: this tree has no linter and takes no dev
dependency that would bring one, which is the same decision it makes about runtime
dependencies and for the same reason. So the check belongs where the other source
surveys are — over the set `tests/surface.py` declares, with the same shape as the scan
that holds L6.

The exclusion is the whole risk and it is small: a name in `__all__` is published rather
than used, and a module that re-exports is saying so out loud. Anything else is either
spelled or it is not, which an AST decides without judgement.

What proves it: an import nothing spells is red, a re-export is not, and the six above
are gone in the commit that adds the check.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
