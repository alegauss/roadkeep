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

### §RK493 Output rendering leaves the command surface

Measured: `cli.py` is 8,489 lines, 21% of the package. The composition is 2,100 lines of
`build_parser` and its vocabulary, ~5,200 of 82 handlers, 554 of `_print_*` and 631 of
`*_json`. Its growth rule is `agents.md`'s own — one subparser per task — so it is where
every task appends: the §0.3 drift in code rather than in prose.

The printers go first because theirs is the cut with no import cycle: not one `_print_*`
or `*_json` helper calls a handler or the parser, so the move is one direction of
imports. It also lifts out the half a verb's edit reads least — a handler changes what
is computed, and the sentence printing it is read once.

Two costs it does have, priced here. `agents.md` is at 125/125 lines and 8,296/8,400
bytes and a test holds the Layout index against every module, so the new module is an
index entry with 104 bytes of room and the compression belongs in this commit. And
`provenance.py` reads module names off a traceback, so a refusal decided inside a
printer starts naming the new file, which is the truth and not a regression.

What proves it: a pure move passes 130 test files, `serving.py`'s inventory is derived
from the parser it does not touch, and `lint` still passes on `docs/`. No supported
Python API means the rename breaks nobody.

### §RK494 The handlers take the names the domain modules already have

After RK493 the file is 2,300 lines of parser and 5,200 of handlers, and the handlers
are the part with no name: each of the 82 is reached through `set_defaults(handler=…)`
and grouped by nothing. Every other module here is one gerund whose docstring is the
authority on it; this is the one file where 82 concepts share a docstring.

So the grouping is the domain modules' own names — authoring, sections, shipping,
linting, querying, adopting — and where a handler lives is derived from what the verb
does. The import direction is `build_parser` importing them, which is why RK493 is a
dep: a handler still reaching a printer left in `cli.py` would import the module that
imports it.

What must not move, and why this is a split and not a rewrite. `build_parser` stays one
function: `serving.py` derives every MCP tool, its description and its stdin declaration
from that object, and two tests read the same one. `dispatch` stays one, because RK489's
rule is that one place refuses two answers.

The cost is a census: `tests/test_document.py` asserts which modules call `.block(` and
`.holds(`, naming `cli.py` for handlers that are moving. Updating it is the test doing
its job — it counts callers, and afterwards the callers are different.

Proven as RK493 is: exit codes unchanged, the served tool list unchanged, `lint` clean
on `docs/`.

## Block E — Adoption

## Block F — The plugin
