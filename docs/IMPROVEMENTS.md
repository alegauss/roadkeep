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

### §RK1366 The remainder on a field the next write deletes

RK1365 found this in the shipping row and fixed it there: `Share.left` subtracts what a
field already holds, and `ship --why` is required and replaces that sentence, so the
room for it is the whole allowance. The same subtraction is still published one row
above, about the line itself.

`amend <id> --why` replaces the `why` exactly as a ship's does. Nothing extends it — the
field takes one sentence — so there is no write for which "what is left beside what is
written" is the number. On RK1365's own line the two readings were 55 characters and
200, and the word aims beside them 8 against 31: the figure an author composes to was a
quarter of the real one, which is the shape RK1365 argues is worse than publishing none.

What decides the boundary is `drafted`. Where the caller passed a draft, `taken` is that
prose and `left` is exactly the overrun the write is refused by, which is right and is
what RK1190 built the flag for. Where `taken` came off the file, it is prose the next
write deletes.

So the fix is narrow and two neighbours stay as they are: a section body's remainder is
real, `section amend --replace` editing prose in place rather than replacing it, and the
every-turn file's is real for the same reason.

Falsified when `budget <id>` reports a remainder that differs from the longest `--why`
the matching `amend` accepts.

## Block D — The gate

## Block E — Adoption

### §RK1367 Withdrawing an argument, where stacking one is the rule

`govern --because` stacks (RK1293): a raise is a decision about the previous decision,
and `[tools] session` carried five of them written that way by hand. That is right for
as long as each paragraph argues about the same question.

RK1364 is the other case. The eight above that key all measured three checkouts against
each other to prove the surface belonged to the package, and RK1360 removed the premise:
the ceiling is about one project, so those paragraphs argue for a reading nothing takes
any more. Fifty-six lines of them, and the only way to drop them was the hand edit
`declare` and `govern` exist so nobody makes.

So the shape is `block amend`'s, one file over: a field write-once in practice, whose
correction was a hand edit until a verb was given the words. Here the field is the
comment run `_because` already reads back, so the verb holds both halves — where the run
starts, and the replacement the caller composed.

What it must not become is a delete. An argument withdrawn in silence is history
removed, which is `record drop`'s own refusal, so the sentence replacing the run is the
caller's and says what was falsified, and the lines it displaced are named in the answer
for the commit to carry.

Falsified when a reading `govern` publishes stands under a comment arguing from a
premise that reading contradicts.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
