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

## Block E — Adoption

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

### §RK49 An indented task line

Shio nests four live tasks under the line that shipped their parent:

```
- ✅ **SH22** (deps: SH2) **Multi-tenancy / SaaS** — shipped → CHANGELOG Block F. Follow-ups remain:
  - 💭 **SH44** (deps: SH22) **Superadmin impersonation** — … → §VI.1
```

The parser refuses the children with "indented: a task line starts at column zero", so
SH44 through SH47 exist in the file, carry ids, deps and pointers, and are invisible to
`list`, `stats`, `pick`, `brief` and the graph. An id that nothing counts is also an id
`next-id` would hand out twice.

Column zero was a deliberate choice: it keeps a task line distinguishable from the prose
in a nested bullet. But the four lines above are not prose — they are task lines, and
they parse completely once the indentation is allowed. So the rule becomes: leading
whitespace is permitted and **kept verbatim**, which L3 requires anyway, and everything
after it is judged exactly as it is at column zero.

What this does not do is legalise the parent. A `✅` in a roadmap is still refused (it
belongs in the ledger), and that refusal is what tells Shio the grouping line is the
thing to change. Nesting a task is a shape the format can carry; using a shipped marker
as a heading is not.

### §RK50 A limit per role

`[limits]` is one table for every governed file, and the two files have opposite economics. A
roadmap line is refused at insertion, where the refusal costs a retry; a ledger line is
*history*, and 761 of Turing's and 234 of Shio's were written years before this tool existed.
Their median is 982 characters against a `line` limit of 320, and their p90 is 2604.

So the moment RK48 lets those entries parse, 234 `line.unparsed` findings become 234
`line.too-long` findings. The count barely moves and the honesty gets worse: an unparsed
line is roadkeep admitting it cannot read the file, while a length finding on a shipped
line is roadkeep asking for a rewrite of something nobody will rewrite, in a file that
only grows.

The limit still has to exist on the write path — `record` (RK41) and `ship` compose
ledger entries from fields already refused at input, so L1 is unaffected either way.
What has to change is what `lint` says about lines that predate it: a project declares
`[limits.changelog] line = 4000` and keeps `line = 320` for its roadmap, and the gate
then reports the drift the project can act on instead of the history it cannot.

The default is the same number for both, so nothing changes for a project that never
declares one — including this repository, whose own ledger is short by construction.

## Block F — The plugin
