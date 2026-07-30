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

### §0.4 The limits, measured against a live corpus (RK20)

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the other
89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the control,
and it shows compliance is available. The difference is that "what does not work" is one
clause by construction and a `why` has no natural end, which is L1 stated as a
measurement: the field whose scope is unbounded is the one that needs the bound at the
write path.

And the migration is smaller than §RK20 assumed. **74 of the 78 pointers resolve, and none
dangle**; 67 of the 70 over-length lines point at a section that already exists and already
makes the same argument — compared line-against-section on SH295 and SH309, the `why` is a
recompression of the paragraph, same examples and all. The rationale is not homeless. The
line is a second copy of it, so the edit is compression against a text that is already
written, not authorship.

## Block A — The model

### §RK47 A lettered subsection escapes the anchor

Found while shipping RK44 and not fixed by it: with the sigil no longer required on an
outline heading, Turing's `IMPROVEMENTS.md` reads 111 sections out of 147 headings, and
23 of the 36 misses are headings that *are* numbered. Twenty of those spell a fourth
level with a letter — `VII.2.a HTTP auth chainable helpers (T39)`, `IX.3.c Workspace SSE
bus (T113)` — which `OUTLINE_ANCHOR_RE` refuses because it admits only digits after the
first dot. Shio has none, which is why RK44's own measurement came out clean.

Two consequences, and the second is the one that matters. A pointer `→ §VII.2.a` is
already a `ref.format` violation, so the two ends of the pointer agree today only
because Turing happens never to write one. And the twenty headings are invisible to both
directions of RK15: not orphans, not sections, and the word budget that charges a
rationale per section does not charge them at all — prose that escapes the count by
gaining a heading, which is the drift the budget exists to stop.

So the pattern is widened at both ends or at neither. The open question is what a
segment may be: a single letter covers every case measured here, while a general
alphanumeric segment would also admit `VII.2.beta`, which no corpus writes and which
makes `§VII.2` ambiguous against a title beginning with a word. Measure before choosing
— the range heading `III.2–III.5` is a separate shape again, and naming one anchor is
not what it does.

## Block B — Authoring

### §RK45 Where a section with no task belongs

`_where` returns `len(document.lines)` for a section whose anchor names no task, and the
docstring one paragraph above it explains why that is wrong for the neighbouring case: a
Block A section appended after Block F's "reads as Block F's, which is the same mistake
`add` refuses one file over". The preface sections are exactly that case. Writing §0.4
with `section add` put it after §RK26, under `## Block F — The plugin`, where the only
signal that it is not Block F's rationale is the anchor itself.

An outline anchor already states its place: §0.4 follows §0.3, and §RK34.1 belongs
inside §RK34. So the position is derivable from the anchor rather than a fallback — find
the longest anchored prefix and file after its subtree, and refuse when there is none,
which is the same refusal `_where` already makes for an undeclared block. Appending is
the one answer that is always plausible and frequently wrong.

## Block C — Query

## Block D — The gate

### §RK46 A path a roadmap names does not exist yet

Measured on Shio: 8 `path.missing` findings, 8 of them false.
`blueprints/*/files/package.json` is a glob, `monaco-editor/esm/vs/…` is elided,
`@graphiql/react` is an npm package, and `openviglet/bootstrap-site` is a repository
slug; `template/widget/<name>.html` carries a placeholder; `target/` is a build
directory; and `import/post-types.json` is the file its task exists to create. Not one
is a claim that a file should be there and is not.

The category error is the file being read. A roadmap describes work that has **not
happened**, so the paths in it are disproportionately the ones that cannot resolve yet —
naming the artefact you intend to write is what a task line is for. A changelog is the
opposite: it describes work that shipped, so a path it names and the repository lacks is
a real defect and worth exit 1.

So the check moves to the ledger, and the extractor learns what is not a path claim at
all: a token holding `*`, `…`, `<`, or a leading `@`. What remains for the roadmap is
nothing — which is the right amount, because there is no defect there to find.

## Block E — Adoption

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
