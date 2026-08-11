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

### §RK1034 One overage, two doors

RK1033 gave `section amend` the ancestor check and gave it `add`'s sentence with it:

> `§IX would be 39 words, limit is 30 with this section under it: delete 9 words — a
> subsection is charged to the address that owns it, so this prose belongs at a free
> top-level anchor (`anchors --next`) rather than under §IX`

The arithmetic is right and the advice is another door's. At an `add` the address has
not been chosen yet, so "put it somewhere else" is one flag away. At an `amend` the
section is already at that address, the prose the caller is holding is a *replacement*
for prose that is there, and `anchors --next` opens nothing: taking the subtree
elsewhere is `section move`, which is a different act with different consequences for
every pointer at it.

What the caller can actually do is two things, and neither is named: shorten this body,
or shorten the parent's own prose — the second being the one that is invisible from
here, because the overage is `§IX`'s and the paragraph in front of them is `§IX.1`'s.

**The shape.** One rule, two sentences, chosen by which door raised it — the same split
`_one_body` and `_one_pipe` already make about which caller is being answered. The
overage stays identical, because it is the same number; what changes is the list of ways
out, which is what RK421 calls the remedy and what L1 says a refusal is for.

What proves it: the two doors say different second halves, both name doors that exist,
and the arithmetic is one function.

## Block C — Query

### §RK1035 The number the row did not state

RK1029 gave `budget` the ancestor row, and phrased it for the read it was filed from —
an address nobody has written yet. On a **written** anchor it answers a question the
caller is not asking:

> `body       30 words, 5 written, 25 left  aim 23 more words`
> `under      §IX spends 19 of 30, so 11 is what an `add` here accepts`

The verb is wrong — there is no `add` here, the section exists and an `amend` is what
follows — and neither number is the one that binds. `§IX` spends 19 *including* this
child's 5, so a replacement body may be 16 words: `30 - (19 - 5)`. The reader is handed
two figures and the subtraction between them.

That subtraction is the whole thing this door exists to remove. *The saving is the
analysis*, and a budget that states two numbers and leaves the third to arithmetic has
kept the analysis and moved it.

**What it should say** is the number an `amend` may write, derived the same way the
refusal derives it: the ancestor's total, less what this section currently contributes
to it, against the limit. The unwritten case is unchanged — there the contribution is
zero and the row already reads correctly, which is why this was not visible when it
landed.

What proves it: a written child is answered with what a replacement body may say, the
unwritten one answers exactly what it answers now, and the figure matches what `section
amend` accepts on the next call.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
