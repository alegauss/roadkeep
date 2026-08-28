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

### §RK1416 A published field that never says anything new

`explain --json` carries `cause` and `decision`. Twenty-one codes carry a decision and
on every one of them it is byte-identical to the cause. Found while rendering the
finding pages (RK1403), where the page printed the same sentence under *What it means*
and again under *Choosing between them* — a reader concludes the second is an answer to
something the first did not cover.

The field is not pointless in principle. A `decide` finding has more than one door and
what to weigh between them is a real thing to say; the causes are written as lead-ins to
those doors, so a cause that reads as a decision is a cause doing two jobs.

Three shapes, and they are not equivalent. The field is filled with what it was meant to
hold, and the pages gain the half a reader most needs. Or it is dropped, and the doors
are the whole answer. Or it is kept and documented as a duplicate, which is the one that
should be argued against: a published key nobody may rely on is a schema that costs a
consumer a reader for nothing.

## Block E — Adoption

### §RK1415 The first configuration, which no verb writes

The walkthrough RK1406 captured has two hand edits in it, and the first is this one.
`init` scaffolds the configuration **and** the files it declares, so it refuses outright
where a roadmap is already there — correctly, since it would otherwise overwrite one.
`declare` adds a role to an existing configuration and does not choose a prefix. Between
them there is no door onto the case that matters most: a repository with a backlog
somebody has kept by hand.

So the adopter writes the file. That is not fatal — it is three keys — but it is the
first thing they do, it is the step no command list mentions, and it is where an
adoption is abandoned. `adopt` already reads the file and *infers the prefix from the
ids it finds*, which is the whole of what the hand edit supplies.

The shape to argue about is whether this is a flag on `init` that adopts rather than
scaffolds, or a widening of `declare` to write the file it is adding to. The first keeps
one verb per job; the second is where a reader already looks after `init` has refused
them and named it.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

### §RK1413 The situations, and the reader who is still not answered

RK1403 shipped a page per finding code and the half that is generated: the class, what
raises it, the doors that close it. The half no read derives is the **situation** — the
ordinary act that put somebody there — and thirty-five of a hundred and nineteen codes
carry one.

The build prints the shortfall on every run rather than hiding it, which is why this is
a task and not a discovery. What it costs is narrow and real: a reader who lands on an
undescribed code gets `explain` rendered as a web page, which is what they could already
have run.

The ones written first were chosen by where a reader actually arrives — the mechanical
fixes, the merge damage, the two id collisions. What is left is a long tail, and the
tail is where a situation is worth *most*, because those are the codes nobody meets
often enough to have learnt.

The failure to avoid is padding. A sentence that restates the cause makes a page say one
thing twice, which is worse than an absence — the suite already refuses that shape, and
it is the reason this cannot be closed by writing eighty-four sentences quickly.

### §RK1414 The one hand-written number on a generated page

Each verb family's page carries `sidebar.order` in its frontmatter, and the six numbers
put the families in the order `build_parser` calls them: writing, then the gate, then
prose, then shipping, then the reads, then adoption.

That order is a fact the parser already holds — the payload's `family` field is emitted
in walk order — so the numbers are a second statement of it. A test holds them against
that order today, which is the right shape and is also the evidence: a fact worth
asserting is usually one worth deriving.

What is small about this is also what makes it worth doing. A family added to `verbs/`
gets a page and needs a number, and choosing one means reading five other files to see
what is taken. A family removed leaves a gap nothing notices.

The shape is the one the finding pages already use: the generator writes the
frontmatter, so the order comes off the payload and the page carries prose alone. The
cost is that a reference page stops being purely hand-written, which is a boundary worth
stating rather than crossing quietly.
