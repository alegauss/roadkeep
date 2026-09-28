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

### §RK1708 An address for a ledger entry with an ungrammatical id

Shio's `docs/CHANGELOG.md` carries adopted entries whose ids predate the id grammar,
such as `**SH-0f**`. One of them is among the six false `code.renamed` findings (see the
rule's own line), and rewording it is the documented remedy. It cannot be applied:
`record amend SH-0f` answers "SH-0f is not in docs/CHANGELOG.md", because the id pattern
does not accept it. The guard also refuses the hand-edit. So the one entry is correct by
no verb, and the finding the gate shows for it names a verb that refuses it.

The ledger reader already parses the entry, since lint reports its line and column. What is
missing is an address for an entry whose id the grammar rejects. Two shapes:
- `record amend --line <n>` on the ledger, taking the line the finding printed. A lint finding
  already names `docs/CHANGELOG.md:1290`, so the address is in hand.
- `renumber` accepting a legacy id as its source, so the entry gets a grammatical id first.
  That changes history, and `renumber`'s own rules may forbid it.

The first is smaller and matches how a finding is read. Either way, the finding's remedy
text for an id-less or ungrammatical entry should print the verb that will actually
accept it. At the moment it prints `roadkeep record amend … --why -` with an ellipsis
where the id would go.

Fixture: a ledger with one `**XX-0f**` entry, a finding against it, and the remedy the
finding prints applied successfully.

## Block C — Query

## Block D — The gate

### §RK1707 code.renamed tells a vendored engine from the project's own source

`code.renamed` resolves a backticked dotted name against the engine's own modules, and
it runs only when the engine sits inside the project (`linting.py`, `config.root not in
home.parents`). The condition is meant to mean "this checkout is roadkeep's source". An
adopter that vendors the engine meets it too: Shio fills `.roadkeep/` the way
`node_modules` is filled, so `ROADKEEP_HOME` names a directory inside the project root.

Measured in Shio on 0.2.489 and 0.2.505: `lint` exits 1 on six `code.renamed` findings,
all false. Ledger entries cite document.fonts, document.referrer and schema.graphqls
(browser and GraphQL names, bare here because backticked this rule fires on them in this
repository, correctly), which match roadkeep's `document.py` and `schema.py`. Held there
as SH1102 since 0.2.473, so its docs gate passes only with `--baseline`.

The engine directory needs to prove it is the project's own source, not merely sit under its
root. Candidates, cheapest first:
- the engine's `pyproject.toml`/package root is the project root;
- the project's `roadkeep.toml` prefix is roadkeep's own;
- a vendored copy carries a marker the installer writes, and the rule skips it.

Whichever is chosen, the vendored layout needs a fixture: an adopter tree with the
engine under `.roadkeep/` and prose citing document.x must lint clean. The existing
fixture of this repository citing a renamed symbol must still report it.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)

## Block J — Validation (whether a person ever tried it)

## Block K — The desktop app (one installer for the reader and the plugin)
