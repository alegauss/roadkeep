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

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

### §RK75 The heading word is a convention

`_BLOCK_LABEL_RE` in `document.py` is `^Block (?P<label>…)`, and `_BLOCK_DEP_RE` in
`schema.py` spells the dep the same way. That is right for the two corpora the format
was read off and wrong for every other one measured: Dumont files all 34 shipped entries
under `## Track A — …`, Turing writes 22 sub-blocks as bare `## D.1 — …`, and cursarei
numbers `## Fase 0 — Higienização`. Three of four adopting projects, and each one gets a
finding per line for using its own vocabulary.

By L6 that settles it: a word a project chose is configuration, not format. What must
stay a fact is the *shape* — a heading declares one label, a task names one heading, and
a dep on a heading resolves against the same list — because that is what `pick`, `stats`
and every block dep are over.

So `[headings] word = "Track"`, defaulting to `Block` so nothing changes for a project
that never declares it, and read by the parser and the dep grammar from one place. A
project whose sub-blocks carry no word at all is the harder half and is not this: `##
D.1` would need the word to be optional, which makes every `## Objetivo` a block. That
is a second decision and belongs to whoever takes it, not to the key that fixes three
files.

### §RK76 An estimate that is not the gate

`adopt` builds its schema as `config.schema.as_ledger() if ledger else config.schema`,
which is the one place in the codebase that reaches past `Config.schema_for(role)`. So
`[limits.changelog]` and `[rules.changelog]` — the two tables a project writes precisely
*because* its ledger is history — are invisible to the estimate, and the number it prints
is the number under the shared limits.

Measured on Dumont: `adopt --ledger` reported 34 `why.no-terminator` against a config
that declares `terminator = false`, while `lint` on the same file reported none. The
command whose whole purpose is "take the measurement before the commitment" was
reporting a commitment nobody was being asked to make.

The fix is that `adopt` asks the same question every other command does, which also
settles what `--ledger` means: not "apply the ledger schema" but "read this file in the
changelog role". A path is not a role — the caller names a file the project may not have
declared — so the flag stays, and only what it resolves to changes.

## Block F — The plugin
