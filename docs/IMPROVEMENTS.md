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

### §RK78 ship deletes what it did not name

Observed on Shio at SH326. The rationale file nests: a level-2 section groups an epic
and each task keeps a level-3 section under it. `ship` deleted the level-2 by taking
everything up to the next level-2, which swallowed four level-3 children — two of them
the rationale of tasks that are still open, so the roadmap then pointed at sections that
no longer existed. 160 lines went in one transaction that reported dropping one section.

The gate caught it: `lint` reported two `ref.unresolved` immediately after. That is the
right instrument in the wrong order — it names the damage after the write rather than
refusing it, and the operator's only remedy was `git checkout` on the whole file, which
also discards the part of the ship that was correct.

Two things to settle. A drop has to be bounded by the next heading of **any** depth
greater-or-equal, not the same depth. And a transaction that would orphan a live pointer
should refuse before writing, the way `add` already validates every field first — the
reasoning `add` states for itself ("a limit reported after the prose exists is a limit
discovered too late") is the same reasoning, one verb along.

## Block C — Query

### §RK83 Ready is two different states

`pick --block P` answered with the lowest ready id and said so. The block held both
designed tasks and ideas, and the id it chose was an idea — a design session, not an
implementation. A caller who asked to execute a block wants the second kind, and had to
override the answer by hand on every iteration of a long run.

The markers already carry the distinction and the tiers do not read them. Whether that
is a new tier below the declared priority, or a flag, or only a sentence added to the
`because` line — "the pick still needs designing" — is the open question. The last is
the cheapest and may be enough: `pick` already explains which tier answered, and the
complaint is not that it chose wrongly but that it chose silently.

Worth noting what should not change: a block whose ideas are never offered is a block
whose ideas are never designed. The bias belongs to the caller's intent, not to the
tool's ranking, which argues for the flag over the tier.

## Block D — The gate

### §RK84 A gate on a corpus with standing debt

Adopting projects arrive with history. One live corpus lints at 317 problems, none of
which the current change caused, and the number moves by one or two per task. `lint`
exits non-zero on all of it, so on that repository the gate cannot be wired to CI, and
the question actually asked after every write — did I add anything — has no command.

It was answered by hand: stash the three files, run `lint`, unstash, run it again,
compare the two summary lines. That worked and it is not something a hook can do. It
also nearly hid a real defect: the count fell by eight on the run that deleted 160 lines
of rationale it should not have (RK78), and the drop looked like an improvement until
the two `ref.unresolved` entries were read individually.

`--since REV` exists and answers a different question (a rationale edited without its
line, RK36). What is missing is a baseline: the violations at a ref, subtracted from the
violations now, exiting non-zero only on the difference. That is also the shape that
lets a repository adopt the gate before it has paid off the debt.

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

## Block F — The plugin

### §RK89 Persist first, curate later

Evidence that exists for the length of one stdout depends on the caller taking a second
step, and RK86 is the record of second steps not being taken. So the capture is written
before it is printed: `.roadkeep/reports/` in the project where the failure happened,
one file per capture, unconditional.

This crosses a boundary worth naming. The tool owns four files in an adopting repository
and this is a fifth path — but it is a fifth path the repository never has to see,
because the same run appends it to `.gitignore` when no rule already covers it. Nothing
enters anybody's history, nothing appears in a diff, nothing has to be explained to a
reviewer who did not install this. The rules that keep that true: append one line, only
when absent, never reorder or rewrite what is there, and if the file cannot be written,
say so and keep the capture anyway. `.gitignore` is not governed and never round-trips,
so it is read to decide and appended to, never rendered.

Retention is deliberately unsolved. Rotation, dedup by argv, an age limit, a command
listing what was never sent — all of it is easier to add to a directory that already has
files in it than to reconstruct from sessions that ended. A capture nobody pruned costs
kilobytes; a capture nobody kept costs the only session that could identify the defect.
Sending is still nobody's default: what lands here is local, and RK87 governs everything
that leaves.
