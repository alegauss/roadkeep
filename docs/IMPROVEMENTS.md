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

### §RK1685 Several designs in one read

Measured in a consuming project, on a task whose whole shape is a fan-out: one
instrument had to carry an entry per roadmap line waiting on an external release, and
the roadmap said thirteen lines. Writing an entry needs each line's design, because the
design is where the awaited artefact is named — a bin, an export, a type that must
disappear.

`show` answers one id per call and returns the whole record around the prose. `section
find` reports which anchors hold a string, with counts, and deliberately not the prose.
So thirteen designs is thirteen round trips, each carrying a line, its deps, its blocker
chain and its non-goals, none of which the fan-out wanted. The session did what is cheap
instead: read the prose file with a script, matching headings by anchor. That is the
read roadkeep exists to replace, and the one that goes wrong quietly — a renumbered
anchor, a level-2 heading where a level-3 was assumed, and the extract comes back short
with nobody the wiser.

A read that answers several ids at once, returning each one's section body and the
pointer it resolved, would make the correct call the cheap one. Shape it as `show`
accepting repeated ids, or a verb taking a block, since a fan-out is usually a block or
a filter rather than a typed list.

The argument is roadkeep's own: a consultation that costs more than reading the file is
a consultation nobody makes twice.

### §RK1686 The generator diff is not the task cost

Measured on Cottony, a Godot match-3 and the first game this format has governed. Its
sprites are generated by a Python script and committed on purpose, so a clone needs
nothing installed. RK37 there shipped one change to `specials.py`; the commit `weight`
reads carries 46 files and 770 lines, of which the authored half is 8 files and 78
insertions and the rest is 37 PNGs with the `.import` sidecar Godot writes beside each.

Both axes are wrong by roughly six on every art line, and wrong in one direction: the
blocks that generate most are priced as the most expensive, which is the opposite of
what an agent pays. The docstring calls files "what an agent holds in context", and an
agent holds none of those PNGs.

Not a new idea, only an unreached read. RK1473 gave `unclosed` this exact filter, and
`[history] incidental` already names the class — what a commit carries that is not the
work. `weight` does not consult it. What that key means there is a path a project's own
hook writes; here it would be a path a project's own generator writes, which is the same
fact about the same commit.

Cottony would declare `docs/design/art/**` and `docs/design/audio/**`. Whether the
existing key stretches or a sibling is declared is the open question, and it is a
question about one config read rather than about the percentiles.

### §RK1687 A criterion that cannot be a regex

`evidence` and `remaining` share one grammar, `<pathspec> :: <regex>`, and it can only
ask whether text is there. On Cottony, the two art lines carrying a real acceptance test
carry it as prose instead.

RK99's proof is a number out of a picture: the 99th percentile of saturation inside the
board, 0.683 against the reference's 0.881. Its section ends "Re-run the same crop after
RK95 and compare the percentile, not the mean" — an instruction, not a query, sitting in
the one thing `ship` deletes. RK100's is "Judge it on `cottony-board-screen.png`,
against `combo.png`, not on its own". Neither is a regex over any file in that
repository, and both are the whole of what done means there.

`brief` already asks for this: with no criterion it prints the `criterion add --task`
that opens one. But a criterion is a sentence a reader checks and `evidence` is the half
that runs, so a project whose deliverable is a PNG, a WAV, a mesh or a frame time writes
the sentence and never runs it.

Check the non-goals before this becomes a design. "No model and no prompts" binds hard:
whatever answers must be the project's own, never this tool judging a picture. That is
the shape `evidence` already has, where the pattern is the author's claim and the count
is the answer — so the open question is what a declared reading may be, not whether the
tool forms an opinion.

### §RK1688 An artefact is named the way its generator names it

`paths_in` keeps a quoted token that resolves on disk, or one whose directory the
repository knows (RK55, RK217). A bare `combo.png` is neither: it has no directory to be
known by, and it sits under `docs/design/art/` while the section naming it sits in
`docs/`.

On Cottony, RK99 and RK100 name five artefacts between them — `combo.png`,
`friend_cloud.png`, `friend_pink.png`, `cottony-board-screen.png`, `meshy.py` — and
`show --json` reports an empty path list for both. All five basenames are unique in that
repository's own listing, so every one of them was decidable.

They are written that way because it is how the work refers to them: a generator's
output table names a sprite `friend_cloud.png`, and so does the person looking at it. A
code file gets a path because a path is how it is imported; an asset gets a name.

The stakes are wider than this read — the same list is joined onto other answers, so a
task whose files are all art names none of them anywhere.

RK217's reason still holds and bounds this: 60 of Shio's 61 findings were a MIME type,
an i18n key or two method names sharing a slash. A basename with no separator is a wider
door than that one, and what would keep it narrow is the listing this already consults —
a token matching exactly one tracked file is a different claim from one matching none or
several.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
