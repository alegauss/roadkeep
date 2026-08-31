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

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1445 The rule a pipe character satisfies

RK463 established that a read the skill names and the tool surface withholds is one that
machine cannot make at all: a plugin installs with no console script and no PATH entry.
The test holding it counts a verb as named only where it **heads** a backticked span — a
deliberate narrowing, since a bare word count said `writes` was named eleven times when
the command is named once.

THE NARROWING IS SATISFIED BY PUNCTUATION. `list|stats|audit [--block <x>]` heads with
`list`, which is served, so the clause passes while naming two verbs that are not.
RK1442 met this from the other side: the sentence about the startable split could not be
written with `stats` at the front of a span and went into the pipe instead, where it was
true and unaddressable. Neither `stats` nor `audit` is served today.

SO THE RULE READS AS SATISFIED WHERE IT IS NOT. A test whose verdict turns on which verb
an author put first reports on prose style, and the failure it exists to catch — an
agent told to run something it has not got — passes through unchanged.

WHAT WOULD ANSWER IT is deciding what a joint span means. Either every verb inside one
is named, which makes the clause a finding and forces the sentence to say which command
a caller actually has; or a joint span is an exemption declared once with its reason,
rather than a shape the regular expression happens to allow.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

### §RK1444 The surface the session page does not price

`SessionCost` renders `cost --tools` and `cost --session`, and the page around it argues
that the skill is trigger-loaded and therefore free on turns that touch no governed
file. What it never says is what that trigger costs when it does fire. RK1424 added
`cost --skill` for exactly that reading and `session.mjs` does not ask for it.

MEASURED WHILE SPLITTING THE SKILL. The prose fix was written and `budget.mjs` refused
it twice: first for typing a count, which this area renders rather than states, and then
because `session.mdx` is at 600 of 600 words — a twenty-six-word addition put it over.
So the page cannot say this without cutting a paragraph written for another argument,
and the area's rule already says which way to go: every figure here is rendered from the
tool that owns it.

WHAT WOULD ANSWER IT is `session.mjs` asking `cost --skill` beside the two it already
asks, and the component carrying a row for the orientation and one per reference page,
each labelled by the cadence it is paid at. Generated content is not counted against the
page budget, so this costs the prose nothing.

The reading duplicates neither figure above it: the schema is paid at connect, the
resident files every turn, and the skill only on the turns its description matches — the
distinction the page spends four paragraphs making and then prices two thirds of.
