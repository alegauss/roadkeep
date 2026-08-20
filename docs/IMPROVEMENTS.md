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

### §RK1285 Two writers, one message, opposite advice

A refusal composed of two writers can contradict itself, and one now does. The sentence
RK1281 added says the remainder cannot go in the rationale section, because this ship
deletes it; the violation printed under it says the remainder belongs there. Both are
the tool's, one line apart.

`RemainderRefused` met the same shape and answered it: the violations are the schema's,
and where one of them names the wrong *field* for the call being made, the record
renames it before printing. The field is right here and the **advice clause** is wrong —
which is the same defect at the other end of the same message.

The clause is not part of the rule. `symptom.too-long` is a code, a count and a limit;
"the remainder belongs in the improvements section" is a door, appended because that is
where an over-long symptom's words usually go. Every other refusal in this tool that
carries a door composes it from the case, and this one is composed from the field.

So the repair is to make it a door like the others: a symptom refused where the section
is being deleted has none, and the record that knows so already says it. Suppressing the
clause or moving the door onto the carrier is what the design has to choose.

What it must not do is leave two sentences that disagree and trust the reader to rank
them.

## Block C — Query

### §RK1286 The one read nobody prices

Every resident file has a budget and the served surface has two, because RK30's argument
is that a limit nobody counts is a limit that moves. The read those budgets exist to
protect has none of its own.

`brief` starts a task, and its whole claim is that it fits in a tool result — an answer
that does not is one a session replaces by re-reading the file, which is the cost RK29
removed. It grew this session: the ledger allowance, the two clauses composing that
sentence, the decisions role's limit, and the claim a decision inherits. Four arithmetic
rows where there was one, each argued and none counted.

That is exactly the shape `[budgets]` was declared against, one read out instead of one
file. Nothing here says the answer is too long — it says nobody knows, and the tool that
prices `agents.md` to the byte and every served description to the character has no
figure for the read it recommends over reading the file.

So `brief` is measured, in the unit a tool result is paid in, and the number is declared
where every other ceiling is. What that number should be is a reading somebody takes,
not one this line guesses.

The bound is the *widest* brief and not the median: a task with a pointer, a design,
deps, criteria at two altitudes and every role declared is the one that overflows, and
the one a reader meets on the hardest task.

## Block D — The gate

## Block E — Adoption

### §RK1284 What a limit inherits, measured before it is declared

RK1281 named three arms and built two. The refusal says which doors are real and `brief`
prices the claim before the write; the third — refusing the limit where it is declared —
is the one the verb for declaring limits was built for, and it does not see this.

`govern limits.symptom <n> --role decisions` measures the decisions file's own lines. On
a project that has filed no decision that is zero sites, so any number is accepted, and
every `ship --decides` afterwards is refused over a claim the roadmap already carries.
Reproduced on a scaffold: 20 accepted against a 46-character symptom sitting open one
file away.

It is RK1279's hole at a different set. There the reading walked a written-out list of
roles and missed one; here it walks the right file and misses what will be *carried
into* it. For this one role the corpus is not only what the file holds — it is every
open line that may ship with a decision.

So the reading for that role's `symptom` is the roadmap's claims as well as the
decisions file's own. Nothing else changes: the widest of the two populations is the
number, the refusal already names it, and no other key inherits anything.

What it must not become is a reading of what *might* be written everywhere. This one
inheritance is declared in code — `_decided` composes the claim from the line — so it is
derivable rather than guessed, which is the whole difference.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
