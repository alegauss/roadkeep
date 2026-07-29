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

## Block B — Authoring

### §RK8 Derived dep markers

`(deps: RK1 ✅)` is a cache of another line's status, and a stale cache here makes a
ready task read as blocked. Derive the markers on every write from the actual status
of the referenced ids; a dep pointing at an unknown id is a lint error, not a rendering
choice.

### §RK9 Sections, not lines

Improvements and strategy are prose under headings, so their unit is a section with a
word budget and a required anchor, not a bullet with a character cap. `section
add|show|drop` governs them, and `drop` is what rule 1 of the ship flow calls.

## Block C — Query

### §RK10 `list`, `stats`, `audit`

Counting by grep drops what it fails to match, and reports the remainder with no
indication that anything is missing — an empty count reads identically to a clean
file. So `audit` is not an extra: it prints every marker-bearing line the counter did
**not** count, with the reason, which is the only way a count can be trusted. `--json`
for anything programmatic.

### §RK11 `pick`

The most common question asked of a roadmap — "what do I work on" — currently costs
reading the entire file. `pick` applies the declared priority queue, then the lowest
id whose deps are all shipped, and prints the reason it chose that task so the answer
is auditable rather than oracular.

### §RK12 `show`

A task is a line in one file, a rationale section in another, and sometimes a spec on
disk. `show` joins them, which is what a maintainer does by hand today at the cost of
loading two files to read forty lines.

### §RK13 `deps`

A blocked task and a ready one are visually identical, so the graph has to be
resolved: blocker chains, transitive readiness, and cycles. A cycle is a defect in the
backlog and should fail `lint`, not merely print. Resolve the reverse direction too —
how many tasks shipping this one unblocks — because that count is the half of
prioritisation a tool may supply: leverage is derivable, value is not. Measured here,
RK14 unblocks 14 of 29 and RK10 unblocks 4, a gap no reading of the file makes visible.
The traversal belongs in tested code rather than rewritten per session: an ad-hoc one
is not merely expensive, it is wrong in ways nothing checks.

### §RK29 One call to start a task

Starting RK1 in this repository cost reading ROADMAP.md and IMPROVEMENTS.md end to end
— some 5k tokens to learn one task, of which one line and one paragraph mattered.
`pick` and `show` each answer half the question. The accelerator is one call that
returns the line, its rationale, its deps' resolved status, the non-goals that bind it
and the paths it will touch: bounded output is the point, because an answer that fits
in a tool result is an answer that costs nothing to consult twice.

### §RK32 A retired id is a decision with no record

Ids are non-contiguous by design and a retired one is never reused, so a gap is normal
— which is exactly what makes it unreadable. A line leaves the roadmap by three doors
and only one of them is recorded: **shipped** reaches the ledger, while **superseded**
by a later design and **abandoned** reach nothing at all. RK4 derives the maximum and
stops there, so nothing distinguishes a deliberate supersession from a botched
hand-edit. ADR practice keeps the record and marks it superseded instead of deleting
it; the half worth taking is the forward pointer, written at the moment the decision is
made, which leaves history to be consulted only for the gaps nobody recorded. Deleting
still beats keeping — an accreting rationale file is the 539 KB this project refuses —
so what survives a supersession is one line, never the design it replaced.
*Unresolvable* stays a valid answer: a squashed or shallow history holds no such
commit, and must print as unresolvable rather than as retired, on the reasoning of
RK28.

## Block D — The gate

### §RK14 `lint`

Validates every line against the schema and **exits non-zero** — that exit code is the
entire difference between a gate and advice. It is also the tool's own conformance
fixture: `roadkeep lint` must pass on this repository's files, so the format is proven
by the artefact rather than asserted in a README.

### §RK15 Resolving pointers

A `→ §RK<n>` aimed at a section that does not exist reads exactly like a design that
does, which is worse than no pointer — it makes a reader stop looking. Resolve every
pointer against the improvements file and every spec path against disk. Scan the
rendered `ref` field only, never the line: RK15's own `why` quotes the pointer as an
example, and a naive scan reports that quotation as a broken pointer.

### §RK16 `--fix`

A first run against a real backlog reports dozens of violations, and a report that
large gets ignored wholesale. So separate the mechanical (ordering, dep markers,
whitespace, marker spacing) from the editorial (an over-long `why`) and auto-apply the
first, leaving a list short enough to act on. Migrating between pointer schemes is
mechanical too, and RK27 had to do it with a throwaway script because this does not
exist yet.

### §RK17 One exit code, three surfaces

