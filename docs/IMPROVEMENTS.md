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

### §RK454 The repair that is claimed and never made

RK451 reads a governed file whose every byte is NUL as one finding naming the restore. A
file where *some* blocks reached the disk is the likelier shape on a large one, and it
falls through to the character pass. Measured on a 505-byte roadmap holding one good
line and 400 trailing NULs:

    ROADMAP.md:6:400  char.invisible  U+0000 unnamed control character at column 400 …
    400 problem(s) … 400 of them need no decision: … lint --fix

Two things are wrong and the second is the loop. The diagnosis is wrong in kind: RK118
wrote every byte of a governed file and none was ever a NUL, so a NUL is a lost write
rather than a character somebody typed — the same fact RK451 acts on, one file shape
over. And the remedy is claimed and not made: `--fix` counts all 400 as needing no
decision, writes nothing, and the next run prints the identical report. A caller that
trusts the sentence runs it forever.

The `_voided` predicate is the wrong shape to extend, because this file *is* text — most
of it parses. What the check has to ask is whether the file holds a NUL at all, and then
say which lines the loss reached rather than which columns.

Open: whether the finding replaces the character pass for that file, as RK451 does, or
sits beside it. Some of those lines are readable and their other defects are real, and a
report that hides them has answered a different question than the one asked.

### §RK455 A stream this tool did not open

`main` hardens the three standard streams before argparse sees a token, and
`provenance.STARTUP_CODECS` records what they were (RK341): stdin strict, stdout and
stderr backslashreplace. A text stream that has already been read refuses `reconfigure`,
and the refusal is a raise — `io.UnsupportedOperation` out of `_force_utf8`, with the
verb never reached.

Measured: `pytest -n 8` over this suite fails between nine and sixteen tests, every one
of them out of that line and none of them about what it asserts. An xdist worker is
bootstrapped over its own stdin, so fd 0 arrives read, and every in-process `main(...)`
scheduled there dies before parsing. That is a test runner finding a product defect
rather than owning one: a stream this tool did not open is a stream it cannot assume it
may re-encode, and the same shape reaches any host that embeds the CLI.

What the repair must not become is a bare pass. `errors="strict"` on the way in is what
keeps input that is not UTF-8 refused rather than repaired, because a substituted
character round-trips into a governed file and stays (L3) — a stdin that silently keeps
cp1252 is that defect with no report. So the answer states which stream could not be
hardened and what the caller loses by it, and never assumes the strictness it failed to
apply.

The suite's own half is separate and smaller: a fixture handing each test a stdin
nothing has read makes the fact local to the test instead of to the runner.

### §RK456 One repository, eleven ways to build it

Eleven test files build a git repository per test, each from its own copy of the helper:
`init --quiet`, then three `config` calls, then `add`, `commit`, `rev-parse`. Seven
processes, measured at 214 ms per repository here — 47 ms for `init` and 20 ms for each
`config`, which is what a process costs on this platform.

Four of the seven are avoidable without moving a single assertion. Identity belongs in
the environment (`GIT_AUTHOR_*`, `GIT_COMMITTER_*`), signing in a `-c
commit.gpgsign=false` on the one call that commits, and `GIT_CONFIG_GLOBAL` and
`GIT_CONFIG_SYSTEM` pointed at nothing make the fixture independent of whatever this
machine's user configuration says — which is hermeticity and not only speed, since a
global `commit.gpgsign` or `init.defaultBranch` is a fact these tests currently inherit.
Measured that way: 161 ms per repository, a quarter off, over the three hundred-odd
tests that build one.

The copies are the other half, and the one this project already has a rule about.
`Schema.render` is the only writer of a line for the same reason a fixture should have
one author: the divergence is already there — `test_history` clones and moves files,
`test_weighing` only ships — so a change to how a test repository is built is a change
eleven files have to agree to make, and the suite's shared facts already live in
`tests/conftest.py`.

### §RK457 The run is what stands between an edit and knowing

A full run is 2865 tests in 5m07s here, paid before an edit is known to hold — and paid
again by an agent that edits, runs and edits.

The time is not one hot spot. Of the 300 s the durations report, 272 s is `call` and 28
s is `setup`, spread over a long tail: `test_history` 50 s, `test_baseline` 29 s,
`test_sections` 20 s, `test_weighing` 20 s. What that tail is made of is process spawns
and filesystem work — git, nested pytest runs, tmp trees — which is what parallelism
answers and what a faster assertion does not.

Measured on this machine, 28 cores, with RK455 fixed: `-n 16` finishes green in 48-70 s,
and `-n 8 --dist loadfile` in 1m47s. Five to six times, and three even under the
conservative distribution.

`pytest-xdist` is a dev dependency, and the zero-dependency law is about runtime: a tool
run as `uvx roadkeep` in someone else's CI pays for what it imports, not for what its
own suite installs. The fixtures already survive it — `checkout` fingerprints and
`governed` copies at each worker's conftest import, so every worker asserts about one
coherent revision, which is what RK263 and RK315 asked for.

What is left to decide is the default distribution, and RK458 is why that is a decision
rather than a flag.

### §RK458 An order nobody chose is holding a test up

Under `-n 16` with xdist's default distribution,
`test_a_pointer_another_prose_role_answers_asks_for_nothing` failed once in five runs.
It passes alone, passes with its own file, and passes under `--dist loadfile` — which is
the shape of a test reading state that another file's test left behind, since only the
default distribution interleaves tests from two files inside one worker.

It is worth an id rather than a workaround, because the coupling is there whether or not
anything runs in parallel. The serial suite passes for a reason nobody has stated, so
the day a file is renamed, a test is inserted, or a run is randomised, the same red
arrives with nothing to blame it on — and the report will name a test whose own
assertion is about none of it, which is the failure mode RK263, RK315 and RK351 each
answered once already.

This project's answer to that class is an inventory rather than a call site: `VOLATILE`
names the caches an autouse fixture clears and states why the others are cleared for
nothing (RK268), and the staleness baseline is pinned per test (RK351). So the finding
is a seventh cache, a module-level constant, or a global nothing in that set covers —
and whichever it is, the inventory is where it belongs, not a `sort` on the worker's
queue.

Until then `--dist loadfile` is the honest default. Closing this is what makes `load`
the default and the run under a minute.

## Block E — Adoption

## Block F — The plugin
