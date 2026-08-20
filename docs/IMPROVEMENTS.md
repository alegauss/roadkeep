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

### §RK1265 The positive twin of a non-goal

`non-goal` is the one durable statement this tool has: addressed by its lead, no marker,
no dep, no pointer — *a constraint has no status to state* — and printed where a
proposal would otherwise repeat it. It is also the only one, and it is negative. Nothing
says what must be **true** for a block to be finished.

Measured in a repository using this tool: a block with **131 recorded entries**,
declared closed and reopened **six times**, every close a line count reaching zero. Its
definition of done *was* written — as a rationale section on the task that introduced it
— and `ship` deleted it, correctly, because `IMPROVEMENTS` holds rationale for unshipped
work. Zero occurrences today; what survived is one implementation sentence, and the
criterion moved to a file this tool does not govern.

RK1180 covers the lifecycle half: a standing block is *caught up* rather than finished.
This is the other half — a standing block still cannot say what would finish it, and a
block that is not standing closes on emptiness.

So: the same shape as a non-goal, mirrored. One list per block, addressed by its lead,
written by its own door, printed by `brief` for that block, and untouched by `ship`.

The scope caution is the design risk — it must stay a list of leads, not a document
store. A criterion that needs a page belongs in the project's own docs; what belongs
here is the line a `close` can read.

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK1264 The opt-in only a fresh project can take

`init --deferred` writes the deferred store and its `[files]` key together (RK1259),
which closes the case for a project being created. The project that met the defect was
not one: its configuration existed, so `init` answers `AlreadyConfigured` and the remedy
there is still the toml key and the skeleton by hand.

That is not special to this role. `[files]` is written once, by the one command that
refuses to run twice, so every role a project declines at scaffold time — strategy as
much as deferred — is one it retrofits by editing configuration the tool otherwise owns.
`adopt` reads and estimates and writes no config by design (RK1040); `install` wires
surfaces, not roles. There is no third door.

It also blocks the cheaper half of RK1259's own design. `brief` and `pick` were to say a
line cannot be paused before anyone tries, and they can — but a project with no store
cannot act on that sentence, so the row is permanent and unsilenceable at a project
doing nothing wrong. A notice whose only remedy is a hand edit is one a reader learns to
skip, which is worse than the refusal it was meant to arrive before.

What is missing is one write: declare a role, create its file with the block headings
the other files already carry, refuse where the key is already declared. `block add` is
the shape — a declaration in every file that takes one, or none.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
