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

### §RK294 A mechanism reached only by advice

RK280 gave a claim the paths its commit owns and gave `claim <id>` the read that names
what the tree holds for somebody else. What it did not give is a caller. The declaration
is asked for in `agents.md` and in the skill, which is the same sentence the finding
itself quoted as failing: advice about what to do at the moment of committing, where the
analysis is expensive and the author is already finishing.

`ship` is that moment. It runs when the work is validated, its answer is already the
three edits it made, and it holds the id — so it can ask the registry the one question a
departing task has: what does this tree hold that no claim of mine names. Reported and
never refused, for the reason `_drop_section` keeps a section it does not own: a loose
path is a legitimate state (a scope nobody declared is every project that has not
adopted this) and a ship that failed over one would be an obstacle at the one moment the
author cannot route around it.

What it must not do is derive the scope. A ship that filed the dirty paths under the
departing id would be answering the question the incident asked — which of these is mine
— by assuming the answer, and the two sessions it exists to separate would each get the
other's files with the tool's signature on it.

### §RK295 A declared path nothing will stage

Verbatim is the right rule and the reason RK280 gives for it stands: a scope inferred
from a sentence would be RK55's guessing put in charge of what a commit contains, and a
path declared before the file exists is the ordinary case — the test is written after
the claim is taken.

So this is not a refusal. It is the one comparison the read already has the facts for
and does not make: `claim <id>` prints `mine` out of the registry and `loose` out of
`git status`, and a path in `mine` that is in neither the dirty set nor the index is a
path staging nothing. Today it prints as an ordinary line of the answer, and the real
file — the one whose name was mistyped — prints two lines below under `loose`, where the
eye reads it as somebody else's.

What makes it worth a column rather than a refusal is when it is wrong: a scope declared
ahead of the work names files that do not exist yet, and every one of them is correct.
So the reading is not *this path is missing* but *this path stages nothing right now*,
which is a fact about the tree at the moment of asking and not a judgement about the
declaration.

### §RK296 The half of RK257 that was left

Stated plainly because it was a choice and not an oversight: RK257 named three missing
things and this shipped two of them. The file the labels came from and the `block add`
that opens the heading are now in the sentence; the labels themselves are still all of
them.

The list is load-bearing exactly once — when the label really was mangled, which is the
incident RK216 was filed from, and there the neighbours are what makes the mistake
visible. That is also the case `shading` already answers by name: it names the labels
that share a prefix, which is the subset a confused author needs. Where nothing shades,
the remaining labels are a set the author is not choosing from.

So the shape is not a cap on the list but a question about when it is printed at all.
What must not happen is the answer that reads well and helps nobody: an elision (`A, AA,
AB, … and 87 more`) keeps the length and loses the one label that would have settled it,
which is RK68's argument about a bounded list read as the whole one.

## Block C — Query

### §RK265 The pointer budget cannot be told about

`budget` derives every number from the id, the marker, the deps and the pointer — all known before the
first word exists. Under `ref_scheme = "id"` that holds: the pointer is derived, and roadkeep's own
backlog counts 40 characters of structure against 320. Under `ref_scheme = "outline"` the pointer is
*chosen by the author*, `budget` has no flag to be told it, and it counts the structure as if the line
carried none — 30 against the same 320.

Measured in a repository that uses the outline scheme: `budget --block AI --symptom
'…108 chars…'` answered `why 182 of 200`. The `add` that followed, identical but for
`--ref XX.2`, refused at 188 characters against a limit of 174. The difference is
exactly ` → §XX.2`, eight characters, and the refusal costs the author a second
composition of the same sentence — which is the whole of what `budget` is for: "a limit
reported after the prose exists is a limit discovered too late to save the tokens it was
meant to save."

The shape of the fix is the flag `add` already takes. `budget --ref` under the outline
scheme, counted into the structure the same way the derived pointer is; and with no
`--ref` given, the honest answer is not the pointerless one — either the widest anchor
the file already holds, or a stated assumption, so a number that cannot be exact is at
least never optimistic.

### §RK283 The one line budget speaks for

`budget`'s own docstring states the principle: every number is derived from what is
known before the first word exists, "so the budget is a fact about the line you are
about to write rather than a verdict on one you already wrote". It is served for the
task line, and for nothing else.

Two other writes carry prose limits, both larger than the line's. `non-goal add --why`
is capped by `[non_goals]`; `section add` and `section amend` cap the body in words.
Measured against Shio on 2026-08-04, filing four tasks after a block emptied: the
non-goal took two refusals — 286 characters, then 234, against 200 — and the section
amend one, 366 words against 300. Each refusal is precise and arrives after the body
exists, which is the cost this verb exists to save, and it is larger here because a
section body is the longest thing an author writes. This section was itself refused
twice before landing, which is the report and its evidence at once.

