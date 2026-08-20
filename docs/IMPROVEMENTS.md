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

### §RK1278 The declared value, beside the default

The shape answers two of the three things a reader wants about a key and stops at the
third. It says what this build uses when nobody declares it, and it says whether this
project declared it — and where the answer to the second is yes, the number printed is
still the first one.

So a project that set `symptom = 90` is told `default 120, declared here`, which is two
true statements arranged to read as one false one. The reader most likely to meet it is
the one hovering the key they are about to change, which is the moment the value matters
and the default does not.

The reason it is absent is the reason `declared` is read back off the file: a parsed
config carries the *effective* value and cannot say which of the two it is. That reading
is right and half-used — the same parse that answers whether a key is written also has
what was written there.

What it must not become is a second parse. What TOML hands back is a scalar, a string or
a list, and rendering one is what `_rendered` already does; resolving it into what the
schema makes of it would be this reader re-deciding what the parser decided.

The absence is a value, not an emptiness: a key nobody declared has no declared value,
which is a different fact from one declared as zero and is said as such.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1280 The one file the guard allows, and what it could say

The guard's own sentence is that `roadkeep.toml` is not governed, "which a human edits
by hand on purpose". That was right when nothing else could write it, and half of it
stopped being true: four of its tables now have a verb that takes the reading first and
refuses a number this corpus already breaks.

So the two writers disagree about what is checkable. A `symptom = 90` typed in is
accepted and reported by the gate on the next run; the same number through the verb is
refused before it lands, naming the line that measures more. The first is the
arrangement this project exists to replace, and it is still the default.

**Denying it is the wrong answer** and the reason is in the shape of the file. A hook
sees a path, not a table: `[files]`, `[markers]`, `[refs]`, `[grammar]` and the rest
have no verb and are not going to get one, so a denial would make the config unwritable
in the sessions that need it most — including the one where `install` has not run yet.

What is missing is the notice. The guard already has the register for it: it allows, and
says what would have answered. An edit to this file is where a reader most needs to be
told that four of its numbers have a door, and the one sentence costs nothing on every
other turn — it fires on a path nobody touches twice a year.

## Block G — The editor surface (the backlog where the file is open)

### §RK1277 Two clocks in one payload

Two facts arrive in one payload and they move on different clocks. Which keys this build
accepts moves when the *engine* moves, so caching it until an explicit refresh is right
and was the reason for the cache. Whether this project declared one moves when the
**file** moves, and it is in the same object.

So a hover says "not declared here" about a key somebody declared a minute ago, and goes
on saying it until the person presses refresh — for a reason no reader can see, since
the row beside it is correct.

RK1017 drew the line this crosses. It kept two caches on purpose — the engine's, reread
only on the explicit ask, and the file's, dropped on every save — because the two
questions have different answers about when they went stale. This read joined the wrong
one.

And the watcher never sees the file at all. It matches Markdown, which was every
governed file when it was written; the config joined `lint`'s checked list since, so an
external edit to it re-runs nothing. A save inside the editor is covered by the save
hook and an edit from a terminal is not, which is the harder half to notice.

The repair is the split RK1017 already made: the shape stays on the engine's clock and
what the project declared is read on the file's, or the whole read moves to the file's
clock and an upgrade is what the refresh button is for.

## Block H — The tool's own shape (what one verb costs to change)