A GitHub Action, a pre-commit hook, and the plugin's `Stop` hook all call the same
command. A gate that runs in only one of the three is a gate with a documented bypass.

### §RK35 A dep can name more work than it looks like

Shio's `(deps: Block P)` is one token and resolves to forty-eight open tasks; Turing's
`(deps: T451–T457)` is one token and names seven. Both are legitimate (RK28) and both
mislead a reader counting deps to judge how blocked a task is, which is exactly the
judgement `pick` and a human both make from the line alone. The gate should say what a
collective dep expands to, because the cost of the abbreviation lands on whoever
believes it.

### §RK30 The context budget is a schema field

`agents.md` declares its own 150-line budget in prose, which is precisely the
arrangement that let Shio's reach 186 KB. A file loaded every turn spends the resource
this tool exists to protect, so its budget belongs in the configuration and its
overrun in the gate's exit code, alongside every other rule that turned out to need
enforcing rather than stating.

### §RK34 Name the byte, not its consequence

The format is structural Unicode — `—`, `→`, `§` and four emoji markers — so the
lookalikes a human editor produces are all invisible at the point of failure. Measured
against the parser: `📋` plus U+FE0F is refused as `status.unknown`, which prints as
"`📋️` is not one of `📋`"; a no-break space before the pointer is refused as
`why.no-terminator`, naming the one thing the line does not lack. Both diagnoses are
correct and unusable, because the character that caused them cannot be seen. Report the
codepoint and its offset instead, and treat a BOM and a CRLF as the same class — a byte
nobody typed, breaking a round-trip that compares bytes. `_looks_like_marker` already
takes this position for U+FE0F and U+200D (RK2); this extends it from *not skipping the
line in silence* to *saying what is actually wrong with it*.

### §RK36 A section may not promise what the line does not

RK15 refuses a pointer at a section that does not exist; nothing refuses the mirror, a
section that requires more than the line pointing at it. That direction is the more
expensive one, because the line is the single source of status and the section is
deleted on ship: a requirement written only into the rationale cannot be picked, cannot
be shipped, and disappears with the section that held it. It happened three times in
the session that added RK13, RK34 and RK32 — every time by an author who had just
learned something and wrote it where the reasoning was, not where the status is. The
check is not semantic and does not need to be: a commit that edits `### §RK<n>` without
touching RK<n>'s line is the whole signal, and history is already resolvable (RK31).

## Block E — Adoption

### §RK18 `init` and `adopt`

The repositories that need this most already have backlogs, so requiring an empty repo
would exclude every real user. `init` scaffolds files and config; `adopt` runs the
schema over an existing backlog and reports what would have to change — a migration
estimate before a migration commitment.

### §RK19 PyPI

Distribution decides whether this is a standard or a script in one repository.
`uvx roadkeep` with no checkout is the bar. Publish after Block D, because a published
`0.1.0` whose format still moves is worse than an unpublished one.

### §RK20 Shio as the first real corpus

Shio's 92 lines are the test of whether the limits are right: if a meaningful fraction
cannot be expressed within them, the schema is wrong and not the lines. Migrating is
also how the six worst offenders finally get their rationale moved to where it belongs.

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

## Block F — The plugin

### §RK22 Deny the hand-edit

With Markdown as the store, an agent can bypass the entire schema with one `Edit` call
— and will, because `Edit` is cheaper than learning a CLI. A `PreToolUse` hook that
denies `Edit`/`Write` on the governed paths and returns the command to call instead is
the only enforcement point an agent cannot route around, and it is what makes L1 true
rather than aspirational. Pair it with a `Stop` hook running `lint`, so a bypass via
`Bash` is caught before the turn ends.

### §RK23 A skill, not a preamble

Format rules pasted into a project's always-loaded instructions cost tokens on every
turn including the turns that touch no roadmap — the exact failure that made
`agents.md` 186 KB. A skill with trigger phrases loads the rules when a governed file
is in play and costs nothing otherwise.

### §RK24 MCP tools

A CLI invoked through `Bash` puts the field names in prose, where they get guessed and
mistyped. Exposing `add`/`ship`/`pick`/`lint` as MCP tools makes the schema the tool's
input schema — the arguments are validated by the protocol, and a wrong name is
refused with the allowed set instead of a usage string.

### §RK25 Slash commands

`/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick`, `/roadkeep:lint` — the same engine,
driven by a human who should not have to learn flag order to file a task.

### §RK26 Marketplace

A `marketplace.json` so `/plugin install` reaches it, following the layout Shio already
publishes from (`.claude-plugin/marketplace.json` + a plugin directory).
