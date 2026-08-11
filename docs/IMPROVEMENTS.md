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

### §RK1074 A census everything was supposed to ask

RK496 wrote `tests/surface.py` because seven suite-wide surveys each derived their own
file set and each was written against the layout of the day. It declared the set once
and had the surveys ask for it.

The addresses did not follow. Moving two modules into `kernel/` for RK1069 broke seven
tests in a row, each because a *path literal* somewhere had to be edited: the cache
inventory's `("document.py", "_parsed")`, the modules a denial may load, the two that
may declare a default, a `callers.pop("document.py")`, the traceback note's expected
pair, a re-export read through `from roadkeep import schema`, and the Layout index.
Every one green afterwards, none of them wrong before — which is exactly the failure
RK496 names, arriving through the addresses rather than through the file set.

The shape that would have held it is the one already there: a module is `surface.Module`
with a `where`, so a test naming one should name it through that rather than by writing
the string. Whether that means a lookup by symbol, a helper that resolves a name to its
current address, or simply a test asserting every literal in the suite matches a real
module, is the work.

Worth doing while the move is fresh: seven edits is the measurement, and the next
reorganisation pays it again with no reason to expect the same seven.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1073 The recursion one function got and its neighbour did not

`Engine.stale` names this package's changed modules by their path **under** the package,
recursively, because RK494 moved eight handlers into `src/roadkeep/verbs/` and a `glob`
would have missed every one. `raised_in` answers the other half of the same note — which
modules were *executing* when a refusal was decided — and kept the flat test: a frame
counted only where `where.parent.name == _HOME.name`.

So the two halves have been spelling a module differently since RK494. Every refusal
decided inside `verbs/` named nothing, and the note that compares "what changed" against
"what decided this" was comparing a recursive answer with a shallow one. Found by
RK1069, which moved two modules into `kernel/` and made a `why.too-long` — the exact
refusal §RK267 was written from — name only `authoring.py`.

Fixed here rather than filed: the frame filter now resolves against the package root and
names the path under it, which is `stale`'s own rule and the same string.

What is worth taking from it is that the pair had no test asserting they agree. Each is
covered on its own, and the note is composed from both — so a third reader of "which
module is this" would be free to invent a third spelling. `tests/surface.py` already
declares the one census the suite quantifies over (RK496), and this is that argument
about a *name* rather than about a file set.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
