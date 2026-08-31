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

### §RK1441 A help string quoting a grammar nothing checks

`--have` on `pick` and `brief` reads: a ready line whose `(needs: ...)` names anything
undeclared is set aside. The schema writes `(requires: ...)` and its parser matches only
that. A caller who takes the help at its word and writes `(needs: ps5)` onto a line has
written prose the grammar does not read as a requirement at all.

IT IS NOT ONE SLIP. `config.py` calls `[requirements]` "the words a `(needs: ...)` group
may draw on", and `picking.py`'s own docstring says the same. Three sites agree with
each other and disagree with the one that decides, which is how a wrong spelling
survives review: it reads as the convention.

WHAT MAKES IT REACHABLE is that nothing joins the two. Every field name a help string
quotes is a claim about the format, and the format is a template of named slots this
package can enumerate. A test over the parser's help text and the slots that template
declares would have refused the first one.

THE CHEAP HALF IS THE CORRECTION and it is three edits. The half worth having is the
join, which is what stops the fourth site.

## Block C — Query

### §RK1439 The line seven other tasks were filed against

Observed in the pportal port, on PP33 - delete curl and json-c from the C core. It has
been the answer to `pick` for many sessions running, and no session has worked it. What
each one did instead is in the ledger: PP544, PP563, PP564, PP565, PP566, PP573 and
PP584 all say "PP33" in their own sentences, all shipped, and PP33 is still open. Seven
children, one parent, and `pick` offered the parent every time.

RK1297 answered the neighbouring case. A line needing a console or a runner reads as
ready, so `[requirements]` was declared and `pick` learned to skip it. This is the same
sentence with a different absence: nothing is missing, the line is simply larger than a
session, and the caller finds that out by reading its criteria and then filing a child.
The dep graph cannot say so, correctly - a child does not exist yet when the parent is
offered.

The evidence is already in the files. A shipped entry naming an open id is a fact `refs`
can see, so "seven entries against this line and it is still open" is a query and not a
new field. No verb asks it, so what would have told the eighth session what the previous
seven learned is spread over seven ledger sentences nobody reads in order.

Not a marker. `⏳` says a line is part-done and says nothing about who has been paying
for it.

## Block D — The gate

## Block E — Adoption

### §RK1438 The output an adopter actually reads

`install` prints what it wrote: the server, the guard, the skill, the workflow, each
marked written or unchanged, with the launcher's path substituted. It is an accurate
report of files. It says nothing about what those files now let a session do.

FOR AN AGENT THAT OUTPUT IS OFTEN THE FIRST CONTACT, and the first refusal is the
second. The skill is the third, arrives on a later turn, and is long enough that it is
skimmed - RK1424 measured it and RK1437 argues about its cadence. The two surfaces a
session reliably READS are the ones that say least about the tool's shape.

WHAT A FIRST CONTACT NEEDS IS SMALL. Which files are now the tool's and not to be
hand-edited; the handful of verbs a day actually uses - `brief` or `pick` to start,
`add` and `ship` to move, `lint` as the gate; and the two that answer without writing,
`budget` before a refusal and `show` instead of opening the file. Six lines, at the end
of a command an adopter runs once and reads.

IT IS ALSO WHERE `install --check` BELONGS IN A SENTENCE: the same output could say that
this is the command a CI job or a pre-commit hook runs to keep the copied skill in step,
which is a fact currently discoverable only from `--help`.

The suggestion is deliberately not more documentation. It is putting the smallest useful
part of it where somebody is already looking.

### §RK1440 The gate that is somebody's checkout

Observed in the pportal port, over one session. `roadkeep lint` reported the gate as
0.2.35, then 0.2.37, then 0.2.38 - and in between it crashed outright with an
AttributeError raised inside linting.py. Nothing had been installed or upgraded. The
`roadkeep` on that machine's PATH resolves into a checkout of this repository, and
another session was editing it.

THE CRASH IS NOT THE POINT. A working tree is allowed to be broken; that is what a
working tree is for. The point is that the adopting repository could not tell. It read a
version number, that number moved three times, and every reading looked exactly like a
release.

`engine.disagreement` ALREADY MODELS SKEW and models the wrong pair. It compares the
gate to the plugin wired into the project, which is the skew between two roadkeep
surfaces. It says nothing about whether the gate is a released version at all - so a
session reading it learns that two copies differ and not that one of them is somebody's
uncommitted edit.

RK1193 IS THE NEIGHBOUR, not this. That task gave an adopter a way to PIN the engine.
This is about the case where nothing is pinned, which is the default and is what a
developer machine looks like.

THE COST ROSE THIS WEEK. That port has just put `roadkeep lint` in its local gate, so a
build now fails on whatever happens to be checked out - right to wire, wrong to be
silent about.

## Block F — The plugin

### §RK1442 The count an agent cannot ask for

RK1432 gave `stats` a split: how many open lines nothing absent is holding up, and what
the rest wait for. RK463 established that a read the skill names and the surface
withholds is a read that machine cannot make at all, a plugin installing with no console
script and no PATH entry. `stats` is withheld, so the split reaches the terminal and not
the agent.

IT ALSO SILENCED THE DOCUMENTATION. The skill was going to say `stats` splits the count;
the test RK463 left behind refuses any read it heads a code span with that nothing
serves, and refused this one. The sentence went into the `list|stats|audit` clause
instead, where it is true and unaddressable - the reader is told a count splits and not
which command prints it.

THE OBVIOUS FIX IS THE WRONG ONE ON ITS OWN. RK1437 says the served surface is already a
reference loaded as an orientation, and `budget.session` refused a clause of forty
characters this week. A forty-fifth tool is paid for by every session at connect.

SO THE QUESTION IS WHICH. `list` is served and already carries the population; the split
could ride its payload instead of arriving as a tool. That costs nothing at connect and
answers the same question, and deciding it is what this line is for.

### §RK1443 The staleness notice, said once and made actionable

The MCP server appends a paragraph to every write when it notices the package changed on
disk after it imported: "N module(s) of this package changed on disk after this server
imported roadkeep... restart the session if it has not." It is correct, and it is
attached to the wrong unit.

An agent doing a batch of work sees it on `add`, on `section add`, on `status`, on
`ship` — the same words each time, in a session that cannot restart itself. Advice that
arrives once is read; the same paragraph on every call is skipped, including on the
write where a stale validator mattered.

Three changes, and the third is the one that pays. **Say it once per server process**:
the process imported stale code, and that does not become more true on the fourth write.
**Say what it invalidates** rather than what happened — which modules changed, and so
whether a validator, a limit or a renderer is the part that may disagree; a caller told
`authoring.py` is the stale one knows whether its own write is affected. **Offer the
reload, not only the restart**: a session cannot restart itself, so a notice whose only
remedy is an action the reader cannot take has no next step. The CLI path re-imports per
process, which is the remedy that works today, and it is buried in the last clause.

Falsified when a session doing ten writes reads the same paragraph ten times.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
