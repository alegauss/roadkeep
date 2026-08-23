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

### §RK1311 One field, three surfaces that do not know it

Observed in pportal, 2026-08-22, attaching a requirement to five existing lines.

`amend --requires console` alone is refused: "nothing to amend: pass --why, --dep or
--ref". The flag is in the parser, is documented in the help two lines above the
message, and works - but the guard that decides whether anything was asked for does not
count it. So the only way to attach a requirement to a line that already exists is to
pass a field that is not changing, which for one of the five meant re-sending a `why`
that then failed the line limit because the annotation had made the line longer. Two
round trips for a field the verb has.

The confirmation is the second half. Passing `--requires` alongside an unchanged `--why`
answers "unchanged: every field already reads that way" - and writes the requirement
anyway. Both cannot be true, and the one that is printed is the one that would stop a
caller retrying. It was only visible because the roadmap line was read directly
afterwards.

`show` does not print requirements either. A line carrying `(requires: console)` shows
deps, marker, section and budget, and nothing about the thing it is actually waiting for
- which is the field a caller asks `show` about when `brief` stops offering the line.

Three surfaces, one field, and the field itself is right: requirements are exactly what
deps cannot express, and declaring them moved this project's queue from a task that
could not be started to one that could.

### §RK1312 A sentence the file wrapped is still that sentence

`section amend --replace` matches the bytes on disk, and the bytes on disk are reflowed.
A section is written to a prose width, so any sentence longer than that width is stored
with a newline and some indentation inside it - and a caller quoting the sentence, which
is how the prose reads to anybody looking at it, is refused for text the section plainly
carries.

Observed in pportal, 2026-08-22, twice in one task. Both times the fragment was a full
sentence copied from `section show`, which prints the prose as it is - so the command
the refusal recommends is the command that produces the text the refusal rejects. The
way through was to shorten the fragment until it happened to fit inside one stored line,
which is guesswork with a round trip attached.

It also makes `--replace` weaker than it looks. A short fragment is what fits, and a
short fragment is what "occurs exactly once" refuses - so the two rules push in opposite
directions, and the caller lands between them.

Matching against the prose with its wrapping collapsed would close it: the same
normalisation that writes the file, applied to the needle before looking. What comes
back out is rewrapped anyway, so nothing about the stored form has to change.

Worth saying that the refusal is good otherwise: it names the section, says the text is
not there, and points at `section show`. It is right about everything except that the
text IS there.

### §RK1316 The list the withdrawal left standing

Observed on a fresh tree, 2026-08-23: a criterion written under Block A, its one task
shipped, then `block drop A`. The heading goes from the roadmap and the improvements
file, the ledger keeps its own, and `## Done when — Block A` stays behind with its
bullets. `criterion list` then reports them under a label `block list` does not carry,
and `criterion add --block A` is refused `no block 'A'` — so what is left has no door
but `criterion drop`.

RK1265 is right that a block's list outlives its lines: an emptied one is a question
somebody answered and not one nobody asked, and RK1300 prints it at the ship that
finishes the block so the reading arrives when it is owed. Neither is about the label
itself leaving. RK1268 settled what happens then, one address over — a task's list goes
inside the transaction that removes the line, because there is no state where the
address has left and a heading still asks what would finish it.

So this is that rule at the block's own address. `drop_block` computes every file's edit
before touching anything, so the region joins the roadmap's entry in `changed` beside
the heading rather than arriving through a second write.

Two things it is not. Not a refusal: the block is empty by the time this verb can run,
and a list is not work filed under a heading. Not silent: the leads are named in the
answer, as a departure's already are.

### §RK1317 The address the renumbering did not move

Observed on a fresh tree, 2026-08-23: a criterion written with `--task`, then `renumber`
onto a free number. The line moves, its `§<id>` section moves with it, every dep naming
it moves, and `## Done when` keeps the number nobody carries any more.

RK1268 addresses a task's list by its id, and the id is what this verb spends.
Everything else bound to it already moves here: the pointer under `ref_scheme = "id"`,
the heading's trailing binding under an outline (RK1231), the dep annotations. The
criteria heading is the one address the write does not know about, and the one added
last.

