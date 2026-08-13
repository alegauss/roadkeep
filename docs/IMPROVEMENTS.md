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

### §RK1157 A name that cannot be mistaken for the answer

`Tool.exposes` is the **declaration** and `Tool.exposed(config)` is the **answer**: the
first is a literal tuple, the second adds whatever `conditional` this project opens
(RK111). The names differ by one letter, and the one a reader reaches for first is the
one that is not the answer.

Measured twice in three iterations. RK1147 claimed `adopt` never named the flag that
changes its estimate — read off the `Estimate` object, while the report had named it
since RK285 — and was restated once the command was run. RK1156 claimed an outline
project cannot file over MCP, read off `Tool.exposes`; `exposed(config)` ends in `ref`,
a served `add` takes it, and the line was retired.

What makes it worth a change rather than a resolution to be careful: `serves()` reads
`exposes` **deliberately**, and says so — it is composed inside a hook the harness waits
on, and asking the config would cost the parser build RK261 removed. So both readings
are legitimate, they coexist in one class, and the cheap one is the one that looks
total.

The fix is the project's own thesis applied to its own API: make the wrong reading hard
rather than documented. A declaration named `declares` (or `whitelist`) cannot be
mistaken for the answer, and `exposed(config)` stays the one thing a caller asks. Eight
call sites and the `_WITHHELD` closure name it, so the rename is mechanical and the
closure proves it total.

What needs deciding: whether `serves` keeps its cheap reading under a name that says
*cheap*.

### §RK1158 The floor is declared and nothing reads it

`pyproject.toml` declares `requires-python = ">=3.11"` and this machine develops on
3.13, so an API newer than the floor is green here and red only in CI. It happened:

```
tests/test_backlog.py:910: TypeError: Path.read_text() got an unexpected keyword argument 'newline'
```

`newline=` on `read_text` is 3.13. The call was written, the suite passed, the task
shipped, and the gate that found it was the one this repository ships as an action
(RK17) — one commit later, in a log somebody had to read.

CI catching it is not the same as catching it, and the difference is this project's own
thesis: a limit reported after the prose exists asks the author to delete work. Here it
asks them to fix a shipped commit, and the round trip is a push, a wait and a log.

The shape that fits: a closure that scans the package and the suite for a **declared**
set of calls newer than the floor, with the floor read from `requires-python` rather
than restated — the same arrangement `test_linting`'s index and `test_surfaces`' staging
closure already use. Declared and not derived, because deriving *every* API's version
needs a table of the standard library nobody here maintains; what a row costs is one
line, and what it buys is that the next one is caught before the commit rather than
after it.

The alternative worth weighing: a linter with a `target-version`, which knows the whole
table and costs a dev dependency plus a configuration this repository has so far not
needed.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
