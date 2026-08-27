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

### §RK1398 An area with pages, not a longer README

The README is the only prose this project publishes for a person, and it is one file: 24
KB covering the measured problem, the six laws, three installation routes, the gate, the
plugin and the non-goals. A reader who wants one of those reads past the other five, and
a link to any of it is a link to the whole thing.

Everything narrower is inside a checkout. `--help` is a terminal read, `explain` answers
a code from an installed copy, `config` describes `roadkeep.toml` from a build, and the
skill is written for an agent that already has the plugin. So the order is backwards:
the reads that would decide an adoption are the ones that need the adoption first.

What is missing is an area with pages — a sidebar that says what exists, search over all
of it, and a contents list per page. PPortal's `site/docs`, in this same author's other
repository, is that area: Astro and Starlight, indexed at build time, emitting static
HTML into a directory GitHub Pages serves. Nothing there runs, which is the only shape
this project's non-goal against a server allows.

This task is the area and its first page, not its contents: the build, the theme, the
navigation and the entry page, with the reference and the walkthroughs filed as their
own lines.

### §RK1399 Where the build may write, and what it must stay invisible to

`docs/` is two things at once. It is the governed store — `roadkeep.toml` points
`roadmap`, `changelog`, `improvements` and `decisions` at files in it — and it is what
GitHub Pages serves, which is why `index.html`, `llms.txt`, `robots.txt`, `sitemap.xml`
and `assets/` sit beside the Markdown. A build whose output directory is that directory
writes over the store.

So the area needs a reserved subtree the build owns entirely and no verb writes, with
its source outside it. The joins are the three PPortal's `astro.config.mjs` names and
asserts: the base path, derived from the repository name and the one segment this area
occupies, since a href typed by hand keeps no prefix and 404s in production alone; the
output directory; and discovery, because the pitch page ships a hand-written
`sitemap.xml` and `robots.txt` that will never know these pages.

Two more are this repository's own. The gate reads the store's declared paths and the
every-turn budgets, so generated HTML under `docs/` has to be invisible to it rather
than merely tolerated; and `id_sources` scans prose for spent ids, so a page quoting one
must not mint it.

`node_modules` and the build cache are ignored. What is committed is the source and the
output both, because Pages serves a branch here and no workflow uploads an artefact — a
standing cost this area inherits and the deploy is free to change later.

### §RK1400 The build in CI, and which of two deploys this area takes

A build that runs on one laptop breaks in the commit nobody ran it. The gate here
already runs the action on this repository's own docs, pytest on three Pythons and
`claude plugin validate`; an area no job builds is the one surface whose breakage is
found by a reader.

The job is the install and the build, failing a pull request the way the other four do.
It is also where the derivation is proved: the reference pages are generated from what
this package declares, so the build is what shows the generation still runs and its
output still matches what is committed.

Which raises the second half. Pages serves this repository from a branch, so built HTML
is committed and a stale commit publishes a stale site — the same defect the derived
README block has, and the gate already refuses that one by splicing the projection and
comparing. Either the gate compares the built output against its source the same way, or
the deploy becomes a workflow that builds and uploads an artefact and nothing is
committed at all.

The second is the smaller standing cost and the larger change, because one deploy cannot
have two sources: it takes the pitch page, the assets and `llms.txt` with it. Whichever
is chosen is a decision this task records, not a preference the next reader has to
reconstruct from the workflow file.

### §RK1401 The parser as a payload, so no page declares it twice

Every reference page about the command line is a second declaration of the parser. Typed
by hand it is wrong at the first renamed flag, and nothing reports it: the page keeps
rendering.

The package already holds the whole truth — each verb, its flags, their defaults and
every `help=` string — and `cost --tools` proves it can be read as data, since it prices
a served description by walking exactly that. What no read does is print it. `--help` is
text formatted for a terminal, and parsing that back is a scrape of this project's own
output, which breaks on a line wrap.

So one read emits the parser as a payload: every verb, every flag, what it takes, its
default, the sentence it already carries, and whether it is published over the served
surface. It is a read about the tool rather than about a governed file, so it costs a
session nothing until it is called, and it is filed in this block because the area is
the only thing that wants it.

The alternative is a page listing flags, which is prose accretion about a schema — the
one kind that can be derived instead. This is the same argument the projections make:
never restate, always project, and let the gate say when the projection went stale.

### §RK1402 A reference generated per verb family, and the check that it is

The reference is one page per verb family, in the order dispatch declares them, rendered
at build time from the emitted parser: the flags, what each takes, the defaults, and the
refusals the verb raises. A page built this way cannot describe a flag that was removed,
and it gains one in the commit that adds it.

PPortal's area does this with a component that reads the host's own flag list and
renders both its tables — nothing retyped, a rename landing in the docs in the commit
that renames. The shape is the same here, with the command invoked at build time rather
than a source file parsed.

What generation cannot supply is why a verb exists, which is most of what a reader came
for. So each page is a generated table under prose written once, the two kept apart:
regenerating never edits an argument, and editing an argument never touches a table.

That join needs a check. A build that quietly falls back to a committed copy publishes a
stale reference nobody sees, so the suite asserts the pages against the parser this
checkout declares. It is the property the gate already holds over the derived README
block, pointed at a second projection — which is also the answer to whether this belongs
in a build script or in the tests: both, for the same reason `lint` and `add` both hold
the line format.

### §RK1403 A page per finding code, for the reader arriving with an error

The gate names a code, and `explain` says what the class is, what produces it and which
doors close it. Both answers live in an installed copy, so the reader who needs them
most has the least: a person looking at a failed CI job, or at a hook that has just
denied a write, in a repository they have not adopted.

Pasted into a search engine, those strings resolve to nothing today. A page per code —
the class, what raises it, the command that closes it, and whether the mechanical pass
or `repair` reaches it — is the one part of this area whose reader arrives with an error
message rather than a question.

They come off the same table `explain` reads, for the reason the verb pages do: a code
added to the gate is documented in the commit that adds it, and one deleted stops being
documented rather than becoming a page about a check nobody runs.

What each page adds by hand is the situation. A code is a classification; what the
reader needs is the sentence naming the ordinary act that put them there — a textual
merge that doubled a heading, a vendored surface left behind by an upgrade, a section
deleted while a line still pointed at it. That sentence is written once per code and is
the half no read can derive.

### §RK1404 The configuration reference, rendered from the read that owns it

`roadkeep.toml` is the whole of the sixth law: prefix, id shape, paths, markers, limits,
budgets, claims, refs, requirements and the two opt-in tables. `config` answers every
question about it — each table, key, type and default, the sentence its source carries,
whether this project declared it, and what this build fixes and no project may set. It
answers from an installed copy on a configured tree, which is exactly what a reader
writing their first one does not have.

So the reference is that read rendered: every table in the order the file is written,
with the type, the default, what declares it, and the boundary between what is yours and
what is the build's — restated nowhere, because `config` publishes it and a page
repeating it is the third copy.

Two things only a person can write. The first is what a number is for: `[limits]` and
`[budgets]` hold judgements measured against a corpus, `govern` refuses one this corpus
already breaks, and `--because` stacks the argument above the key — so the page says the
number is measured and never recommends one. The second is a whole file for a project
adopting with a backlog already in it, which no read generates.

The worked example is this repository's own `roadkeep.toml`. It is the conformance
fixture, so it is the one configuration that is provably valid, and it is one fetch away
rather than transcribed.

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
