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

### §0.4 The limits, measured against a live corpus (RK20)

§0.1 asked whether the limits are right or the lines are. Shio's 78 active lines answer
it, and the answer is split in a way that only a real backlog could have produced:

| Field | Limit | p50 | p90 | max | Over |
|---|---|---|---|---|---|
| `symptom` | 120 | 58 | 86 | 111 | **0 of 78** |
| `why` | 200 | 481 | 900 | 1251 | **70 of 78** |

The same authors, in the same lines, met one limit every single time and missed the other
89% of the time. So 89% is not evidence that 200 is too small — `symptom` is the control,
and it shows compliance is available. The difference is that "what does not work" is one
clause by construction and a `why` has no natural end, which is L1 stated as a
measurement: the field whose scope is unbounded is the one that needs the bound at the
write path.

And the migration is smaller than §RK20 assumed. **74 of the 78 pointers resolve, and none
dangle**; 67 of the 70 over-length lines point at a section that already exists and already
makes the same argument — compared line-against-section on SH295 and SH309, the `why` is a
recompression of the paragraph, same examples and all. The rationale is not homeless. The
line is a second copy of it, so the edit is compression against a text that is already
written, not authorship.

## Block A — The model

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK61 Ownership under an outline

`section.orphan` and `section.stale` ask whether a task line owns a section, and both
are guarded by `ids.match(anchor)` — the anchor has to be `SH<n>`-shaped. Under
`ref_scheme = "outline"` an anchor is `XVI.12`, so neither check ever fires, and that is
the scheme both live projects use. Shio has 146 sections and gets no ownership check at
all.

Not a theoretical gap: Shio keeps a 280-line JUnit test for exactly this, and the
measurement that motivated it was 121 sections against 82 pointers with **11 dead**, 1
section written twice, 9 unnumbered, 1 left behind after its task shipped. When Shio
adopted roadkeep only one of that test's five checks could be retired — the other four
are what this gap leaves unenforceable, and a project should not keep a linter in
another language to cover a scheme this tool claims to support.

What is missing is one fact: the ids a heading names. `### §XVI.12 A design (SH123)`
says whose it is, in prose the parser already reads for the number. Collecting those ids
makes both checks scheme-independent — the anchor addresses the section, the heading
says who owns it — and it also answers the check with teeth: a task that *has* a section
and points somewhere else is a pointer that resolves and is still wrong.

The heading and not the body: a section quoting another id is discussing it, not owning
it, and a check reading the body would report every cross-reference in the file.

## Block E — Adoption

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

### §RK62 A line with nowhere to go

Shio's roadmap carries `- ✅ **SH22** … — shipped → CHANGELOG Block F. Follow-ups
remain:` with four live tasks nested under it. That one line is four findings — a
shipped marker in the roadmap, the same id in two files, no pointer, no terminator — and
**no command can remove it**. `ship SH22` refuses, correctly: the entry is already in
the ledger at line 878, and a second would make the file disagree with itself. `retire`
would write a departure that did not happen. The hook denies the hand-edit, which is the
point of the hook.

So adoption leaves a class of line the format rejects and the tool cannot fix — and it
is exactly the shape adoption produces, because a project that moved a task to its
changelog by hand and left a pointer behind was following its own convention.

The door is `ship` again, one step narrower: when the id is already recorded, closing
the roadmap line is not a second entry, it is the rest of a transaction that never
completed. The refusal becomes an offer — the line goes, the section goes, dependents
are re-annotated, and the ledger is untouched because it is already right. What must not
follow is a `--force` that writes a duplicate entry; the asymmetry is the point.

Nesting stays legal (RK49), so the four children survive the parent's removal where they
are.

## Block F — The plugin
