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

### §RK1125 The section nobody names

RK1120 reads **lines**: `ids_since` parses two revisions of a carrier and answers which
ids gained or lost one. A prose file holds no lines, so it is covered by the other half
— a rationale file this task did not write is `loose`, named whole.

The gap is the file this task *did* write. One `section amend §RK-A` earlier in the
session puts this id in `docs/IMPROVEMENTS.md`'s diff, so the file is accounted; another
session's new `### §RK-B` inside it then rides into the staging with nothing said, which
is exactly the state RK1117 was filed about and RK1120 closed for the roadmap:

```
$ roadkeep section amend RK-A --body-file …     # this id is now in the file's diff
$ roadkeep ship RK-A --why "…"
  stage    git add -- … docs/IMPROVEMENTS.md
                                               # §RK-B is in there, and nothing names it
```

`sections.anchored` is the reader that makes it decidable, and it is already used
against a revision one command over: `lint --since` parses the file as it was so a
removed section is attributed to the section that held it (RK36). So the question is the
same comparison with a different unit — anchors instead of ids — over `PROSE_ROLES`
instead of `CARRIERS`.

What is worth deciding rather than copying is the *unit reported*. An anchor is not an
id under an outline scheme, and the ids a `§XVI.12 A design (SH123)` heading names live
in its title — which `Section.names` already reads, and which is what makes the sentence
say "somebody else's design" rather than an address the reader has to resolve
themselves.

## Block C — Query

### §RK1124 The revision resolved once per file

`ids_since` asks `resolves` before it reads anything, which is right — the two silences
`content_at` returns are what made a whole backlog read as newly arrived — and it asks
it once per **carrier**, because `sharing` loops over the roles. Resolving `HEAD` is a
fact about the repository and not about a file, so every call after the first is a
subprocess for an answer already in hand.

Measured on this repository, which declares two of the three carriers:

```
resolves alone   20.6ms
ids_since x3     85.6ms      (two carriers reached; the third is not declared)
```

RK176 set the floor this spends from at **43ms** for a whole session-start read, and
`stale` was written to cost 0.86ms of it. `claim <id>` now pays the figure above on
every call — and it is a read an agent runs before every commit, so it is the one place
in this mechanism where a subprocess per role is a habit rather than an answer.

The fix is a parameter and not a cache: `resolves` once in `sharing`, its answer passed
down, which is the shape `plan(gauging=…)` already uses for the one expensive question a
caller may decline. A cache keyed on a revision would be a second reader of git state
with its own staleness, in a module whose whole rule is that nothing is stored.

`--porcelain` already pays none of this — it prints the paths and returns before the
split — so what is measured here is the two answering forms, which are the ones a person
reads.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
