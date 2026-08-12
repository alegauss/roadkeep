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

### §RK1107 A heading with no anchor, and the hand edit it forces

Every write here addresses a section by its anchor, and a prose file's first two
headings have none: the preamble that says what the file is, and the `## Table of
contents` that lists its families. `section show 'Table of contents'` answers that no
such section exists, which is true and leaves the caller one door — the hand edit the
guard exists to deny.

It matters because those two go stale mechanically. `ship` drops a section; where that
section was a family's last child, the contents row naming the family and the preamble
sentence introducing it are both wrong in the same instant, and each is a derived fact
about a file this tool owns that nobody reports.

Two questions the design has to answer. The first is what the address is: a title is not
an anchor and a positional name (`preamble`, `contents`) is a second addressing scheme,
so it has to be one the project declares rather than one invented here. The second is
whether a contents is prose at all — a list of the file's own headings is derivable,
which makes it a rendering and not a body, and then the verb is not `amend` but the
`--fix` that already repairs the other derived fields. The preamble is genuinely prose
and needs the first answer, so the two headings that look like one problem are probably
two.

### §RK1109 A confirmation over prose that was never read

`section amend <anchor> --title "…"` deliberately leaves the body alone: `None` stays
`None`, so a title-only amend does not block on a pipe nobody meant to open. That rule
is right and it has a failure mode. A caller who piped the new prose *and* passed
`--title` gets the title compared alone, and where the title already reads that way the
answer is `§XI.21 unchanged: it already reads that way` at exit 0 — over a paragraph on
stdin that was never read.

That is a silent no-op wearing a confirmation, which is the one shape a write path may
not have. Everything else here refuses and says what it looked at: a field over its
limit exits 2 naming the limit and the line of config that set it, an unresolved pointer
is a finding with the command that closes it. This one reports success about a file it
did not open.

The fix is not to read the pipe. It is to notice that a body arrived: stdin not being a
tty is a fact this process has, and `reading.py` already decides whether fd 0 could be
made strict UTF-8 for its own reason, so the reader exists. Where a body is detectable
the answer is a refusal naming `--body -`; where it is not — a harness that handed over
a used fd 0 — then `unchanged` has to say that no body was read, since the caller cannot
otherwise tell the two cases apart.

## Block C — Query

## Block D — The gate

### §RK1106 The fourth relation: a citation inside prose

`referring.py` declares three relations — a dep names an id, a pointer names a heading,
a queue entry names either — and argues that a fourth should be a line there rather than
a fourth implementation. This is that fourth. A `§X.Y` written **inside a section's
body** is a reference nothing resolves: `ref.unresolved` reads the pointer a task line
carries and `section.stale` catches the other direction, so a body citing a section that
has shipped lints clean.

Measured on Shio: four citations in `docs/IMPROVEMENTS.md` name retired addresses —
`§II.1`, `§II.7`, `§III.1`, `§III.10` — against an `anchors` that reports family II as
one live and seven retired. `lint` says clean over 641 lines. The reason none is caught
is that a citation was never a field, and every check here is over a record's field.

What makes it hard is what `ship` and `section drop` already do: both name the sections
whose prose cited what they deleted, so the fact is derivable at the moment of deletion
and is reported to a caller who may not act on it. The gate is the backstop for exactly
that, which means the scan and those two answers have to read one index — otherwise a
project gets two counts of its own dead citations, and the reader that agrees with the
file is not the one it was told to trust.

## Block E — Adoption

## Block F — The plugin

### §RK1108 The environment the plugin never reaches

The plugin is the whole install on a developer machine, and there is one environment it
never reaches: Claude Code on the web reads settings and files committed to the
repository and installs no marketplace plugin. The hooks and the server never load, the
guard is absent, and an agent falls back to editing the governed files by hand — the
drift this tool exists to stop, in the environment with the least supervision.

Shio answered it with a committed `.claude/hooks/roadkeep-launch.py` that resolves an
engine at runtime and stands down where an installed plugin is present, so nothing
double-fires. That file is where the defect was measured: it looks under
`~/.claude/plugins` alone, so where `CLAUDE_CONFIG_DIR` moves the harness's real config
directory it finds a stale copy, defers to it, and no guard runs at all. A hand edit of
`docs/ROADMAP.md` and `docs/IMPROVEMENTS.md` passed.

`provenance.installed` already resolves that pair — the environment variable or
`~/.claude` — which is the whole argument for moving the launcher here: *which copy
answers* is this tool's own question, `engines` already reports it for three copies, and
a project re-deriving it gets one of them wrong quietly. What `install` writes is the
surface to put it on. Whether the fallback may clone over the network is a separate
decision and probably a no.

## Block G — The editor surface (the backlog where the file is open)
