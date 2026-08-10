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

### §RK450 What an atomic rename does not buy

RK118 writes the new content beside its target and puts it in place with `os.replace`,
so no reader ever sees half a file. The docstring's claim is that every state a reader
can catch is a *whole* file. This machine produced one that is not.

A hard reboot mid-session left `ROADMAP.md`, `CHANGELOG.md`, `IMPROVEMENTS.md` and
`README.md` at 2,980, 121,337, 4,333 and 24,068 bytes — every byte NUL. The lengths are
the ones the writes intended. Nothing else in the tree was touched, and the source files
written by the same session in the same minutes were intact.

That is the known shape of a rename without a flush. `stage` calls `write_text`, which
returns once the bytes are in the page cache, and `commit` renames immediately. NTFS
journals the rename's *metadata* and the directory entry lands; the data blocks behind
it had not been written, so after the reboot the file has its committed size and no
committed content. `os.replace` is atomic with respect to two versions of a file and
says nothing about the durability of either.

The fix is one `flush` and one `os.fsync` on the staged handle before it is closed,
which is what every editor and every database does between the two steps. It costs a
syscall per governed file per write.

Open: whether the directory entry needs its own fsync — POSIX says yes for the rename to
be durable, Windows has no handle to open one with, and this tool runs on both.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK451 The report that scaled with the damage

A governed file that a crash left entirely NUL is read as one line of control
characters, so `char.invisible` fires once per byte. Measured on the file this
repository lost: 3,301 findings for 3,301 bytes, each identical but for a column number,
each naming `lint --fix`.

Only the first of three problems is cosmetic. The report is unreadable, and truncation
is the only reason a terminal survives it. The remedy is worse than useless: `--fix`
strips characters that are not text, so here it would produce an empty file and report
the tree clean — a recoverable state destroyed with the gate's blessing. And the
sentence a reader needs is the one nothing says: this file has no content, and `git
checkout` closes it.

The shape of the answer is a check that runs **before** the line reader. A governed file
whose bytes are all NUL is not one this format can have opinions about: one finding, its
own code, and a remedy naming the restore rather than a repair.

Two things it must not become. Not a heuristic about "looks binary" — the decidable
question is whether this is text the tool could have written, and RK118 wrote every byte
of it. And not a refusal to run: the other governed files are still worth linting, and a
report that stops at the first unreadable one hides what is fine.

## Block E — Adoption

## Block F — The plugin
