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

### §RK1710 The non-goals a listing leaves out

Found in quickshell (QS225), whose roadmap carries 21 non-goals. `non-goal list` prints
twelve and ends `... and 9 more under Non-goals`; `--json` carries the same twelve and
`non_goals_elided: 9`, with no lead and no reason for the nine. No flag asks for the
rest, so a non-goal that binds the task at hand can only be read by grepping the
governed file, which is the thing the tool exists to make unnecessary.

The task needed one of the nine: QS225's design says that a monitor-covering chain
reaching independent flip names an exception in the non-goal about windowed latency, and
that non-goal is not among the twelve printed.

What to build: `non-goal list --all` prints every entry, and `--json` always carries
every lead and reason (the elision is a terminal convenience, not a data limit). Where a
filter is wanted, `--near "<text>"` ranks the leads the way `delivered --near` does, so
a caller can find the one non-goal about a subject without reading all of them.

Falsified when a project's twenty-first non-goal can be read through `non-goal list`.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1709 anchors --next answers nothing where a new block needs a top-level

Seen in Shio, an outline-ref project whose IMPROVEMENTS.md mixes numbering families
(VI.2, VI.3, VI.4, VII and the roman top-levels up to LXXV). A session reopened a
finished block, so its first task needed a fresh top-level family. Neither answer the
tool offers helped: `anchors --next` printed 'not one numbering, so none derives' for
the default namespace and for every family, and `anchors --block U --next` refused
because no open line in the block carries a pointer yet. The only way to find LXXVI was
to grep the governed prose file for headings, which the project's rules forbid, since
those files are read only through roadkeep.

Once LXXVI was known, `add --ref LXXVI.1` accepted it and opened the family, so the
write side works (RK1140). The gap is on the read side. When the families are not one
numbering, `anchors --next` should still name the next free top-level of the main
sequence, which here is the roman numerals past the highest one used. If it cannot, it
should name the families it compared and how to pick one, instead of printing the same
refusal once for each. A caller should never have to read the file to learn an address
the tool is about to validate.

The capture attached to the line is the failing call as it ran, with the project's
roadkeep.toml.

### §RK1711 The first strategy section of a fresh scaffold

Found adopting roadkeep in a new private repository (alegauss/visibility) on 2026-10-13.
`init --prefix VS --block A --block B --block C --strategy --deferred` wrote
docs/STRATEGY.md with the three block headings and no section. Every attempt to write
the first strategy section was refused with "no section §<x> extends (docs/STRATEGY.md
declares: none)": the anchors tried were B, B.1, I and S:I. The refusal's own remedy
reads "`roadkeep section add B --title … --role strategy` opens what it extends", which
is the first call that was refused. A task id is refused too, correctly, since no line
points there. So a project that asked init for a strategy file has no door to its first
paragraph except a hand edit, which the guard denies. The fix decides what anchor opens
the first section under an outline or id scheme, accepts it, and makes the refusal's
remedy a call that succeeds; a test runs init --strategy and writes one section through
the CLI. The report captured with `roadkeep report` holds the environment.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)
