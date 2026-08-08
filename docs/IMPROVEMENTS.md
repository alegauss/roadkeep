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

### §RK385 Nothing notices that a new line asks for what a shipped entry already delivered

RK340 shipped on 2026-08-05: "outline anchors are one namespace across prose roles". On
2026-08-06 RK378 was filed asking for a per-role anchor namespace. `add` accepted it,
`lint` passed it, `pick` offered it, and the duplication surfaced only when a worker
claimed the line and went looking for the code. RK382 repeated it a day later against
RK178.

A lexical match at write time, above a declared threshold, was the mechanism proposed
here. This ledger labels four supersessions and two survive in history as filed;
measured against those, it **does not separate them**. Over the symptom alone RK340
places 9th of 382. Over symptom and `why`, RK378 → RK340 ranks 1st at 0.277 while RK382
→ RK178 ranks **33rd** at 0.125 — against a median 0.208 for an ordinary line's nearest
*non*-duplicate, so the true match scores below the typical false positive. Narrowing to
rare tokens moves the two ranks apart and lifts neither. An alphabet of identifiers is
emptier still: 192 of 382 entries name none.

The reason is in the pair. RK382 and RK178 state one problem in disjoint vocabularies,
which is what a problem discovered twice looks like — recognising it takes meaning, and
L4 has no model.

So the threshold is the wrong instrument and the symptom stands. What is untried is
exactness rather than similarity: a read the author is told to make before proposing, on
`non-goal list`'s precedent, where the tool states what a block already delivered
instead of guessing which entry is yours.

### §RK400 Name the parent a ship just emptied

`ship` deletes the task's own `§<id>` section and already names any section whose prose
cited what it deleted. Under an outline it leaves one thing standing that nothing names:
the **parent** the deleted children hung under. That paragraph was written as an
introduction to them — it states the problem they solve, in the present tense, often
under a banner about what is or is not worth building.

Shipping the last of `§X.1`–`§X.4` therefore leaves `§X` telling a reader the work is
open, sometimes that it is on hold, and always describing a defect the ship just
removed. It is the first thing anyone reads about that family and the only part of it a
ship never touches.

The fix is one line in the ship's answer, alongside the citation one: *"§X now has no
subsections — its prose introduces work that shipped"*. Deciding what it should say
instead is a `section amend`, and a judgement; noticing is not.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin
