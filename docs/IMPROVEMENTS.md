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

### §RK348 The refusal that is about somebody else's line

Shipping RK325 was refused with `why: 173 characters, limit is 171: delete 2
characters`. Nothing about the call was over: the `--why` being written was 119. The
line at 173 was RK327's, which names RK325 as a dep — and `(deps: RK325)` becomes
`(deps: RK325 ✅)` when the ship re-derives it, two characters that leave the prose
budget two short.

The refusal is correct and unreadable. It names the field, the count and the limit, and
every one of those is about a line the caller is not editing and has no reason to be
looking at. What it reads as is *your sentence is too long*, so the author shortens the
one they just wrote, gets the same number back, and has to diff the file to find out
why.

The fact is in the transaction. `refresh` re-derives every dependent's annotation and
knows which line it was validating when the schema refused, so the id belongs in the
message — the same rule every other refusal here already keeps, which is that a length
is reported against `file:line` and never as a bare number.

Worth separating from the repair the author then needs. Trimming a dependent's `why` to
make room for a marker nobody typed is a real edit and a legitimate one; what is not
legitimate is discovering it by elimination. The design question is only whether the
annotation's growth should be *offered* — `--lines`-style — or simply named, and named
is the smaller answer.

### §RK349 One enrichment, four doors

RK312 taught `ref.missing` to name `anchors --block <x>` and the free address under it.
It is wired into `authoring.add`, around the one `place` call that command makes.

Every other write that validates a line reaches the same violation and gets the sentence
as it was. Measured while building RK327's fixture: `defer RK2` on a project whose store
declares `ref` refused with `ref: every task points at its rationale section`, naming
nothing — the exact text RK312 was filed against, one verb over. `resume` writes the
line back and validates it again, and `section add` reaches the same schema.

The asymmetry is worse than the original defect, because a caller who has met the good
refusal once now knows the tool can answer this and reads the bare one as *there is no
answer here*.

What makes it a small task is that the enrichment is already a function of a config and
a block: `_naming_the_anchor(config, block, error)` needs the block, and every door that
refuses a line has one — a `defer` reads it off the line it is moving, a `resume` off
the line it is writing back. So the repair is a shared wrapper at the seam every write
already passes rather than four call sites, which is what would otherwise drift.

Worth checking whether that seam is `place` itself. It has no `Config` today, which is
why RK312 went around it, and threading one in is the change that makes this one line.

### §RK350 The property the survey made and did not keep

RK339 gave `status` and `claim` a refusal naming their read-only near-twins, and found
the second pair by a one-off script: edit distance over the forty-one verbs, crossed
with whether each needs a positional. Exactly two pairs qualified.

That script is the whole finding and it was thrown away. The next verb added is measured
by nobody, so a third pair is found the way the first two were — by somebody typing the
report's name and reading `error: the following arguments are required`.

The shape to hold it in already exists one file over.
`test_every_module_is_named_in_the_layout_index` turned an index that silently stopped
being an index into a gate, on the argument that what held it was a habit; this is the
same argument about a list that grows the same way.

The property is decidable and narrow: for every pair of verbs within one edit where one
requires a positional and the other does not, the one that requires it declares a
`twin`. Both halves are read off the parsers — the distance from their names, the
requirement from their actions — so nothing here is a table to keep in step, which is
the trap `Prose` already avoided.

What it must not do is demand a sentence for every near-collision. `lint`/`list` and
`ship`/`show` are pairs where neither call fails in a way the other's name explains, and
a gate that asked for prose there would be answered with prose nobody needed.

## Block C — Query

## Block D — The gate

### §RK353 The name the skill teaches and the parser does not know

Two surfaces name one act differently on purpose. `scope` is the MCP tool for declaring
what a commit owns, and at the CLI that same act is `claim <id> --path …`, because there
`claim` without a path is the other act — taking a line. The skill says so.

What happens next was measured in this session: the skill was read, `roadkeep scope RK345
--path …` was typed, and argparse answered `invalid choice: 'scope'` followed by all forty
verbs. Nothing in that refusal names `claim --path`, and nothing distinguishes a name this
tool publishes elsewhere from a typo.

The same gap has been closed once already at the other end: RK333 is the refusal that
offers `mcp__roadkeep__add` under a name a plugin-provided server does not use. The
pattern is a route named for the surface the reader is not on, and the fix in both
directions is the same shape — the refusal knows the other surface's table and can say
which verb the name it was given belongs to.

Small in code and not in effect: a session that is refused a route it was taught either
retypes from memory or falls back to editing the file, which is the door the guard
denies and the whole reason these names are published at all. What is worth deciding is
whether the mapping lives with the tool table or with the parser, since only one of them
can be the authority on a name.

## Block E — Adoption

### §RK305 A majority that measures the backlog, not the file

RK288's guard is right about the alarm it silences and wrong about how it decides. It
prints `--ref-scheme <other>` only where the other scheme accounts for more headings
than the declared one — a proxy for *this file is really addressed the other way*.

The proxy holds on a static file. It does not hold here. This repository's rationale
file carries a permanent preamble anchored `0.1`-style and one `RK<n>` section per
**open** design, and a ship deletes the second kind. So the ratio falls with every task
delivered, and at the moment the open designs stop outnumbering the preamble the tool
tells a fully conforming file to be read the other way. Measured while shipping Block B:
five and five, one ship from the alarm, on a file reporting every heading conforming.

What the count cannot see is that the two kinds of heading are not competing readings of
one file. One is prose the project keeps and the other is a queue. A file whose declared
scheme parses **every** heading it was asked about has no minority reading to report,
whatever the ratio — which is the condition RK288 was actually written about, and the
one the majority was standing in for.

### §RK315 A fixture a second session can edit

This repository's docs are the conformance fixture on purpose, and
`test_a_file_that_mixes_anchors_is_not_told_to_switch` reads `docs/IMPROVEMENTS.md` from
the live checkout to assert that a file mixing both anchor shapes is not told to switch.
Measured across three runs of the same commit: one red, two green, with a concurrent
session shipping tasks into that file throughout — the ships delete id-anchored
sections, which is the ratio the assertion turns on.

A fixture git holds is a fixture any process in the checkout may rewrite, so this
failure names the scheduler rather than the code. The round-trip property tests read the
same tree and survive it, because they assert a property of whatever they read; this one
asserts a count. What needs deciding is whether the assertion belongs against a copy
taken at collection, or whether a count over a file the backlog erodes is the wrong
assertion whoever is writing it — RK305 already names that ratio as fragile.

### §RK347 The collision an estimate is taken to find

`adopt` exists so the commitment is priced before it is made: what parses, what
conforms, the longest field against its limit, the markers to declare. `--sections` is
that read for a rationale file, and it takes one path.

Which is right for every limit it reports and wrong for the one RK340 added. An address
is doubled only across two files, so a per-file estimate cannot see it by construction —
and this is the finding an adopting project meets most: measured in one,
`IMPROVEMENTS.md` and `STRATEGY.md` both open at `I` and both declare a `III`, which is
four `section.ambiguous` on the first run of the gate, against files the estimate had
called conforming.

The read exists: `history.doubled` answers it over the project, and `anchors` already
prints it. What is missing is that `adopt` asks — and that having asked, it names
`[refs]` as the declaration that makes the two sets two, which is a line of
configuration rather than a renumbering of somebody's document.

The estimate stays a read that writes nothing and exits 0 (RK18): what is added is a
figure in it, not a refusal. An adopter told the number before they commit is the whole
point of the command, and this is the one they are most likely to be surprised by.

### §RK351 The answer a running suite is not holding still for

`_answered` appends what RK79 and RK200 exist to say: which tree answered, and whether
the modules this process imported have moved on disk since. Both are right, and both are
part of the string a test reads back with `text_of`.

So the tests that assert on that string are asserting on a fact about the *repository*,
not about the call. Reproduced deliberately: `touch src/roadkeep/cli.py` three seconds
into `pytest tests/test_serving.py` fails a test that passes on a quiet tree, and the
diff is the note being added rather than any field changing. Observed first as two
failures in `test_serving.py` during a full run that overlapped a commit, both green in
isolation minutes later — which reads as flakiness and is not.

The cost is paid by the one workflow this tool is built for: an agent edits, runs the
suite in the background, keeps editing, and is handed a red that says nothing about the
change. A red that cannot be trusted is worse than no red, because the next one is
discounted too.

This is RK315's shape with a different input — that one is the governed docs being
written mid-run, this is the source files being touched — so whatever answers it should
answer both. What is worth deciding is where the seam goes: a test that reads the fields
it asserts on rather than the whole string, or a fixture that pins the staleness answer
for the duration of the call.

### §RK352 A fixture that collides with the environment it is about

`_drifted` compares a capture's recorded text-handling facts against this process's,
which is the whole of RK341: a verdict reached under different codecs says so. The test
for it records `PYTHONIOENCODING = utf-8:surrogateescape` and a locale, and asserts both
come back as drifted.

Both do — unless the process running the test already declares that variable with that
value, in which case only the locale drifts and the assertion fails. Measured here: the
PowerShell tool starts Python with exactly that value exported, so the suite is red
under one shell and green under another with no change to the code between them.

The fixture is asserting "this process does not have X" about a value chosen because it
is the realistic one, which is the same reason a real environment would have it. A value
nothing would ever export makes the same point about the comparison and cannot be shared
by accident; reading the current environment and picking one it does not hold is the
other direction, and says why in the test rather than in a constant.

Small, and worth doing because of what it costs when it fires: this is one of the few
tests that can be red for a reason outside the repository, and a red nobody can
reproduce is the one that gets ignored on the run where it means something.

## Block F — The plugin
