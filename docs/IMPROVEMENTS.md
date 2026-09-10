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

### §RK1670 The door an undeclared role has

`Config.path` raises `this project declares no 'deferred' file (has: changelog,
improvements, roadmap)`, which is two thirds of what a refusal owes: it names the
absence and what stands in its place, so the caller can tell the question apart from an
empty answer. What it does not name is the verb — and `declare`'s own description says
outright *reach for it when a verb refuses over an undeclared role or table*, so the
door exists and the one refusal it was written for does not point at it.

RK1328 made the same repair one table over: `criteria.NotGoverned` said *`declare
criteria` opens the table* rather than naming a hand edit to configuration this tool
owns the writes to. A role is the same shape and reaches more callers — every read and
write that resolves a path goes through here.

What has to be decided is the site. This raise is in `config.py`, below `remedying` and
`provenance`, so a `Door` here would be an import the layering does not have; the plain
backticked verb `criteria.py` uses needs none, but `test_composing` holds its census
total over every function that composes a command, so the row and its run come with it.

### §RK1671 The suite that shipping breaks

Three tests went red in one sitting of shipping, none of them about the code that
shipped: `test_ranking` asserted that at least half the differing rows are unreachable
at any width and the backlog reached one differing row; two note-cost tests asserted
this project's gate says a note, and pricing the last open line silenced the last of
them. Each repair was a guard or a skip, and each was written by whoever met the red.

RK1098 met this once and built the answer: `conftest.populated` is this repository
whenever its backlog has an open line and a three-line stand-in when it does not, so *an
emptied roadmap changes which files are read and never whether the contract is
asserted*. RK1630 met it again and moved a claim to a pinned corpus. Neither is a rule,
and the three above reached the live state directly.

Measured: 24 reads of `Config.discover(<checkout>)` across six modules, 18 of them in
`test_budgeting`. What is not known is how many of those assert a **non-empty** answer,
which is the half that goes red — and that is the reading, not a guess to be repaired.

## Block D — The gate

### §RK1672 The other pasted line

RK1667 taught `capturing.offer` to ask `provenance.survives` before printing a line, and
one refused `add` prints **both** doors: the retry row, and the capture offer under it.
Measured on an outline project with a symptom naming `pick` in backticks — the offer
replaced the token and said so, and the retry two lines above it carried the span
verbatim.

The retry is the door that costs most to get wrong. RK1149 built it because the refusal
had already derived the one token the caller was missing, and the alternative was a
sentence to read, extract and retype; RK1600 published the argv beside it for the same
reason. So it is composed *to be pasted*, and pasting it into the shell this repository
is developed at runs whatever the backticks enclose.

What is not obvious is whether it takes RK1667's answer unchanged. That door replaces
the token with `…` and asks for one field back; here the caller's own prose is the
*whole* of what the retry re-sends, and a retry with a placeholder in it is a call they
have to complete rather than one they can run — which may be an argument for the
payload's `argv` instead, already published and never quoted.

## Block E — Adoption

### §RK1673 The two tables no verb tunes

`declare non_goals` on a project that already has the table refuses, and named `govern
non_goals.lead <n>` from RK1328 on. `governing.GOVERNED` is `limits`, `budgets.<path>`,
`tools`, `claims`, `reads` — so that call has always exited 2, with `no governed number
at 'non_goals.lead'`. `declare --help` says the same thing in its own words: *a table
arrives empty, and `govern` tunes what is in it*.

RK1668 found it by running the line rather than reading it: the span was bare, so it was
no `census` site, so nothing had ever executed it. The door is now `config`, a read that
is true, and what the two sentences claimed is still missing.

What it costs is exact. `[non_goals] lead` and `[criteria] lead` are word limits like
every `[limits]` key, and the only route to either is a hand edit of `roadkeep.toml` —
the act L1 exists against, and over MCP not an act at all (RK1264's argument, one table
over).

The question the repair answers is whether `GOVERNED`'s claim is wrong or its membership
is. It reads *every other table holds a name, a path or a flag — a decision with no
reading behind it*, and that is false of these two: `budget --non-goal --lead` already
prices one and `lint` already refuses a lead over the number. So the reading exists, and
it is not where the write is.

What must not happen is a third spelling: a `declare --lead` beside `govern` would put
two verbs on one number.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
