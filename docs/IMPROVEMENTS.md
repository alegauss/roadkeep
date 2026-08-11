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

### §RK1095 The two halves of one number

`budget --tools` answers what the served surface costs a session and `budget --file`
answers what an every-turn file costs a turn. Since RK1092 both rank their parts, so
both now have the same shape — a total, a breakdown, and a ceiling somebody declared —
and neither knows the other exists.

What a caller actually wants is the sum. An agent connected to this server and working
in this repository pays the tool list once and `agents.md` on every turn, and deciding
whether to cut a tool description or a paragraph means running two commands and
subtracting by hand. That is the arithmetic RK183 removed from the line budget and RK345
removed from the file one, still standing at the level above both.

The obstacle is that they are not the same unit of time. The schema is per session and
the file is per turn, so a single total would be a number that is wrong for every
session whose turn count is not one. What is honest is naming both against the thing
they are paid for — so many characters once, so many on each turn — which is two figures
and one sentence rather than one figure that hides a multiplier.

Worth checking whether the skill belongs in it. `skills/roadkeep/SKILL.md` is
deliberately not budgeted (RK23) because it is trigger-loaded, and a session that writes
on every turn pays it on every turn — which is the case this read would be for.

## Block D — The gate

### §RK1094 Advice older than the file it is about

`roadkeep.toml` says the Layout index is *~20% of the lines and ~23% of the bytes*, and
concludes: when this file is at the wall again, compress the prose and not the index.
`budget --file` now reads it as **3,136 of 8,392 bytes — 37%** — and 42 of 123 lines,
34%.

The advice was right when written and has not been re-derived, which is the shape RK203
is about one level up: a number stated in prose moves without anybody noticing. Every
task that adds a module adds an index entry, and the prose has been compressed twice
since — RK1091 took two paragraphs to buy one rule — so the halves moved in opposite
directions.

What that changes is which is the cheap cut. At 37% the index is the largest thing in
the file by nearly three times the next section, and it is also the part
`tests/test_linting.py` holds against `src/roadkeep/` — so shortening an entry is safe
in a way shortening prose is not, because the test says what may not be dropped.

Two ways to take it. Re-measure the sentence and leave the conclusion, which costs one
edit and is honest. Or compress the index and let the prose keep its slack, which is the
opposite of the standing advice and what the number now supports. Worth deciding with
`--json` in hand rather than by re-reading the paragraph.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
