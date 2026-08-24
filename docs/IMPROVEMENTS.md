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

### §RK1322 RK1322

Measured on this repository, 2026-08-23: 47 of 148 Python files are CRLF in the working
copy and 101 are LF. `.gitattributes` pins what git stores (RK1132) and
`test_no_file_mixes_the_two_line_terminators` refuses a file holding both - so each file
is internally consistent and the tree is not.

The cost is paid by anything that appends. Three times in one session a heredoc added LF
to a CRLF test file and the invariant went red; each time the fix was rewriting the
whole file in the terminator it already had, which is a read nobody can make from the
file's name. The skill warns about heredocs into source (RK1091) for a different reason,
and this failure wears the same clothes.

git says so too, once per commit: `CRLF will be replaced by LF the next time Git touches
it`. A warning on every commit that touches a third of the source is one a reader learns
to skip, which is the state RK16 keeps findings out of.

Three shapes. A gate finding per file whose working copy disagrees with what
`.gitattributes` stores, which is the reading git already does and nobody surfaces; a
normalising pass in `--fix`, which is derived and therefore its kind of repair; or a
read that answers which terminator a path has, so an append asks instead of guessing.

Falsified if `core.autocrlf` explains the split, which would make it a checkout setting
and not a fact about the tree.

### §RK1323 RK1323

`agents.md` states it as a law: this repository's own `docs/` is the conformance
fixture, and `roadkeep lint` must pass on it, because the format is proven by the
artefact and not asserted in a README. A limit these lines cannot express is the wrong
limit rather than a set of wrong lines.

`[criteria]` is outside that proof. `criterion list` here answers *no [criteria] in this
project's roadkeep.toml, so what finishes a block is ungoverned*, so every `brief` this
project makes prints an empty `done_when` and RK1300's event - the criteria arriving
with the word `finished` - has never fired on the corpus it was built against. Two
blocks closed in this session and neither carried a list to print.

RK1313 sharpened it: `init` now writes the table empty into every new project, so the
shape a fresh adopter starts from is one the tool's own fixture does not have. That is
the asymmetry, and it is the one RK66 argued the other way round - a schema applied to
prose nobody wrote to it reports on adoption.

The work is not the declaration. It is writing what would finish each open block, which
is a judgement about the plan and not a config edit, and the reason this is a line
rather than a commit.

Falsified if the criteria a block would carry are already stated somewhere the gate
reads, which would make this a duplication rather than a gap.

## Block E — Adoption

## Block F — The plugin

### §RK1325 RK1325

Measured 2026-08-23 on a tree `roadkeep init` had just made - no `.claude`, no
`.mcp.json`, nothing wired. `served_by` answered `mcp__plugin_roadkeep_roadkeep__` for
it, and `mcp__roadkeep__` for this repository, which does declare one. So every door in
that project's payload carries a `call` naming a tool that project has nothing to answer
with.

RK449 states the rule the other way: where nothing serves the door, only the argv is
published. The fallback makes *nothing serves it* unreachable - a root with no
declaration inherits whatever the running environment has, and the payload then asserts
about the project what is true about the machine.

Both readings are defensible and that is the decision. `served_by` takes a root and
reads `.mcp.json` under it, which is a question about the project; its docstring says
*the prefix this session's tools arrive under*, which is a question about the process.
They agree on every wired project and part company on an unwired one, which is exactly
the adopter this tool ships for.

It also cost a test. An equality over a ship's event had to stop comparing the door
whole, because whether `call` is present depends on the machine the suite runs on.

Falsified if a served caller can act on a project other than the server's own, which
would make the prefix right and the root the wrong argument.

### §RK1326 RK1325

Measured 2026-08-23 on a tree `roadkeep init` had just made - no `.claude`, no
`.mcp.json`, nothing wired. `served_by(root)` answered
`mcp__plugin_roadkeep_roadkeep__`, and this repository, which does declare one, answered
`mcp__roadkeep__`. So the fresh project was handed the prefix of a plugin it has no
relationship with, and every door in its payloads carries a `call` naming a tool that
cannot act on it.

RK449 states the rule the other way: where nothing serves a door, only the argv is
published. That is exactly the state here, and the fallback answers anyway.

Two readings, and they are not the same question. *Which surface serves this session* is
a fact about the process, and the fallback is right about it: a caller inside a plugin
session does reach these tools. *Which surface serves this project* is a fact about the
root that was passed, and it is the question the argument makes it look like. Everything
downstream reads it as the second - the door is published beside a project's own answer,
and a client runs what it names.

The fix is to decide which one the argument asks, and where it is the project's, to
answer nothing when the project declares nothing.

Falsified if a served call reaches whatever project the caller names, which would make
the prefix right and the reading a misunderstanding of the transport.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1321 RK1321

Measured this session, twice. RK1305 added a seventh subject and `budget` reached 2,744
against a per-tool ceiling of 2,600 - overtaking `ship` at 2,466, the tool that number
was calibrated against. RK1310 then added a 65th verb and the whole surface reached
64,190 against 63,500. Both ceilings were re-argued rather than met, and both arguments
were about the same tool.

The ceiling is doing its job: `roadkeep.toml` says it is set close enough that a
description growing by a paragraph is a finding rather than a rounding, and it found
this. What it found is not a description that grew. `budget` answers about a line, a
section body, a non-goal, an every-turn file, the tool list, a session, a brief and a
retirement - eight questions under one name, where every other served tool answers one.
A per-tool limit is refused by the tool whose description somebody just edited (RK1059),
and this one is refused by whichever subject was added last, which is the property that
argument rejected for a total.

There is a seam. Four of the subjects price prose a write is measured against; three
price what a surface costs a session. `budget --tools`, `--session` and `--brief` share
a reader and share nothing with `--block`.

Falsified if splitting leaves either half still the largest tool, which would make this
a name and not a bundle.

### §RK1324 RK1324

Measured on this repository, 2026-08-23, by grepping the writers: `remedy` at five
sites, `door` at three, `doors` at two, `clauses` at one. Every one is the same fact - a
command this answer says the caller may run next - and a consumer wanting *what can I
run* has to know all four names and which verb uses which.

RK1307 closed half of it. Its gate asserts that a command a verb's text offers is
reachable in that verb's payload, which is about presence; nothing says the key is the
same key. So the class came out consistent in content and four ways apart in shape, and
the next verb to grow a door picks a fifth name for the reason the first four did.

The shapes differ too, not only the names. `lint` carries a `Remedy` with a kind and a
decision, a finding being able to offer a choice; `Partial` carries a list, a
half-written state having two next steps; the event carries one object; `brief`'s
`clauses` are costs rather than calls and are arguably not this class - which is itself
the question, because the name does not say.

One name and one shape for a runnable command, wherever a payload publishes one, would
let a client write that reader once. What the plural is for, and whether a cost is a
door, decide it.

Falsified if the four are four different facts, which would make one name the conflation
rather than the fix.
