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

### §RK437 The width RK430 could not reach

`[limits] prose` is the column a written paragraph is filled to, and it is the one
character figure RK430 left counting code points. The reason is mechanical:
`textwrap.fill` measures in code points and has no other mode, so agreeing would mean
writing a wrapper and re-flowing every paragraph this tool has already written.

The exposure is small and real. Nothing lints a wrapped width, so no build reddens; what
happens instead is that `adopt` reports a paragraph as within the width while a
line-length check on the consumer's side reports it over — measured here, one paragraph
of this repository's own improvements file is 87 code points and 90 units against a
declared 88.

Two honest answers. Either wrap in units, which is a small wrapper and a one-off re-flow
of files that then stop moving; or declare `prose` as a code-point width in
`roadkeep.toml`'s own vocabulary, so the table stops implying one unit for all of it.

### §RK438 Two meanings of empty, one of them offering a drop

Every write prints `event <id> Block <x> open|empty`, and `empty` there means the
roadmap holds no line under the label — the single moment a heading becomes droppable,
which is why RK408 attached the `block drop` offer to it.

RK429 then gave `empty` a second meaning: a block nothing has *ever* filed anything
under, as opposed to `finished`. The two now disagree out loud. Shipping the last line
of Block C in this repository printed `Block C empty` beside an offer to withdraw the
heading, while `pick --block C` answered `Block C is finished: the ledger records 12
filed under it` — and the heading is one of the six this project's plan is made of.

The offer is not wrong, but the word is. What a reader needs is which of the two facts
they have: this file has no line left under the heading, and the block itself is
finished, paused, or was never filled. The state is already computed; the event does not
ask for it.

## Block C — Query

## Block D — The gate

### §RK439 The heading inside the region is not a second address for it

Shio's ledger nests eight `### Block K follow-ups` sub-headings under their own `##
Block K` parent, and `declaring` counts every heading whose label matches whatever its
level, so each one is read as a second declaration of K. `lint` fires `block.repeated`
at all eight, every write through `place` refuses, and `ship` cannot file into the block
at all — two field captures from that project are this one refusal, hit twice.

Neither remedy the finding names fits the shape. `block drop` wants a region holding
nothing and these hold entries; `block merge` folds the sub-headings away, deleting an
organisation the author chose. The third road, renaming so only the `##` declares the
label, was measured there: 91 entries moved to `block.missing` and the rename was
reverted.

That measurement is the argument the rule is missing. RK391 refuses two headings that
are two addresses for one label — the state where a write cannot know which region it
files under. A heading *inside* another heading's subtree is not that state: its
position already says which region owns it, so the entries beneath it are the parent's
and the ambiguity never arises. The distinction is one `subtree_end` already draws, and
`declaring` is where both ends read it, so it is one expression and not a special case
per caller.

Open: whether a nested heading may name a *different* label than the one whose subtree
it sits in, which is a genuine second address and should stay refused.

## Block E — Adoption

## Block F — The plugin
