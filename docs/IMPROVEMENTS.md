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

### §RK1127 The subtree that is not a stranger

`designs_since` labels each section by the id its heading names, or by its anchor where
it names none, and `sharing` then subtracts the id being committed. Under the id scheme
a subsection's anchor is `§RK2.1`, which is not the string `RK2` — so this task's own
subtree survives the subtraction and is reported as another session's design.

Measured in a scratch repository, one subsection appended to the section being shipped:

```
$ designs_since(config, "HEAD", "improvements")
frozenset({'RK2.1'})
$ … - {"RK2"}
{'RK2.1'}
```

So the report a departure prints would name `RK2.1` as work this commit is carrying for
somebody else, on the ordinary shape RK1112's own docstring describes: *a `§<id>.1` is a
section with an anchor of its own, amended by naming it*. A reader who trusts one false
`shared` line stops reading the true ones, which is the whole cost of the rule it
belongs to.

The comparison is the wrong one and the right one is already written. `sections` reads
an address **segment by segment and never as a string prefix** — the care `_extends`
takes so `§0.1` is not read as extending `§0.10`, and `descending` is the reader that
answers which anchors are one address's own subtree.

Which leaves a question the fix has to answer rather than inherit: a subsection of
*another* task's design is that task's, so the exclusion is "extends this id" and not
"starts with it", and an outline's `XVI.12.3` is nobody's id at all until its title says
so.

## Block C — Query

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1128 A --lines refusal points at a missing entry that is present

`ship <id> --part "…" --lines 1` on a line that already records a partial refuses with
*"--lines says how many lines a completion replaces, and this call replaces none:
docs/CHANGELOG.md records no partial for T898, so the entry is placed and nothing is
deleted"*.

The ledger did record one — `docs/CHANGELOG.md:693`, `**T898 (the lint half)**` — and
dropping `--lines` proves the engine knows: the next refusal is *"T898 already records a
half in docs/CHANGELOG.md:693 (the lint half)"*, with the right guidance (a delivered
step takes its own id).

So the first message sends the caller to look for an entry that is there. The real rule
is narrower than what it says: `--lines` describes how many lines a **completion**
replaces, and a call still passing `--part` is not a completion, so there is nothing for
it to replace regardless of what the ledger holds. Saying that — rather than reporting
the ledger as empty — would land the caller on the second refusal's advice directly.

## Block G — The editor surface (the backlog where the file is open)
