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

### §RK354 A finding about a file nobody was told was read

`Report.checked` is printed even on a clean run, and the argument for it is in
`linting`'s own docstring: a gate that passed by reading nothing looks exactly like a
gate that passed. RK326 put a finding outside that list.

The queue is read from the roadmap where a heading declares one and from `roadkeep.toml`
where none does — the second being where the defect was measured — so there the
finding's `file` is the config. Measured on a scratch project: `checked` is
`('ROADMAP.md', 'CHANGELOG.md')`, the finding names `roadkeep.toml`, and the summary
reads `1 problem(s) in 1 line(s) across 2 file(s)`. A reader counting files against
findings is told two things that cannot both be true, and the sort in `_examine` puts
anything not in `checked` last by falling off the end of the index, which is right by
accident.

Two shapes, and the choice is what `checked` means. If it is *every file this run read*,
the config belongs in it always — and then a project with no queue names a file no
finding can be about. If it is *every file this gate judges*, it belongs there only
where it declared the queue, which is the one thing about that file this gate has an
opinion on.

Neither is free: the first widens a list that is a promise about coverage, and the
second makes membership conditional on a config key.

### §RK355 The list of derived repairs, stated four times

RK16's split is the tool's most-repeated sentence: `--fix` repairs *annotation, pointer,
dep order, marker codepoint, whitespace* and leaves the editorial. It is written in
`fixing`'s docstring, in `agents.md`, in the shipped skill, and in `guarding.Review` —
the one an agent actually reads, because the `Stop` hook prints it at the moment a
governed file has drifted.

RK328 added a sixth repair and moved three of the four. The fourth still says five, and
nothing went red: no test compares that sentence to anything, so the copy with the most
readers is the copy with no gate.

This is the family RK30 and RK104 already answered twice, in the same shape both times —
a claim in prose is a claim that goes stale, so the sentence moves into something that
fails. Here the fact is derivable: `fixing` knows which reasons it can write, because it
writes them, and every one of them is a literal in that module.

What needs deciding is which end holds it. A `reasons()` the fixer exports and the four
copies quote is one answer and makes `guarding` import `fixing`, which RK260 spent
milliseconds getting out of the hook's path. A test that reads the four files and
compares them to each other holds the same invariant, costs the hook nothing, and is a
fifth reader of a list that already has four.

### §RK356 A pin that ages without saying so

RK335 traded a channel for a number, and the trade is stated in the workflow: what a
merge was gated by is now a fact somebody can read off the file months later, and the
cost is that the validator drifts behind what an installing user runs. That cost was
accepted knowingly and has no signal attached to it.

The failure it leaves is quiet in the direction that matters. A payload defect the newer
validator reports and the pinned one does not is a release that goes out green, and the
first reader to meet it is an adopter whose session loads the plugin — which is the
audience RK334 bought this job for in the first place.

Three shapes, none obviously right. A second job on the *unpinned* channel, allowed to
fail without blocking, turns the drift into a red somebody sees while keeping the merge
gated by the pin; it costs a job and a convention about which reds block. A scheduled
run of the same job asks the same question daily rather than per push, and puts a
network call on a clock this repository does not otherwise keep. Or nothing at all, and
the pin is raised whenever somebody notices — which is what `stable` was, with the
number written down.

What makes this an idea rather than a task: which of the three is right depends on
whether this repository wants a red that nobody is required to act on.

### §RK357 An address that stopped resolving when the line left

Every other repair `--fix` makes replaces a line in place, so `file:line` in the report
is still the line that was repaired after the file is written. RK328's is the exception:
the line is gone, and every line under it has moved up one.

Measured on the fixture that holds it. A queue of `- RK1`, `- RK2`, `- RK9` with RK1
shipped reports `ROADMAP.md:7  fixed  RK1: queued work that shipped`, and line 7 of the
file the pass just wrote is `- RK2` — an entry the run did not touch, under an address
that names the one it did. A second drop in the same pass compounds it, the linenos
being read before any removal.

Reporting the position *before* the write is deliberate and is not the defect: the
reader who wants to see what was taken has the file as it was, in git, at that line.
What is missing is anything saying which file the address is about, so the two readings
— the tree before the pass, and the tree after it — are indistinguishable in a line that
a terminal renders as a link.

What is worth deciding is whether a removal is a third kind of report beside `Repair`
and `Skipped`, or whether the same shape carries a field saying the line is gone. The
first makes `--json` carry three lists where a consumer reads one; the second is a
boolean every reader has to know to check.

## Block E — Adoption

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
