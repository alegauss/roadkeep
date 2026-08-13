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

### §RK1123 The dataclass with two payloads and no closure

`Scope` has five fields and two payloads carry them: `rendering._scope_json` for a
departure and the dict `claim <id> --json` composes. Nothing holds the two against the
dataclass.

Measured while shipping RK1120, which added the fifth: both payloads were edited by
hand, and the only thing that would have caught a missed one is a reader noticing later
that a client is parsing a field this tool stopped sending — or never started.

This is the arrangement RK276 and RK289 already closed one dataclass over. RK289 bound
`Plan` to `install --json` with a test that reads `dataclasses.fields` and asserts every
name is in the payload — and it earns its keep on every field added since, RK1113's two
included:

```
named = {PLAN_RENAMES.get(field.name, field.name) for field in fields(Plan)}
assert named <= set(payload)
```

The same test over `Scope` is the deliverable, and the rename table is the part that
needs a decision rather than a copy: the two payloads already spell three of the five
differently (`mine` → `paths` in one of them, `loose` → `unclaimed`, `idle` →
`staging_nothing`), and a name a client reads is a contract this must not quietly rename
to make a closure pass.

So: one table saying which field each payload calls what, asserted in both directions
like RK491's rule for an unheld code — a field with no entry is red, and an entry naming
no field is red too, which is what keeps the table from outliving the dataclass it
describes.

## Block C — Query

### §RK1122 The read that cannot see what the departure can

RK1120 gave a departure the half `loose` cannot reach: for a governed file this id
explains, which *other* ids gained or lost a line since HEAD. `claim <id>` is the other
reader of the same contract and it answers `shared: []` on every call, because
`departing` computes the list and `split` does not.

The asymmetry is backwards. A departure is the moment of committing and this read is the
one an author makes *before* it — `--porcelain` exists to be piped straight into `git
add --`, so it is the answer a commit is actually composed from on every task that is
not shipping. A session that runs it is told the paths and not that the roadmap it is
about to stage already carries somebody else's line.

```
$ roadkeep claim RK2 --json | jq .shared
[]                       # always, whatever the roadmap holds
$ roadkeep ship RK2 --why "…"
  shared   ROADMAP.md  (RK9 moved in it too, and staging it takes that)
```

Both readings are already available here. `claim <id>` asks git for `dirty` and
`indexed` and computes `written`, which is the accounting the `shared` list is
subtracted from, so what is missing is the call and not the machinery: `ids_since` is
pure over a revision and a role.

What is worth keeping is why the two verbs differ at all. A departure *must* answer,
because after it the claim is released and no verb can; this one is asked, so it answers
either way. That makes the read the cheaper place to put a warning and not the one to
leave it out of.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
