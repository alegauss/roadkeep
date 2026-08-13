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

### §RK1149 The refusal that knows the answer (RK1145)

`lint` findings carry a `remedy.doors` array: the tool to call, the arguments, and
whether it writes. `add` refuses with prose alone — and its two most common refusals
have *already done the work*:

    ref: every task points at its rationale section — Block L's prose is under §XII,
    where §XII.17 is free (`anchors` with block: L lists it)

    §XXIII.7 was declared before (e210585) and its section is gone … §XXIII.10 is the
    next one nothing ever used

Both know the answer. Both hand it over as a sentence the caller must read, extract and
retype into an otherwise identical call. Measured in one session against Shio, a project
on the outline scheme: seven tasks filed, five of them refused first for exactly this,
five retries carrying no new information. The second refusal is worse than the first,
because the anchor it forbids is one `anchors` would have offered and the caller had no
way to know it was burnt.

The fix is the mechanism this tool already has, not a new one: attach a door to these
refusals the way `lint` attaches one, complete and pre-filled, so the retry is a call
rather than a transcription.

Auto-assigning instead was considered and is the wrong half. A ref is an address other
lines cite, and choosing it silently is how a task ends up pointing somewhere its author
never read — the refusal is right, its ergonomics are not.

## Block C — Query

## Block D — The gate

### §RK1148 A skip that makes a historical claim can be held to it

A skip reason is prose an author writes once, and three of the five RK1144 catalogued
make a **historical** claim — the shape *used to* be here. Measured against the
revisions those pins replaced, three of them are false:

```
shio: no adoption cost left to estimate    → 0 codes at b9302e8e too
shio: no line left to disagree with        → 0 offenders at b9302e8e too
turing: no fourth level with a letter any more → 0 lettered at f08304fcb1 too
```

Two are true: Shio's block dep was there at `b9302e8e` (RK1145 froze it) and T354
pointed at a doubled anchor before it shipped. So the suite says *a shape left this
tree* on three states that had already left, or never existed under that reading — and
RK1146 was filed, worked and shipped on the strength of one of them.

Both retired revisions still resolve. That makes the historical clause **checkable**: a
skip claiming a shape is gone can assert it was there at the pin before, and a false
claim goes red where today it reads as coverage.

What that costs is a second revision per corpus, and RK105's objection applies with its
sign reversed — a baseline is a pin nobody re-measures *on purpose*, because the state
it holds is what the claim is about and must not move.

The cheaper alternative, worth weighing rather than dismissing: forbid the clause. A
skip that says only what it read at this pin needs no second revision and cannot be
wrong — and loses exactly the information that motivated RK1145.

## Block E — Adoption

### §RK1150 A version skew wearing a typo's message (RK1150)

Reached from Shio, filing RK1149. The MCP server resolves roadkeep from the plugin cache
and the project resolves it from a checkout, so the two can differ. When they did:

    roadkeep: D:\...\roadkeep.toml: unknown key 'headings.permanent'
    (allowed: headings.word)

Every word true, and the conclusion it invites is wrong. `headings.permanent` is not a
typo and not somebody's invention — it is a key a *later* roadkeep added, read by a
binary that predates it. The message's own `allowed` list is the older schema, presented
as though it were the schema. The cheapest action it suggests is deleting a key the
project needs, and the second cheapest is editing a config that is already correct.

Nothing in the sentence can be used to reach the real answer, because the one fact that
separates the two readings — which roadkeep is running — is absent. The tool prints its
version in the MCP handshake and in `--version`, and not in the refusal that needs it.

So: name the running version in every config refusal, and where a key is unknown say
which of the two states it is. A key no version has ever declared is a typo; a key this
version does not have is an upgrade. They are different findings and they currently
share a message.

Cheap, and it is the first thing a reader needs on a machine where two copies are
installed.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
