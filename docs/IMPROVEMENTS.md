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

### §RK1059 A budget the gate cannot spell

RK30's argument is that a budget stated in prose is a budget nothing holds, and its
answer is `[budgets]`, checked by `lint`. RK464 then measured the served tool list for
the same reason — what the surface costs a session that connects it — and stopped at the
read. `budget --tools` answers **53,369 UTF-16 code units across 52 tools** here,
against the 7,695 bytes budgeted for `agents.md`, and nothing refuses either number.

The gap is structural rather than an oversight: `[budgets]` is keyed by path and this
cost is not a file. It is composed per session from the parser, the config and the
`TOOLS` table, so what needs bounding is a derivation. That is also why it drifts
silently — every flag added to a served verb and every sentence added to a `help=`
raises it, in an edit whose diff shows one argument.

Measured moving twice in one session: withdrawing one flag from `record add` took 221
code units off, and a note rewritten on two verbs put some back. Neither was visible as
a cost in the change that made it.

What a budget here means is the decision. A ceiling on the total is one answer and a
poor one — it fails on whichever tool is added last. A per-tool ceiling names the
offender, and `budget --tools` already ranks them, which is the shape the read was built
in.

## Block E — Adoption

## Block F — The plugin

### §RK1060 A caveat that costs more than the fields it qualifies

`_aimed` closes every prose bound with the same paragraph: aim for N words, N characters
refuse, counted in UTF-16 code units, and the `maxLength` beside it counts code points,
so an astral character can validate on the client and be refused here. It is correct,
RK436 argued it well, and it is published on **13 properties** — 4,186 of the 53,369
code units the tool list costs, or one sentence in every twelve a session reads.

The duplication is not the schema's to remove. `$ref` would deduplicate the *document*
and not the reading: a model is handed the tool list as text, so a shared definition it
has to resolve is worse than a repeated sentence, and every published bound here exists
because an unpublished one reaches the author as a refusal.

What is available is where it is said. This server has **instructions**, delivered once
per session and already carrying the version and the package path, and the caveat is a
fact about the whole surface rather than about `why` on `add`. Said there, the per-field
note keeps the number and the aim — which are what differ — and loses the paragraph that
never does.

Worth measuring rather than assuming: the saving is real only if the instructions are
not themselves repeated per call, which is a fact about the client and not about this
tool. The read to make first is whether a session that connects this server is given
them once.

## Block G — The editor surface (the backlog where the file is open)
