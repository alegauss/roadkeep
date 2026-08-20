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

### §RK1267 Where the durable half of a deleted design goes

RK310 opened this door and stopped at the stale half: `--superseded-design` records that
a deleted design was *wrong*, and nothing records where the part that was right went.

The deletion is correct and the measurement behind it stands — a rationale file reaching
539 KB one honest paragraph at a time is what this tool exists to refuse. What is wrong
is that it is untyped. A section holds three contents with three half-lives: the
investigation, which dies with the ship; the criterion, which becomes a test; and the
decision, the constraint that has to stay true after the code moves. `ship` treats all
three alike.

The cost is measured here rather than supposed. RK1265 records a definition of done
written as a rationale section, deleted correctly, surviving in zero places — and the
block it governed was then closed and reopened six times.

This repository's own answer is the module docstring, which cannot drift from the code
it sits above. Nothing asks for it and nothing checks it. `--recorded-in <path>` is that
trace, appended to the ledger's sentence beside RK310's and for RK310's reason — the
entry is where the address and the outcome already meet — and refused on a path this
repository does not have, as every other path a ledger sentence names already is.

Not an archive: a flag that copied the section into a second file is the 539 KB with
better manners.

### §RK1268 A definition of done, addressed to the task

`criteria` addresses the pair (block, lead) on purpose: a criterion is about a body of
work, and a flat list would make finished a property of the backlog. That argument holds
and this does not overturn it — it adds the other unit.

The unit an agent executes is the task. What it wants before writing code is the spec:
the problem, what is out of scope, what must be true when it is done, and how that is
checked. Three of those four are here — the `symptom`, `non-goal list` and the design
section — and the fourth is per block.

Half of it already exists per task, and it is the half nobody can check off by reading:
`evidence <id>` runs a fenced query the design declares and counts the sites that must
exist. So the executable claim is per task while the readable one is per block, which is
the wrong way round — the checkable sentence is the cheap one to write and the one a
reviewer reads.

The address becomes the pair with an id in it, under the rule the list already has: a
lead is unique inside its own list. `brief` prints the block's list today, so the task's
own sits beside it and a task started that way never asks twice. It still binds nothing
— presence, not enforcement — because whether the work satisfies a sentence is a
judgement this tool has no model for (L4).

### §RK1269 The decisions role — an ADR is this format already

Adopters ask for ADR by name, and read as this format an ADR is the pair already written
here: an id, a marker, one falsifiable claim, a `why`, and a section carrying the
argument. `retire --superseded-by` is its Superseded-by, built and shipped. The only
difference is the departure — a roadmap line leaves by three doors and a decision leaves
by one, so nothing is ever deleted and the file grows only by decisions somebody
actually made.

So this is a role and not a second grammar. RK1064 made a role's shape declarable, RK340
gives a prose file its own namespace, sections already carry the word budget, the
round-trip and the pointer check, and `declare` retrofits a role a scaffold left out.
What it costs is `ROLES` in `config.py` being a closed tuple that every reader of a role
reads.

Keep it named, and do not open that tuple to any word an adopter types: a role no
machinery knows is a file with no schema, which is the convention this tool exists to
replace.

`ship --decides` is the door that files into it — one line, under the same limits,
written at the moment the section is deleted and by the one reader who knows what
survived it. Never the section copied whole.

And it is priced: every verb costs the session at connect, so the read surface stays
`show` and `brief` rather than a second query family.

## Block C — Query

### §RK1270 The config's shape, printed by the parser that enforces it

`_TOP_KEYS`, `_LIMIT_KEYS`, `_MARKER_KEYS` and six more frozensets are the complete
statement of what this file may say, and their only reader is `_reject_unknown`. That is
enough to refuse a typo and not enough to answer the question asked before anything is
typed: what may go here, and what does it mean.

Every consumer needing that answer has so far written it again. The scaffold `init`
emits knows the tables; `declare` knows `[files]`; a completion list in an editor would
know all of them. Each copy is L6 broken from a different side — the shape of a
project's own declaration decided somewhere other than the package that reads it.

So the package prints it, once. One payload per key: its table, its type, its default,
whether this project declared it, and the sentence already attached to the frozenset as
a `#:` comment — harvested from the source, never restated beside it.

What this is not is a schema for somebody else's validator. The shape published is what
*this build* accepts, and that is the distinction `ConfigError`'s skew clause exists
for: a key nothing declared is a typo, a key this build predates is an upgrade, and the
file cannot tell them apart. A payload naming the build that answered lets a reader
conclude the second one — the sentence that refusal wanted and had no way to reach.

## Block D — The gate

## Block E — Adoption

### §RK1272 A verb for the tables only a hand has ever written

`declare` retrofits a role into `[files]` and `priority migrate` moves the queue out of
the config; every other table is edited by hand. In an agent session that is not a hand
edit, it is no edit at all — the write path is the served surface, and nothing on it
writes this file.

The tables worth a verb are the ones whose value is a judgement about a number:
`[limits]`, `[budgets]`, `[tools]`, `[claims]`. Each already has the read that decides
it. `budget --file` prints what an every-turn file costs against what it may; `budget
--tools` ranks the served descriptions and prints the room; the P90 of the lines that
already read well is what put `symptom` at 120. The reading and the number live in
different places, so the reading happens once and the number is defended in a comment
afterwards — this project's own `[tools]` entry is four paragraphs of exactly that,
re-argued three times in one session.

So the verb prints the reading and takes the number in the same call, and refuses one
the current corpus already violates rather than writing a limit whose first act is a
finding. It writes the declaration and never the argument for it: why 120 and not 130 is
prose, and the tool does not write prose.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

### §RK1271 Completion in the config file, carrying no rule

The host states the property this may not break: it carries no rule, and
`tests/test_editor.py` holds it — a literal marker, id or governed filename in
JavaScript is L6 broken from the outside rather than the inside. A completion list
written as a schema under `editor/` is exactly that, and the widest one yet: nine
frozensets restated in a language the parser never reads.

RK1270 is therefore the whole design, and this is the rendering. A
`CompletionItemProvider` and a `HoverProvider` over the config file, both reading the
one payload, cached until the file changes like every other read the host makes.

The gate half already works and needs nothing built: the config is in `lint`'s checked
list, its findings carry `file:line:column` and the door that closes them, and the
diagnostic and quick-fix providers are registered for any file the gate names. What is
absent is the half before the save.

Which is the write prompt's argument met one file over: a view that only reads sends its
user somewhere else to type the format from memory, and that is the failure this project
is about moved one window across. The saving is the analysis — which key it was,
answered before a line exists, costs nothing; answered by the gate afterwards it costs
the edit twice.

## Block H — The tool's own shape (what one verb costs to change)
