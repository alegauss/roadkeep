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

### §RK1069 The move the test was written before

RK1065's title sequenced this — *held by a test before it is a package* — and the test is
what shipped. `tests/test_kernel.py` names `schema.py` and `document.py`, the one runtime
call above them (`exporting.refreshes`, RK188) and the one annotation (`Config`, under
`TYPE_CHECKING`), and holds the backlog vocabulary they declare as a ceiling: 47 names and
17.

A ceiling with nowhere to fall is where that leaves it. Both modules sit beside the
thirty they are supposed to be under, so nothing about opening either file says which
half of the package it is, and the rule that they import nothing above them is a test
somebody has to know exists rather than a directory that makes the violation not
compile.

The move is `src/roadkeep/kernel/`, and its cost is entirely in addresses: about
twenty-two import lines in the package, the `("document.py", "_parsed")` keys in the
cache inventory, `tests/surface.py`'s census, the Layout index, and `test_kernel`
itself. No behaviour, and the round-trip property test over three corpora is what says
so.

Worth doing after the vocabulary comes down rather than before. A directory named for
the mechanism, holding two files that define `Task` and `Dep`, advertises a boundary it
does not have — and the rename that fixes that is the larger half of this work, touching
every caller of the two names rather than every importer of the two modules.

## Block B — Authoring

## Block C — Query

### §RK1071 The citation reached the refusal and not the read

RK1067's argument is that an author standing over a limit should be one line from where
it was set, and it delivered that on the refusal: `limit is 150 (roadkeep.toml:10
[limits].why)`.

`budget` is the same author at the earlier moment. It exists precisely so the number
arrives *before* the prose does — that is the insight the whole tool is built on, the
saving being the analysis rather than the characters — and it prints `why 30 of 200
left` with no hint that 200 is this project's choice or this tool's default. So the fact
reaches the author on the path they take when they got it wrong and not on the path they
take when they are about to get it right.

`Schema.source_of` already composes the clause and `budget` already holds the schema, so
this is a print and not a mechanism. What needs deciding is the terminal's shape: the
read is a column of small numbers and a parenthesised address after each would drown it,
where one line under the table naming the file — and the two roles, since
`[limits.changelog]` differs — probably says it once.

The `--json` half is not a layout question and is simply missing: a payload that carried
the origin beside each figure would let the surface that serves this over MCP answer
*why is it 200* without a second call, which is the read that costs a turn.

## Block D — The gate

### §RK1070 An inference over a list nobody declared the shape of

RK1068's fold is right about the population and loose about how it reads one.
`_grammatical` scans the finding list for two codes — `line.non-canonical` and
`line.unparsed` — counts them against a role's bullets, and removes them with `finding
not in broken`, which is identity over a dataclass.

Three things follow that nobody declared. The pair of codes is a literal in the
function, so a third way a line can fail wholesale is folded only if somebody remembers
to add it there. The removal is by value equality, so two identical findings on one line
— possible, since nothing forbids it — are dropped together or not at all. And it runs
after every per-line check by position in `_examine` rather than by anything that says
it must, which is the arrangement RK365 already replaced once for the ordering.

`_untainted` is the same shape one step away and has the same property, which is the
argument for doing this once rather than twice: it suppresses by
`code.startswith("char.")` and by `(file, lineno)`, and the two functions are both *a
finding that explains others* without either saying so.

What that suggests is a small declaration — which codes explain which, and at what scope
— read by both. It is the shape `referring.py` took for relations and `remedying.py`
took for doors: the index is the thing, and the loop over it is four lines.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
