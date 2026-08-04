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

### §RK201 The one surface RK185 did not reach

RK185 made the case in one sentence: a model has no characters, so a limit published
only in them is a target reached by trial. It then published the word aim on every
surface an author reads *before* composing — the MCP field schema, `budget`, `brief`,
the skill.

The refusal is the surface they reach after, and it still says "delete 9 characters".
That is exact and it is unactionable in the same way the ceiling was: the author
subtracts a number they cannot measure, and the observed loop is five retries against
one gate in a single session of this repository's own work.

The correction is small and it is not a second opinion: RK184 already computes the
surplus, and stating it as words alongside is the same conversion `budget` makes, from
the same constant. "Delete 9 characters — about two words" is a sentence an author can
act on without re-composing.

Two things to be careful of. The word figure here is a *surplus* and not an aim, so it
rounds the other way: rounding down would name a cut that does not clear the gate. And
the refusal must keep the character number first, because that one is exact and the word
one is an approximation of it — an author told only "two words" and given a 9-character
overrun would be back to guessing, with a smaller number to guess against.

## Block B — Authoring

### §RK236 A pointer under an outline is not a claim of ownership

Under `ref_scheme = "id"` the anchor is the id, so a section has exactly one owner and
deleting it on departure is right. Under `outline` the anchor is an address in a file
the project already keeps, and the two are not the same claim: Turing's Block O lines
pointed at `STRATEGY.md` §X.3 (content calendar) and §X.4 (measurement), subsections of
a standing GEO memo whose siblings §X.1 (thesis) and §X.2 (channel split) are the same
kind of prose and survived only because no line happened to name them. Retiring the last
owner of each deleted both, and restoring them took the hand edit the guard denies.

The two existing guards do not reach it. RK64 asks whether another **open line** points
at the anchor — true while four of five Block O lines were live, false at the fifth.
RK196 asks whether **two roles** declare it — which is why §X.1 survived, by the
accident of also being an IMPROVEMENTS heading.

What distinguishes the two cases is whether the section was written *by* an `add
--section` for this line, and the tool has that fact only where the anchor is derived.
So the honest shapes are a `--keep-section` on `ship` and `retire` for the author who
knows, or a refusal under `outline` when the anchor is not the line's own — never a
heuristic about prose the tool does not read.

### §RK237 The note under a block heading has no door

An adopted roadmap carries a blockquote under each block heading — what the block is,
and often a "fully shipped, see the changelog" paragraph — because that is what a
hand-written backlog looks like. Turing's had ten, and four of them stood over blocks
with no open line left at all.

RK144 is right to count that prose: a paragraph orphaned by a removed heading is filed
under the block above it, silently and in a way that round-trips. But the consequence is
a corner with no exit. `block drop` refuses while the note is there; no verb writes or
removes a block note, so the note can only leave through an `Edit` the guard denies or a
`Bash` write the user approves and RK175 then reports as unattested. The block that most
needs withdrawing — every line under it shipped — is exactly the one whose note says so.

Two shapes, and the second is the smaller: a verb that takes the note (`block note
--drop`, one heading's loose prose and nothing else), or `block drop --prose` naming
what it will take in the refusal it currently only refuses with. Either way the fact
worth keeping is that the note is *loose prose under a heading*, which the document
model already resolves — nothing here needs to read what the prose says.

## Block C — Query

### §RK200 The record with no way to read it

RK175 closed the symptom it was filed for: a governed file whose bytes no verb wrote is
named as the turn ends. What it did not give is a way to *ask*. The digest sidecar is a
temp file whose name is a digest, the comparison happens inside a hook, and the answer
reaches exactly one reader at exactly one moment.

That is the arrangement RK161 ended for claims, and the argument is the same one: L5
says every question is a command, and "which lines are claimed" had to be answered by
finding a temp file. Here it is worse in one way — reporting **re-baselines**,
deliberately, so a turn that ends is a turn whose evidence is consumed. A session asking
afterwards what happened has nothing to read, and neither has the next one.

The obvious shape is the one `claims --prune` has: a read that says which governed files
are attested, which are not, and where the record lives — without moving the baseline,
because a query that changes the answer to the next query is not a query. Whether the
`Stop` block should stop re-baselining once such a read exists is the second question
and not this one.

What to check first is whether anybody wants it. The claim registry earned its read
because `pick` stepped over ids and could not say whose; this record has one consumer
and may not need a second.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin
