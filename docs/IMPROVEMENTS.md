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

## Block F — The plugin

### §RK1246 The field four messages share

Four records carry `served` — `Refusal`, `Notice`, `Review`, `Unattested` — each filled
at its own site from `served_by(config.root)`. Four sites, one fact, nothing holding
them together.

Not a theory. RK479 found `Unattested` was the one **not** wired: it rendered a route a
served session could not call, and somebody found it by reading the message. The test
written then holds that one record, leaving the property asserted per instance by
whoever remembered.

RK1244 is the same family the other way round. RK1242 added a second field beside
`served` on one of the four — a three-way answer stored as two — and the census in
`test_spelling` swept both spellings and passed, because it compares what a message
*offers* and has no opinion about what a record *holds*.

So the missing instrument is a census of the carriers: every record with a `served`
field and the site that fills it, asserted total. A fifth added tomorrow is red until
somebody says which site fills it — `remedying`'s table over every code, `PREVENTION`
over every finding, `SITES` over every composed command, applied to the field four
messages share.

Two things to decide. Whether the census reads the field name or a marker the records
declare, a name being what drifts. And whether it asserts the *site* or only that one
exists: the second is cheap and would have caught RK479, the first also catches a site
filling it from something other than `served_by` — a case nothing has met yet.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1245 One comparison, two units

`budget --session` exists so an author can decide between cutting a tool description and
cutting a paragraph. Since RK1243 it prints three figures in two units:

    session    54925 utf-16-code-units once, 7366 bytes on every turn
      once      54639  56 tool(s) and the handshake, at connect
      once        286  the session-start notice, +34 of 320
      turn       6906  agents.md

The split used to be defensible, because the two cadences were also two kinds of thing:
a JSON payload a client validates, and a file on disk. The notice broke that. It is a
**message handed to a session**, exactly as `agents.md` is, and it sits under `once` in
code units beside a file under `turn` in bytes.

So the read whose whole purpose is a comparison now asks the reader to make it across
units. On ASCII prose the two agree and the defect is invisible; on a paragraph carrying
the status markers this tool writes, `agents.md` measured in bytes is three times its
length in code units, and the choice a reader makes from these numbers is the wrong one.

What is probably right is that a **resident file is prose too**, and prose is counted
the way RK430 says everything here is counted. `[budgets]` declares `lines` and `bytes`,
so the key stays and the report gains the reading a model actually pays for.

To settle before touching it: `bytes` is the declared limit and `lint` refuses on it, so
a report in another unit is a read and a gate disagreeing — which is the shape RK1243
just closed for the notice, by moving the *gate* rather than the report.