The shape is the same: both limits are facts about the file and the role, known before a
word. `budget --non-goal` answers one; `budget <anchor>`, the way `budget <id>` already
answers for a line, answers the other — and an amend is where it matters, since there
the author has a body in hand to fit inside a number nobody has stated.

What this is not is a `--dry-run` on the write verbs. The point is to be answerable
*before* the prose.

### §RK287 Two numbers, one of them printed

Measured in Claude Code Tray, whose `[limits] section = 300`. `section amend XXV --body
…` replaced a two-line intro and reported `310 words`; `section show XXV --json` says
the same. That section's own prose is 48 words. The other 262 are `§XXV.3`, a subsection
written by `section add`, which the same run had reported at 255 on its own.

`lint` is clean, and it is right to be: the limit is measured on a section's own prose,
which is what makes a file of many small sections the shape the limit exists to
encourage. So the two verbs an author reads *while writing* state a number the gate does
not use, and they state it beside a limit it appears to breach. The move it invites is
to cut prose that was never over — or, on a parent genuinely over with short
subsections, to trust a figure that happens to pass.

Both figures are wanted: what the section costs a reader is the subtree, what the limit
weighs is its own prose. `budget` has the same shape and RK283 is already about what
that one leaves out, so the answer is a phrasing these verbs share — `48 words, 310 with
subsections (limit 300)` — rather than a choice between them. The rule underneath is the
one RK245 and RK265 each found separately: a verb printing a number beside a limit is
claiming the two are the same number.

### §RK293 The next family, which is the one question the listing does not answer

`anchors` was the answer to *which number may a reopened family take*, and it answers it
well: live addresses, retired ones with the commit that spent them, and `next §XX.31`
per family. Adopted in Claude Code Tray on 2026-08-04 it stopped an `add --ref XX.10`
that would have re-pointed history at a new section, and named the free address in the
refusal.

The question one line up has no answer. `IMPROVEMENTS.md` numbers one §I… sequence and a
block reused after its family shipped needs a *new* top-level — that is the normal case
in a backlog organised by theme, not an edge one. Nothing prints which top-level is
free, and the listing cannot be read for it either: the families come out sorted as
strings, so `IX` follows `IV` and precedes `V`, and the last row is not the maximum. The
number was guessed from the tail of 46 rows and happened to be right.

Two lines of output, both derived from what the command already walked: the next free
top-level beside the header's totals, and the family rows in numeral order so a reader
can check it. The second matters on its own — a listing ordered by a numeral's spelling
is one nobody can scan for a gap, which is the other question anchors gets asked.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK267 A note that knows more than it says

RK155 made the MCP server say when its own modules moved after it imported them, because
a config key added in one commit made every write refuse `unknown key` while the CLI
accepted it. The note works. What it does with the relevance question is hand it back:
it lists every module `Engine.stale` found and closes with "re-run only where the
changed files are the ones that would decide this", which is the reader being asked to
know the call graph of a refusal they did not raise.

Measured while shipping RK255: a `why.too-long` refusal — decided by `schema.py`,
unchanged — arrived naming `cli.py`, `merging.py` and `provenance.py`, three modules
that could not have decided it. The note was 450 characters of correct and irrelevant
text on a refusal that had already said everything actionable in one line, and it fires
on every error in every session that edits this package, which is every session that
develops it.

The module that raised the refusal is knowable: the exception has a traceback, and the
frames above the server are this package's. Intersecting that with `Engine.stale` turns
the note from an inventory into a judgement — say nothing when the sets are disjoint,
and say which module when they are not. The risk is a refusal raised in one module
because a helper in another changed, which the intersection misses; that argues for
narrowing the sentence rather than suppressing it, and for keeping the full list behind
the one module that is named.

### §RK275 A check the agent it was built for cannot call

L5 is that every question is a command, so answering one costs no context. `merge
--check` is exactly that shape: it writes nothing, reads two facts, answers in three
lines. The MCP server exposes the query surface — `list`, `brief`, `budget`, `deps`,
`weight` — and not this one, so the agent the plugin exists for reaches it by shelling
out or not at all. In practice, not at all: nothing prompts the question, and an unwired
driver is silent until the merge it was registered for.

The reason it is absent is that `merge` is git's driver contract. Three positional
paths, a `--path`, an exit code git reads — none of that belongs in a tool an agent
calls, and the server was right to leave the verb alone. But `--check` is not that verb
sharing a name; it is a different command wearing the same subparser, which is why it
needed a flag.

The shape to decide: whether the server grows a tool for a flag — one subparser per task
is the mapping, and this the first exception — or whether `--check` becomes its own
subcommand, `merge check`, picked up by the rule the server has.

The second was argued for as cheap "before it is load-bearing". It no longer is: RK272,
RK273, RK274, RK277 and RK278 each put behaviour behind that flag, so the rename moves a
documented command with five decisions in it. Not an argument against — the measure of
what an exception would hold.
