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

### §RK1023 Stdin, the escape hatch a shell cannot reach

A `why` containing a double quote cannot be passed inline from Windows PowerShell — the
quotes reach argparse and the tail of the sentence comes back as `unrecognized
arguments`. The documented way out is in `add --help` itself:

> `--why WHY  one sentence, ending in a stop; '-' reads stdin, which is how an apostrophe or a
> backtick survives a shell`

On Windows PowerShell 5.1 that route is closed. Piping to a native command encodes
through `$OutputEncoding`, and the encoder emits a UTF-8 preamble, so the first
character roadkeep reads is U+FEFF. It then refuses:

> `U+FEFF ZERO WIDTH NO-BREAK SPACE at position 1: invisible in an editor … pass the field on stdin
> with -, where nothing rewrites it`

The remedy the refusal names is the route the author already took. Setting
`$OutputEncoding` to a `UTF8Encoding` constructed with `$false` does not help; the
preamble still lands.

**The fix** is one line at the read: strip a single leading U+FEFF from a field read on
stdin. A BOM at position 1 of a stream is a byte-order mark doing its job, not prose —
it is only content once it is somewhere else in the string, and there the existing check
still catches it.

**Why the reader and not the author.** Stdin exists so a shell cannot corrupt a field. A
stdin path that a mainstream shell cannot feed correctly is not an escape hatch, and the
author cannot fix it from where they are standing: nothing in their command names the
encoding that added the byte.

### §RK1024 The budget the insert did not check

`add` opens its own help with the promise that nothing is written unless every field
passes, because *a limit reported after the prose exists is a limit discovered too late
to save the tokens it was meant to save*. It then did exactly that.

The sequence, in one project, in one sitting:

1. `anchors --block AJ` answers `next §L.1 — nothing ever used it`.
2. `budget` reports `section 300 words (improvements), 249 written, 51 left`.
3. `add --ref L.1` **accepts** a 278-word section: `design §L.1 → IMPROVEMENTS.md:963  278 words`.
4. `lint` fails: `L: 577 words, limit is 300: delete 277 words`.

The parent `§L` was already 299 words of its own 300. Nesting counts the child inside
the parent, so **every** subsection of `§L` is over the limit before a word of it is
written — including the empty one. The anchor `anchors` recommended cannot be used at
all, and neither `anchors` nor `budget` nor `add` said so; only `lint` did, after the
prose existed.

**Two fixes, and the second is the one that matters.** `anchors` should not offer a
child anchor whose parent has no budget left. And `add` should validate the section
against the total it will produce, not against the child alone — which is the check it
already claims to be.

The recovery, for whoever hits this before it is fixed: `git restore` the governed files
and re-add against a free top-level anchor. Nothing else undoes it.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
