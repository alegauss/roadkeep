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

### §RK77 The corpus no configuration reaches

Shio and Turing adopted because their lines already *were* this format under other
numbers; Dumont adopted because its roadmap was empty. cursarei is the case none of that
covers, and it is the honest test of L6: four gaps, each needing a different key, none
fixable together.

**The marker holds a space.** Its lines are `- [ ] **C40** · …`, and the parser reads the
first whitespace-delimited token — which is `[`, never `[ ]`. Declaring the checkbox in
`[markers]` does nothing, so all 16 open lines are invisible rather than rejected.

**The heading has no label.** Five read `## Fase 0 — …` and five `## Trilha contínua — …`.
RK75's configurable word does not reach this: the five Trilhas share both words, so there is
no label to be the block, and what tells them apart is prose.

**The separator is `·`.** Twelve lines split symptom from why with a middle dot where the
render writes an em dash — and by L3 a line that does not round-trip is one the tool refuses
to write the whole file for.

**The ledger is keyed by release.** `## Não lançado` over `#### NEW FEATURES` over
`* **Título (C26)** — …`, the id inside the bold title. Nine of twelve entries carry it
where nothing looks.

So the answer is not a `roadkeep.toml` here. A config whose every read is zero claims a
governance it does not have, which is the drift this tool exists to refuse.

### §RK98 The estimate that cannot tell a table from an empty file

`adopt docs/ROADMAP.md --prefix T` on commitclerk answered `read 0 line(s), 0 conform, 0
would change` and then listed nine blocks. Both halves are true and together they are
misleading: the headings parsed, the 45 tasks under them did not, because each is a row
in a `| ID | Status | Task | Depends on |` table rather than a bullet. The number that
decides whether to adopt was the number a project with an empty roadmap gets.

The estimate is the one command whose whole job is to be read *before* the commitment,
so a zero it cannot explain is the failure mode it exists to prevent. It already reports
`rejects` for a marker-bearing bullet the grammar refused; a row is the same category
one shape further out — a line that is plainly a task and plainly not this format.
Counting the pipe-delimited rows under a block heading and naming them (`45 line(s) in a
table this format does not read`) costs no new grammar and turns "nothing to do" into
"here is the conversion".

Deliberately not a table parser. Reading the shape is an estimate's job; writing it is
not, and a tool that adopted the table would be a tool with two line formats, which is
the rule L3 exists to keep singular.

### §RK99 The half of the corpus the estimate does not read

`adopt` measures a backlog: the longest symptom, the longest why, the longest rendered
line, each against its limit. A project adopting the tool has to declare
`limits.section` and `limits.prose` in the same file, and about those the estimate says
nothing — so setting them means either copying this repository's numbers, which is the
template argument L6 refuses, or writing a script.

Adopting commitclerk was the second: a fifteen-line script split the file on headings
and counted words, found 226 as the longest section, and `section = 250` followed from
that. The command that already parses headings, already knows the two ref schemes and
already reports a longest-against-limit could have answered it — `adopt
docs/IMPROVEMENTS.md --sections`, or the same run reading the prose file the config
names once one exists.

The measurement matters more here than on a task line, not less. A line over its limit
is one refusal at insertion; a rationale file with no budget at all is the 539 KB
failure this tool was built after, and the number that would have caught it is the
number an adopting project currently guesses.

## Block F — The plugin