So it is re-addressed and never removed, which is where this differs from RK1316 and
from the departures. A renumbering is not a departure: the work is open, the list is
what finishes it, and deleting it would spend the one thing a collision repair exists to
preserve. The heading is rewritten through `criteria.heading_for`; the bullets are
untouched.

Refused before anything lands, as the rest of this verb is. A `Done when` heading
already at the destination is two lists under one address, which is the state `criterion
add` refuses one call at a time. And reported beside the section, because a heading this
write moved is one the author has to be told about.

## Block C — Query

### §RK1314 The sentence that rode along with the key set

`roadkeep config` prints, under `[criteria]`, the sentence "`[non_goals]` - the two
fields the roadmap's other bullet has (RK70)". That is the other table's docstring, and
it names the other table.

One value reader is right, and RK1265 argued it: `[criteria]` is the same two numbers
about the positive twin, so `_scope` takes the table name and only the problems it
reports differ - two copies would be two opt-ins that came to accept different shapes.
What followed the docstring across is not that. `describing` maps both addresses to
`_SCOPE_KEYS`, so the sentence rides along with the key set.

It matters because of what this read is for. `config` exists so a key is written from
what the build accepts rather than from memory, and the sentence beside each row is the
package's own words about that key, which is the whole reason nothing on that surface is
a second copy of a rule. A row whose words describe a different table is worse than a
row with none: nothing in it disagrees with itself, the two tables carry the same two
key names, and the reader has no way to tell it from a correct row.

The fix is a sentence about criteria taken from where that table is documented, read per
table rather than per key set.

## Block D — The gate

### §RK1318 The address the gate never re-asks

Observed on a fresh tree, 2026-08-23. Two states reach it: `block drop` withdrawing a
label whose list stays (RK1316), and `renumber` spending the id a list is addressed to
(RK1317). `lint` calls both trees clean.

`_criteria` checks what a schema can check — shape, the two lengths, a lead stated twice
inside one list. `criteria._addressed` validates the address at the write, which is L1
and right; nothing re-asks once the address has stopped existing, and the write path
cannot, the block having been there when the bullet was written.

So the finding is at the heading and its subject is the address, one per region and not
per bullet: what is orphaned is the list. This stays the backstop the two writes above
make rare and never impossible — a hand edit, a textual merge, a tree governed before
either of them shipped.

The door is `criterion drop <lead>`, bare. The addressed form is refused, the address
being exactly what stopped existing, so a remedy spelling `--block` would name a command
that cannot run — which RK16 forbids. And an orphan the last drop leaves empty has no
door at all: the heading survives its bullets by design (RK1265), so `--fix` is what
takes that one, a heading addressed to nothing with nothing under it being derived dead
as a shipped task's queue entry is.

## Block E — Adoption

### §RK1313 The two tables the scaffold stopped writing

Observed on a tree `roadkeep init` had just created, 2026-08-23. `criterion add --block
A` refused with "roadkeep.toml declares no [criteria]", and `add --requires hardware`
refused with `requires.unknown`, naming a table the file does not carry.

RK1040 already settled this shape. `init` writes `## Non-goals` into the roadmap and,
for the same reason, writes `[non_goals]` empty into the config: a schema applied to
prose nobody wrote to it reports on adoption, but a section the scaffold just emptied
has no prose to report on, and leaving it ungoverned refuses the one verb that fills it.
The comment above that table in `render_config` says so.

RK1265 added the positive twin and RK1297 added the requirement vocabulary, and neither
reached the render. So the two verbs that arrived last are the two a fresh project
cannot call, and the remedy each refusal names is a hand edit to configuration this tool
owns - which is what RK1264 built `declare` to remove, and which over MCP is not an edit
at all.

They are not one fix. `[criteria]` is an opt-in, so the empty table is the whole of it.
`[requirements]` is a vocabulary: `declared = []` governs nothing and changes only which
refusal the author reads, so what belongs there is the commented stanza - the shape
`[ids]`, `[headings]` and `[ledger]` are already written in, which is written only where
a project departs from what every project starts with.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
