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

### §RK1164 The count ship already knows

Measured over one block: six ships, six `list` calls immediately after, each asking the
same question — is this block done, and what is next.

`ship` already knows. Its result carries `event: {id, block, stage}`, so the block has
been resolved by the time the response is composed, and the standing sentence `list`
returns (*"Block L has 1 open"*) is derived from data the same call has in hand. The
second call re-reads the roadmap to recompute something the first one could have said
for free.

The cost is not the round trip so much as what it does to a loop. A caller running a
block task-by-task has to remember to ask, and the failure when it forgets is silent: it
ships the last task and reports the block finished without checking, or it stops one
task early because nothing said there was another. Both were reachable on the run this
came from.

What to add is small: the block's standing after the ship, in the same shape `list`
returns it, so a caller can act on one response. Not the next task's brief — that is
`pick`'s job and it would make a write verb answer a planning question, which is the
sort of merge that makes a surface hard to learn.

The same argument applies to `retire`, which resolves a block for the same reason and
leaves the caller in the same place.

## Block C — Query

### §RK1163 The design a dependency has already answered

Measured on a real run. Shio's SH720 asked whether a duplicate-URL check should widen to
drafts, and its rationale argued both sides: widening risks "a report full of findings
about drafts somebody is still writing", which is "the noise that gets a check switched
off". A genuine trade-off when it was written.

Its dep, SH719, shipped first — a unique index making a draft duplicate impossible to
create. That deleted one side of the trade-off: what remained to report was legacy
damage, never somebody's unfinished draft. The rationale still read as an open question,
and `brief` handed it over verbatim beside `deps_resolved: SH719 shipped`. Both facts
were on screen and nothing connected them.

Following the design as written would have given the wrong answer for a
defensible-looking reason. It was caught by reading the dep's commit, which a caller has
no reason to do when the tool has just said the dep is satisfied.

So: when a section's last revision predates the commit that shipped a dep the line
names, `brief` should say so — one line beside the section, not a refusal and not a
guess at what changed. `origin` already answers which commit wrote a design, so the data
is reachable from a verb that exists.

The general shape: a dep is not only a scheduling fact. Shipping one can settle a
question the dependent's design left open, and the design is the artefact least likely
to notice.

## Block D — The gate

### §RK1165 A run is one fact, said once

`gaps` on this repository prints **503 lines**, and 499 of them are one fact. Every row
of the run reads the same way — *never carried: the whole history mentions it nowhere* —
with only the number changing, from 501 through 999.

Measured: the never-carried ids are a **contiguous run of 499** plus exactly two singles, at 80 and
224. The run is a numbering jump — this backlog restarted its series at a thousand — so it is
permanent, unactionable, and 499 rows on every run for ever.

The two singles are the signal: each is a number the counter spent and no commit ever
carried, which is the reading RK95 built. They are findable today only by paging past
the jump.

This is RK1143's rule one command over — a row that is never the next step makes the row
beside it unread — and the shape is already in the format: a **range** is how this tool
spells many ids at once. One line for the run, rows for the singles.

What needs deciding: whether a run is collapsed by size or by *reason*. A jump in the
series and five ids somebody burnt in one afternoon are both contiguous, and only the
first is permanent.

Worth stating because it decided the prose above: naming those ids here is refused
(`body.promise`, RK431), an id in this prefix that no line carries being read as spent.
The rule found this section, which is the rule working.

## Block E — Adoption

## Block F — The plugin

### §RK1166 A stale registry row is not a wired plugin

`_plugin_is_wired` decides whether the launcher stands down, and it decides on a row in
the harness's registry matched by project path. That was a deliberate choice over "is
there a copy on disk": a marketplace clone and every cached version live under
`plugins/` whether or not this project uses them, so a glob finds files in cases where
no hook is loaded.

The converse was not considered. A row can name an `installPath` that no longer exists —
the harness prunes old versions and leaves the row behind. The launcher reads it,
concludes the plugin's hook is live, and returns 0 without guarding, while the plugin it
deferred to cannot load because its directory is gone. Both guards are absent at once,
which is the drift the docstring says this tool exists to stop.

Measured in the Viglet Turing corpus, whose row pins
`...\cache\alegauss\roadkeep\0.1.285` while only `0.1.685`, `0.1.721` and `0.1.727`
exist on disk:

    launcher, registry as it is   ->  exit 0, 0 bytes
    launcher, empty registry      ->  exit 0, 5204 bytes, permissionDecision deny

and, end to end, an `Edit` on `docs/ROADMAP.md` was not refused: it reached the tool and
failed on its own missing `old_string`, which is what a `PreToolUse` deny would have
preempted.

The fix keeps the reasoning that rejected the glob and adds the half it missed: a row
only stands the launcher down when the path it names is still there. A row pointing at a
pruned install is not a wired plugin, it is a stale record, and the safe reading of it
is the one already chosen for an unparseable registry.

## Block G — The editor surface (the backlog where the file is open)
