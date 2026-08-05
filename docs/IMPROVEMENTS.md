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

### §RK361 The fourth caller of place, refusing into the dark

RK348 and RK349 both landed the same rule from opposite ends: a length is reported
against `file:line`, and a refusal names the command that answers it. `place` is where
three of the four line writes now get both — `add`, `defer` and `resume` each pass
`where` and a config.

`merging.merged` is the fourth and passes neither. A line one branch added and the other
did not is re-placed there, and every refusal that reach produces arrives naked: an
over-length line says a number, an undeclared block lists labels with no file beside
them, and the caller is in the middle of a merge with two versions of the file and no
statement of which one the number is about.

The comment above that call argues nothing can arrive wrong — every version was held to
the round-trip, so the bytes are the ones already checked. That is true of the
*rendering* and not of the schema: an annotation this tool re-derives during the merge
is exactly the two characters RK348 was filed about, and the branch that shipped a dep
is the branch that makes them appear.

Cheap, because both arguments are already in hand at that call. What wants deciding is
only whether the merge driver should also carry the anchor clause, or whether a merge is
the one context where naming a command to run is wrong — the caller is inside git's
driver, not at a prompt, and an instruction they cannot follow yet is noise.

### §RK362 A declaration is not a delivery

RK350 closed the half that was a habit: which verbs owe a near-twin sentence is now read
off the parsers, so a third pair is named by a failing test rather than by whoever types
the report's name.

It gates the `twin` default and stops there. Whether that default ever becomes output is
`_Verb.error`, which fires on `"required" in message` — a substring test against the
sentence argparse composes, in argparse's English. Both live pairs have a test that runs
the bare call and reads the printed text, so delivery is held for `status` and `claim`
by two tests naming them. A pair added tomorrow inherits the property and neither of
those.

Two ways that goes wrong and only one is exotic. The dull one: a verb whose required
positional is declared with `nargs` the survey counts and the message words differently,
so the gate is satisfied and the caller still reads argparse's own line. The other: a
Python release rewording that message, which turns the sentence off for every pair at
once and leaves a suite of green tests asserting the defaults are declared.

The shape is the one already here — the property that enumerates the pairs can run each
of them bare and assert the sentence arrives, which makes the enumeration answer both
halves. What wants care is that it must not become a second copy of the two hand-written
tests: those assert *which* sentence, and this one asserts only that one was printed.

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

### §RK358 A fixture that forbids the state the workflow is in

The suite asserts that a `pick` over this repository's own roadmap comes back at
`Tier.LOWEST`. That holds on a quiet backlog and on an empty one, and it is false for
exactly as long as a task is being worked on: `claim` and `status <id> 🛠` put a line in
progress, `pick` then answers `Tier.STARTED` because finishing what is started is the
tier above lowest-ready, and the assertion names the tier below it.

Observed twice while shipping Block E, once per task. The workflow this repository
documents is one task per commit, taken by claiming the line — so the window where the
assertion is false is the window where work happens, and the runs that pass are the ones
made between tasks. That is RK315 and RK351's shape a third time: a red about the state
of the checkout rather than about the code, on a suite an agent runs in the background
while it edits.

What is worth deciding is whether the tier belongs in the claim at all. The two facts
under it are that this backlog is pickable and that the chosen line's pointer is its own
id, and both survive a claim; the tier is the one field encoding an assumption about who
is working right now. A branch on `Tier.STARTED` would keep it and say so, which is the
smaller answer if the tier is worth asserting.

### §RK359 The collision the estimate can see, and the one it cannot

RK347 gave `adopt --sections` the finding a per-file read cannot make: an address two
prose files both declare, named with the files and the `[refs]` line that ends it. It is
answered off `config`, so it fires where the target is one of this project's own files
and is silent everywhere else — which is right, because `[files]` otherwise names
somebody else's siblings (RK292).

That leaves the shape the command is for. An adopter runs `adopt` from outside the
project, against a file no `roadkeep.toml` declares, and there are two of them:
`IMPROVEMENTS.md` and `STRATEGY.md`, both opening at `I`. The estimate reads one, calls
it conforming, and the collision arrives on the first `lint` after the config is written
— which is the one moment RK18 says the number is worth nothing, because the commitment
is already made.

The read is the same read; what is missing is a way to say which files to take it over.
A second positional, or a `--with <path>` repeated, keeps the estimate a read that
writes nothing and exits 0, and keeps one path meaning one file for every other measure
in the report. What must not happen is inferring the sibling from the directory: a
`DESIGN.md` beside an `IMPROVEMENTS.md` is a guess about somebody's layout, and the
report would then be measuring a set the caller never named.

## Block F — The plugin
