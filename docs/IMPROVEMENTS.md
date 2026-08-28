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

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

### §RK1405 The agent surface, priced and explained where a person can read it

Half of this tool's surface is not a command line. A session gets a hook that denies an
edit to a governed file, a skill saying which command to call instead, slash commands, a
server with tens of tools, and a launcher for the sessions where no plugin can be
installed. The README covers installing all five; nothing describes what the session
then receives.

That reader's questions have numbers in them. What connecting the server costs before a
call is made, which `cost --session` answers and `[tools]` bounds. Which tools appear at
all, since a verb that is one role's whole grammar is published only where that role is
declared, so two projects see two lists. What the guard denies, what its refusal says,
and why it names a command rather than stopping at no.

The list is generated from the served schema, for the reason every reference here is: a
description is edited in a docstring and priced by a budget, and a page restating it is
a copy that drifts silently.

The prose beside it is what no read answers — when the skill loads and what a turn
touching no governed file pays for it, what the hook does on a session that has the
plugin twice, and what three copies of this tool disagreeing looks like, which is
`engines` and which an adopter meets as a refusal they did not expect rather than as a
concept they were taught.

### §RK1406 The adoption walkthrough, with output a test captured

Adoption is the path with the most friction and the least prose. A project that already
has a backlog scaffolds or adopts, declares the roles it wants, installs the surfaces,
registers the merge driver, and only then finds out what its existing files break. The
README gives the commands; it gives no run.

So the page is a walkthrough with real output: a repository with a drifted roadmap in
it, each command, what it printed, what it refused and what the tree held afterwards.
The refusals matter most — being refused by `adopt` on a file that has always been there
is the moment an adopter decides the tool is not worth the trouble, and the baseline
that forgives standing debt by name is the answer they never read.

Output pasted into prose is fiction with a shelf life. The corpora this suite already
runs against are the way out: the walkthrough is a script the tests execute, its output
captured and rendered into the page, so wording that changed fails a build instead of
misleading a reader.

It has to end with the first ordinary session — a task added, its design filed, a ship,
and the one commit carrying all three — because the friction adopters report is rarely
the install. It is the first write they made by hand out of habit, and the denial they
then had to interpret.

### §RK1407 The model page, which is the one thing nothing derives

The verbs are learnable one at a time; the model behind them is not. A line is a claim
carrying an id, a marker, a dep group and a pointer. The pointer resolves into a
rationale section that a ship deletes. A block is a heading several files agree on. A
criterion says what makes a block finished where a non-goal says what may not be
proposed. The queue is a section, a pause is a role, and a decision outlives the task
that made it.

None of that is written for a person. The skill states it for an agent mid-session,
shaped for the moment a write is about to happen; the module docstrings state it for
whoever is changing the code; the design rationale here states it one task at a time and
is deleted as each ships.

So this page is the reader's own: what the roles are and which file each is, what a
task's life looks like from insertion through every door it can leave by, and what each
door leaves behind — an entry, a forward pointer, a gap, or nothing at all.

Its test is whether the reference pages have to explain themselves. If a verb page needs
to say what a block is before it can say what the verb does, that sentence belongs here
and the reference links to it. It is prose all the way down, because the model is the
one thing nothing derives.

### §RK1408 Render what a file owns, restate nothing

This project's own thesis is against what a documentation area usually becomes. The six
laws are written in `agents.md`, in the README, in the design rationale and in
`llms.txt`; a fifth copy is the accretion the tool exists to refuse, and the copy nobody
is looking at is the one that drifts.

The rule is that a page renders prose this repository already owns rather than restating
it. The measured problem, the laws, the non-goals and the status all live in files with
an owner, and three of them have a verb: `non-goal list` is the list, `export` is the
projection, and a page holding its own version of either is stale from the next write.

Where a page needs framing no file carries, the framing goes in the page and the
substance stays where it was. Where a page would state a count, it renders the
projection or states no number — which is what the pitch page already does and what a
test already holds it to.

The direction matters. The README is what GitHub renders and what PyPI shows, so it
stays the short one and this area holds the long form; the failure to avoid is a README
demoted to a summary of pages nobody reaches without a browser. What the area adds is
depth the README cannot afford, never a second telling of what it already says.

### §RK1409 The area's own budget, held by something that refuses

The measurement that started this project is what an unbounded prose file costs: an
index at 186 KB while declaring itself an index, a rationale file at 539 KB while scoped
to unshipped work. A documentation area is that same invitation with better typography —
every page has room, nothing refuses a paragraph, and six of the eight worst lines were
written by the author who then diagnosed the drift.

So the area declares its own numbers and something holds them, the way `[budgets]` holds
the every-turn files: a word budget per page, measured against the pages that already
read well rather than picked, and a rule that a page restating a count fails.

What this cannot be is a lint about prose quality. The limit is a number a build checks,
and what it buys is what the write path buys — the question "what would I cut?" never
arrives, because the ceiling was known before the first sentence was composed.

Generated content is the exception. A verb page's table is as long as the parser makes
it, and cutting it would be editing a schema to fit a budget, so the budget is over the
prose an author wrote and the generated half is counted and reported apart. The number
goes where every other number in this project goes — declared in configuration, argued
above the key, and refused if this corpus already breaks it.

### §RK1410 A fetchable twin per page, and the index that has to name it

`llms.txt` exists because a model reading this project should not have to render a
landing page to learn what it is. An area published as HTML alone re-creates that
problem one page at a time, and what a read costs an agent is this project's whole
premise.

So every page keeps a fetchable plain-text twin at an address derived from its own, and
the area publishes an index of them. The source is Markdown already: what is needed is
that the build emit it beside the rendered page rather than only the page, and that the
address be derivable, so a link handed to a session resolves without a lookup.

That is also what keeps `llms.txt` honest. It is hand-written today and says what the
tool is; once there are pages, it is the index naming them, and a page added without an
entry is a page no agent finds — a check the build makes, not a habit somebody keeps.

What it must not become is a second corpus. The twin is the same bytes rendered
differently, emitted in the same build, so nothing is written twice and no file can
disagree with the page beside it. Two files saying almost the same thing about a schema
is the failure this tool was written after watching, and it is no better when one of
them is for a model.
