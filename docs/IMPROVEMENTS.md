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

## §I — The model

### §I.1 A schema over the task line (RK1)

Six fields: `id`, `status`, `block`, `deps`, `symptom`, `why`, `ref`. Limits are the
P90 of the lines that already read well — `symptom` 120, `why` 200, rendered line 320
characters. Two rules are not lengths and matter as much: `symptom` states **what does
not work** (never a solution name, because a line named after its fix cannot be
falsified), and `why` is **one sentence** — a second sentence is the signal that the
content belongs in this file instead.

### §I.2 Round-trip as the ownership test (RK2)

The tool edits files a human also edits, so it must reproduce what it read
byte-for-byte before it is allowed to write. Parse → render → compare, over a corpus
of real files, as a property test. If round-trip fails on a line, the tool refuses to
rewrite that file rather than normalizing it silently — L3 exists because a formatter
that "fixes" what it misunderstood destroys work no diff review will catch.

### §I.3 `roadkeep.toml` (RK3)

Prefix (`SH`, `RK`, `TU`), the file paths, the marker set, per-field limits, and which
of the four files exist. Turing has a `STRATEGY.md`; Shio does not; Cursarei keeps its
roadmap under `docs/roadmap/`. All three are configurations of one format, and the
moment any of that is hardcoded the tool serves exactly one repository.

### §I.4 Deriving the next id (RK4)

Real backlogs are non-contiguous — epics own sub-ranges, superseded ids are retired
and never reused — so the next id is the max across **every** configured file plus any
declared extras, never inferred from a block's header range. A counter file would be a
second source of truth that drifts; the maximum is derivable, so derive it.

## §II — Authoring

### §II.1 `add` (RK5)

Takes the fields, validates against the schema, renders the canonical line, inserts it
under its block. Refusal messages carry the limit, the actual length, and the
suggestion to move the remainder to the improvements file — an error that teaches is
the difference between a guardrail and an obstacle.

### §II.2 `ship` (RK6)

Shipping is four coordinated edits across three files, which is why one is always
missed: move the entry to the changelog under its block, delete the improvements
section, replace the roadmap line with nothing or a single pointer, and update
dependents' dep markers. One command, one transaction, or the files disagree.

### §II.3 `status` (RK7)

A marker lives in exactly one file. `status` writes it in the roadmap and fails if a
sibling carries one, because two files that both express status will eventually
express different status, and there is no way to tell which is right.

### §II.4 Derived dep markers (RK8)

`(deps: RK1 ✅)` is a cache of another line's status, and a stale cache here makes a
ready task read as blocked. Derive the markers on every write from the actual status
of the referenced ids; a dep pointing at an unknown id is a lint error, not a rendering
choice.

### §II.5 Sections, not lines (RK9)

Improvements and strategy are prose under headings, so their unit is a section with a
word budget and a required anchor, not a bullet with a character cap. `section
add|show|drop` governs them, and `drop` is what rule 1 of the ship flow calls.

## §III — Query

### §III.1 `list`, `stats`, `audit` (RK10)

Counting by grep drops what it fails to match, and reports the remainder with no
indication that anything is missing — an empty count reads identically to a clean
file. So `audit` is not an extra: it prints every marker-bearing line the counter did
**not** count, with the reason, which is the only way a count can be trusted. `--json`
for anything programmatic.

### §III.2 `pick` (RK11)

The most common question asked of a roadmap — "what do I work on" — currently costs
reading the entire file. `pick` applies the declared priority queue, then the lowest
id whose deps are all shipped, and prints the reason it chose that task so the answer
is auditable rather than oracular.

### §III.3 `show` (RK12)

A task is a line in one file, a rationale section in another, and sometimes a spec on
disk. `show` joins them, which is what a maintainer does by hand today at the cost of
loading two files to read forty lines.

### §III.4 `deps` (RK13)

A blocked task and a ready one are visually identical, so the graph has to be
resolved: blocker chains, transitive readiness, and cycles. A cycle is a defect in the
backlog and should fail `lint`, not merely print.

## §IV — The gate

### §IV.1 `lint` (RK14)

Validates every line against the schema and **exits non-zero** — that exit code is the
entire difference between a gate and advice. It is also the tool's own conformance
fixture: `roadkeep lint` must pass on this repository's files, so the format is proven
by the artefact rather than asserted in a README.

### §IV.2 Resolving pointers (RK15)

A `→ §x.y` aimed at a section that does not exist reads exactly like a design that
does, which is worse than no pointer — it makes a reader stop looking. Resolve every
pointer against the improvements file and every spec path against disk.

### §IV.3 `--fix` (RK16)

A first run against a real backlog reports dozens of violations, and a report that
large gets ignored wholesale. So separate the mechanical (ordering, dep markers,
whitespace, marker spacing) from the editorial (an over-long `why`) and auto-apply the
first, leaving a list short enough to act on.

### §IV.4 One exit code, three surfaces (RK17)

A GitHub Action, a pre-commit hook, and the plugin's `Stop` hook all call the same
command. A gate that runs in only one of the three is a gate with a documented bypass.

## §V — Adoption

### §V.1 `init` and `adopt` (RK18)

The repositories that need this most already have backlogs, so requiring an empty repo
would exclude every real user. `init` scaffolds files and config; `adopt` runs the
schema over an existing backlog and reports what would have to change — a migration
estimate before a migration commitment.

### §V.2 PyPI (RK19)

Distribution decides whether this is a standard or a script in one repository.
`uvx roadkeep` with no checkout is the bar. Publish after Block D, because a published
`0.1.0` whose format still moves is worse than an unpublished one.

### §V.3 Shio as the first real corpus (RK20)

Shio's 92 lines are the test of whether the limits are right: if a meaningful fraction
cannot be expressed within them, the schema is wrong and not the lines. Migrating is
also how the six worst offenders finally get their rationale moved to where it belongs.

### §V.4 Rollout (RK21)

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

## §VI — The plugin

### §VI.1 Deny the hand-edit (RK22)

With Markdown as the store, an agent can bypass the entire schema with one `Edit` call
— and will, because `Edit` is cheaper than learning a CLI. A `PreToolUse` hook that
denies `Edit`/`Write` on the governed paths and returns the command to call instead is
the only enforcement point an agent cannot route around, and it is what makes L1 true
rather than aspirational. Pair it with a `Stop` hook running `lint`, so a bypass via
`Bash` is caught before the turn ends.

### §VI.2 A skill, not a preamble (RK23)

Format rules pasted into a project's always-loaded instructions cost tokens on every
turn including the turns that touch no roadmap — the exact failure that made
`agents.md` 186 KB. A skill with trigger phrases loads the rules when a governed file
is in play and costs nothing otherwise.

### §VI.3 MCP tools (RK24)

A CLI invoked through `Bash` puts the field names in prose, where they get guessed and
mistyped. Exposing `add`/`ship`/`pick`/`lint` as MCP tools makes the schema the tool's
input schema — the arguments are validated by the protocol, and a wrong name is
refused with the allowed set instead of a usage string.

### §VI.4 Slash commands (RK25)

`/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick`, `/roadkeep:lint` — the same engine,
driven by a human who should not have to learn flag order to file a task.

### §VI.5 Marketplace (RK26)

A `marketplace.json` so `/plugin install` reaches it, following the layout Shio already
publishes from (`.claude-plugin/marketplace.json` + a plugin directory).
