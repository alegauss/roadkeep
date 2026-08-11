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

### §RK1030 The statement that was not the problem

A `roadkeep.toml` whose first three bytes are `EF BB BF` makes every verb of this tool
answer the same line:

> `roadkeep: Invalid statement (at line 1, column 1)`

Line 1 column 1 is `prefix = "RK"`, which is correct, and the message points at it. What
is wrong is a byte no editor shows, in the file a project writes before it has run
anything — and on Windows the default route writes it: PowerShell 5.1's `Set-Content
-Encoding utf8` and `Out-File` both add the mark, which is how this was found.

`config.py` opens the file `rb` and hands the bytes to `tomllib`, which refuses a
preamble by specification. So the diagnosis belongs here rather than upstream, and it is
the same argument RK1023 made about the pipe: the author cannot fix it from where they
are standing, because nothing in their command names the encoding that added the byte.

**Not the same fix.** Stripping it silently is right for a prose field and wrong for a
config: this file is the project's declaration, and a tool that quietly accepts one
encoding variant of it teaches nothing. So the answer is the message — name the mark,
the file, and the one-line command that removes it — with the edit left as the author's.

What proves it: a config carrying the mark answers with the byte and the fix rather than
with a statement that is correct, every other TOML error is unchanged, and the sentence
names the file the caller has open.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1031 A reserved id is not a spent id, and lint cannot tell them apart

Shio reserves ids for **epics** — `SH25`, `SH62`, `SH67`, `SH74` — each owning a
sub-range whose sub-tasks ship under their own numbers. The epic id is never a task line
and never a ledger entry; it exists so a reader can say "the Media Library work" in one
token, and Shio's own skill documents the convention.

`body.promise` reads every prose mention of one as an id no line carries, reads that as
spent, and reports it as a hazard for the deriver. Right about a typo, wrong about a
reservation, and the two are indistinguishable from the text. The consequence is not
noise but a **gate that can never be clean**: ten findings today, none actionable, none
removable — the advice each gives ("spell the example outside this project's prefix") is
refused by the convention it argues with. A permanently red gate is one nobody reads.

What is missing is a way to say **this id is reserved**. The shape that fits is a
declaration in `roadkeep.toml` beside `id_sources` — the file that already tells the
deriver where ids live, told which are spoken for. The deriver then skips them because
they *are* taken, `lint` stops reporting them, and a genuine typo still fails, because
it is not on the list.

The check that this is a fix and not a suppression: a reserved id later written as a
task line is a real conflict, and the tool should say so.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
