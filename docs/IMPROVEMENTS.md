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

### §RK453 Which lines claim an address, beside whether it is spent

RK452 stops the state being created; it does not reach the corpora already holding it. A
heading written before its line binds nobody for the rest of its life, and no command
lists one — the fixture's §I.1 was found by reading `ship`'s `kept` field as it scrolled
past, and Shio's were found the same way.

`anchors` is the only verb that lists sections, and its `live` answers a different
question: RK247 built it about address reuse, so `live` means a heading declares the
address *now*, and §I.1 — written for a task that has since shipped, claimed by nothing
open — is counted among `3 live` beside two that are working.

`lint` cannot be the reader, and RK236 already said why. Under an outline a heading
naming no task is prose belonging to none, which Turing's standing GEO memo genuinely
is, so a finding would refuse a legitimate memo with nothing that closes it. The state
is a fact and not a violation, and L5 is that a fact costs a command rather than a file
read.

So the claim goes where the sections are already listed: per address, which live lines
point at it and whether its heading binds one. An adopting project sees its unbound
headings in one call, RK452's write is auditable instead of asserted, and an address
whose only claimants are in the ledger is named — the thing `ship` reported once and no
reader has held since.

## Block D — The gate

### §RK454 The repair that is claimed and never made

RK451 reads a governed file whose every byte is NUL as one finding naming the restore. A
file where *some* blocks reached the disk is the likelier shape on a large one, and it
falls through to the character pass. Measured on a 505-byte roadmap holding one good
line and 400 trailing NULs:

    ROADMAP.md:6:400  char.invisible  U+0000 unnamed control character at column 400 …
    400 problem(s) … 400 of them need no decision: … lint --fix

Two things are wrong and the second is the loop. The diagnosis is wrong in kind: RK118
wrote every byte of a governed file and none was ever a NUL, so a NUL is a lost write
rather than a character somebody typed — the same fact RK451 acts on, one file shape
over. And the remedy is claimed and not made: `--fix` counts all 400 as needing no
decision, writes nothing, and the next run prints the identical report. A caller that
trusts the sentence runs it forever.

The `_voided` predicate is the wrong shape to extend, because this file *is* text — most
of it parses. What the check has to ask is whether the file holds a NUL at all, and then
say which lines the loss reached rather than which columns.

Open: whether the finding replaces the character pass for that file, as RK451 does, or
sits beside it. Some of those lines are readable and their other defects are real, and a
report that hides them has answered a different question than the one asked.

## Block E — Adoption

## Block F — The plugin
