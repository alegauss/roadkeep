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

### §RK434 One rule, two readers, and the second one predates the first

`_dead_block` was where this project first worked out that a block with nothing open is
three different facts: `priority.block` for a label nothing declares,
`priority.block-empty` for one the ledger files entries under, and
`priority.block-unstarted` for a heading written before its lines. RK429 then wrote that
same walk as `Backlog.standing`, because `brief`, `pick` and `list` needed it too.

Both are correct today, which is exactly the state that does not last. They already
disagree in one place: RK429 added a fourth state for a block whose lines were all
deferred, and the gate has no such answer — a queue entry naming a paused block is
reported as one nothing has been added to yet.

The gate keeps its own codes and its own remedies; what should move is the
classification under them. This project's whole discipline is that one rule has one
reader, and a rule spelled twice is the drift it exists to refuse.

### §RK435 A remedy that states the other code's condition

Three codes share one shape and their remedies were written together. `priority.block`
is the label nothing declares; `priority.block-empty` is the one whose every line has
shipped; `priority.block-unstarted` is the heading written before its lines — the note
says so itself, `queues Block X, which no line is filed under yet`.

Its remedy reads: *the block was never declared, so the token addresses nothing*. That
is `priority.block`'s condition, and the finding it is printed under has already
established the opposite. RK420 made every finding name the command that closes it
precisely so a reader would not have to work one out; a reason that contradicts the line
above it is worse than none, because it is the half a reader trusts.

Whether `priority drop` is even the right door here is the second question: a block
whose lines are coming is a queue entry that will start firing, and dropping it is the
one move that guarantees it never does.

## Block E — Adoption

## Block F — The plugin

### §RK436 The one counter this tool publishes and does not own

RK430 made every character limit a count of UTF-16 code units and said so on every
surface this tool prints. One surface it does not print: `serving` publishes `symptom`
and `why` as JSON Schema `maxLength`, and that keyword is defined over the string's
**characters** — code points. So the number is right and its unit is not.

The gap only opens on a field carrying an astral character, which a symptom rarely does
and a pasted emoji does immediately. Then a client validates locally, passes, calls the
tool and is refused by a number it was told it had met — the same shape as the Shio
ratchet, moved from a build to a round trip.

Three answers exist and none is obviously right: publish the stricter figure and lose
room on every ASCII field, describe the unit in the field's `description` and rely on it
being read, or leave it and name the residual where a client author would look.
