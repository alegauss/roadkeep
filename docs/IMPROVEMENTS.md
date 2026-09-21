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

### §RK1695 A count read as an address

`record amend RK1 --lines 2 --why "It works now.\n\n  more prose"` on a wrapped entry is
the reproduction: the blank line ends the entry, `Document.rewrite_entry` raises
`Continuation` exactly as designed, and the caller gets a Python traceback instead of
that refusal. Found while shipping RK1693, and reachable on every door that writes a
tail back.

The cause is a name. `_refused` asks `_retrying` for the retry a refusal can offer, and
`_retrying` reads the address off the first of `_OFFERS` — `offered`, then `free` — that
the error carries. `Continuation` stores its line count as `offered`, an `int`, so the
retry substitutes a number into the caller's argv and `deliverable` calls `endswith` on
it.

The repair belongs to the channel, not to this one error: rename the kernel's field
(`given`, as `Wrapped` already spells its own count) so no count can be read as an
address, and have `_retrying` take only a string, so a third refusal choosing the same
word fails as no retry rather than as a crash. A test drives the reproduction through
`main` and asserts exit 2 and the refusal's own sentence on stderr.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

### §RK1694 What a failure is owed

A validation that failed found a defect, and this tool has exactly one thing for a
defect: an open line. Leaving the verdict and the line as two commands is how the second
one gets forgotten, which is the argument `ship`'s three edits are one transaction for.

**`--files <symptom>` writes both**, as `--decides` writes a decision into the fourth
file: the verdict lands on the ledger entry, the open line lands under the same block,
and the caller's `--saw` sentence becomes its why. Nothing composes prose — the symptom
is the caller's too.

**Only with `failed`.** A `worked` that filed a line would be filing work nobody found,
and a `nothing to see` has nothing to report. Refused on either, naming the verdict that
takes it.

This is also what makes RK1690's rewrite-in-place safe. A verdict is overwritten by the
next one, but a failure that filed a line left a record no rewrite touches, and that
line ships into the ledger as its own entry.

Done when a failed validation with `--files` leaves the verdict and a new open line
under the same block, or leaves neither, and the other two verdicts refuse the flag.
