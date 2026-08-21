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

## Block D — The gate

## Block E — Adoption

### §RK1294 RK1294 The same reason, arriving twice

RK1293 made the argument for a governed number something the tool places, and placing it
twice is what a re-run does. Measured on a scaffold: `govern limits.symptom 100
--because "First reason."` run twice leaves

```
# First reason.
# First reason.
symptom = 100
```

and the second answer says `reason   written above the key, in your words` as if
something new arrived. Stacking is the right rule for a *different* argument — a raise
is a decision about the previous decision, and this project's own `[tools]` entry is
five of them written that way by hand. It is the wrong rule for the *same* sentence,
which is not a second decision but the same one arriving twice: a retried call over a
transport that dropped the first answer, a `replay` of a capture, or an agent re-running
a command it is not sure took.

The number is idempotent already — declaring 100 over 100 leaves one row — and the
argument beside it should be too. What is asked for is the narrow comparison: an
argument that is byte-for-byte the block already directly above the key is not written
again, and the answer says the reason already stands rather than claiming a write.
Anything wider is a judgement about whether two sentences mean the same thing, which is
a model, and this tool has none (L4).

### §RK1295 RK1295 An answer for a write that did not happen

`Declared.argued` is `bool(because)` and the placing is `_argued(config, because)`,
which wraps the prose and returns nothing at all when the prose is nothing at all. A
`--because "   "` therefore reports

```
  reason   written above the key, in your words
```

over a file that gained no comment. Reproduced on a scaffold: `govern claims.held 90
--because "   "` prints that line and leaves `[claims]` exactly as it was.

Small, and the class is not. Every answer here is a statement about what the file now
holds — `stage` names what to add, `removed` names a line that is gone, `decided` names
a row that arrived — and a caller that cannot see the file is the caller this transport
is reached from. An answer that reports a write which did not happen is the one defect
this project cannot let stand anywhere, because the answer *is* the contract: an agent
that reads "written above the key" has no reason to look, and the number keeps standing
with nothing beside it while the session that declared it believes otherwise.

The fix is one expression — the field says whether comment lines were placed, not
whether an argument was passed — and what it buys is the other branch firing: the
`--because` sentence naming the flag, on the call that tried to use it and gave it
nothing to place.

### §RK1296 RK1296 A reason kept where nothing hands it back

RK1293 moved the argument for a governed number out of the commit body and into the file
this tool owns, on the reasoning that a commit body composed by a tool this project does
not own is a place the argument cannot be kept. It is kept there now, and the read that
asks about the number does not return it. Measured here, immediately after declaring
one:

```
$ roadkeep govern reads.brief
reads.brief  utf-16 code units, per brief
  reading  none — no open line to brief …
  declared 3300
```

Directly above `brief = 3300` sit the four lines this session wrote arguing for exactly
that number, and neither answer carries a byte of them. The agent asking why the ceiling
is 3300 is told "3300", and the only way to the reason is opening the config — the read
L5 exists to replace, on the one file every other rule is read out of.

`Measured` should carry the argument standing above the key, the way it already carries
what the corpus says and what the project declares: the contiguous comment block
directly above the row, verbatim and unwrapped, absent where there is none. Then
`stated()` prints it under the reading and `--json` carries it as a field, and a raise
is argued against the argument it replaces rather than against a number with no history.

Two things it is not: a rewrite of the comment, `--because` being the only writer; and
an interpretation of what the comment means. What comes back is the lines that are
there.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
