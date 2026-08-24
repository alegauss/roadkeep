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

### §RK1328 RK1328

Measured here, 2026-08-23, declaring `[criteria]` on this repository for RK1323: the
table went in by hand, because no verb opens one.

RK1313 closed this for a project being scaffolded - `init` now writes `[criteria]` empty
and the requirement vocabulary commented - and named the shape while leaving the other
half open: *the remedy each refusal names is a hand edit to configuration this tool
owns, which is what RK1264 built `declare` to remove, and which over MCP is not an edit
at all*. Every project already past `init` is that other half, and so was this one.

The two verbs that write this file cover different axes and neither covers this.
`declare <role>` retrofits a **file**, which is RK1264's own case: `[files]` is written
once by a command that refuses to run twice. `govern <address> <n>` writes a **number**,
against a reading. An opt-in table carries no number at all - declared at all means
governed - so it falls between them.

What decides the shape is whether that is a third verb or a widening of `declare`: the
argument there is a role and here a table, and both are *this file, one key, refused
where it is already declared*. The refusal a caller reads today names the table; what it
cannot name is a command.

Falsified if `govern` accepts an address with no number, which would make this a flag
and not a gap.

## Block F — The plugin

### §RK1325 RK1325

Measured 2026-08-23 on a tree `roadkeep init` had just made - no `.claude`, no
`.mcp.json`, nothing wired. `served_by` answered `mcp__plugin_roadkeep_roadkeep__` for
it, and `mcp__roadkeep__` for this repository, which does declare one. So every door in
that project's payload carries a `call` naming a tool that project has nothing to answer
with.

RK449 states the rule the other way: where nothing serves the door, only the argv is
published. The fallback makes *nothing serves it* unreachable - a root with no
declaration inherits whatever the running environment has, and the payload then asserts
about the project what is true about the machine.

Both readings are defensible and that is the decision. `served_by` takes a root and
reads `.mcp.json` under it, which is a question about the project; its docstring says
*the prefix this session's tools arrive under*, which is a question about the process.
They agree on every wired project and part company on an unwired one, which is exactly
the adopter this tool ships for.

It also cost a test. An equality over a ship's event had to stop comparing the door
whole, because whether `call` is present depends on the machine the suite runs on.

Falsified if a served caller can act on a project other than the server's own, which
would make the prefix right and the root the wrong argument.

### §RK1326 RK1325

Measured 2026-08-23 on a tree `roadkeep init` had just made - no `.claude`, no
`.mcp.json`, nothing wired. `served_by(root)` answered
`mcp__plugin_roadkeep_roadkeep__`, and this repository, which does declare one, answered
`mcp__roadkeep__`. So the fresh project was handed the prefix of a plugin it has no
relationship with, and every door in its payloads carries a `call` naming a tool that
cannot act on it.

RK449 states the rule the other way: where nothing serves a door, only the argv is
published. That is exactly the state here, and the fallback answers anyway.

Two readings, and they are not the same question. *Which surface serves this session* is
a fact about the process, and the fallback is right about it: a caller inside a plugin
session does reach these tools. *Which surface serves this project* is a fact about the
root that was passed, and it is the question the argument makes it look like. Everything
downstream reads it as the second - the door is published beside a project's own answer,
and a client runs what it names.

The fix is to decide which one the argument asks, and where it is the project's, to
answer nothing when the project declares nothing.

Falsified if a served call reaches whatever project the caller names, which would make
the prefix right and the reading a misunderstanding of the transport.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
