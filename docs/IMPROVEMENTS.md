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

### §RK452 The pointer write binds the heading it starts naming

Under an outline the id in the heading is the binding (RK262), and two writes make it:
`section add` renders it when a live line already points at the anchor, `add --section`
because it holds the line. Neither runs when the design is written first. `section add
I.1 --title "…"` on an anchor nothing points at yet composes a heading naming no task,
and the `add --ref I.1` that follows creates the pointer and never returns to the
heading. On a fixture, line first yields `### I.2 Why the cache is cold (XX2)`, section
first `### I.1 Why the widget stalls`.

The second order costs permanently. `ship` reports `kept … §I.1 names no task in its
heading, so it is prose belonging to none`, `lint` exits 0, and the rationale for
shipped work stays in the prose file, which is what RK6 exists to stop. The recovery is
the `section amend --title "<title> (<id>)"` RK262 already named, derived from a field
called `kept` a round after the evidence scrolled away.

So the pointer write does from the other end what `section add` does: where `--ref`
names an outline section binding no task that no other live line claims, the binding is
rendered with the pointer in one transaction. Not a heuristic about the prose (RK236):
the anchor is claimed by exactly the line that would have bound it had it been written
first. Two live claimants is RK64's ambiguity and stays the author's, as at `section
add`.

## Block C — Query

### §RK453 Which lines claim an address, beside whether it is spent

RK452 stops the state being created; it does not reach the corpora already holding it. A
heading written before its line binds nobody for the rest of its life, and no command
lists one — the fixture's §I.1 was found by reading `ship`'s `kept` field as it scrolled
past, and Shio's were found the same way.

`anchors` is the only verb that lists sections, and its `live` answers a different
question: RK247 built it about address reuse, so `live` means a heading declares the
address *now*, and §I.1 — written for a task that has since shipped, claimed by nothing
open — is counted among `3 live` beside two that are working.

`lint` cannot be the reader, and RK236 already said why. Under an outline a heading
naming no task is prose belonging to none, which Turing's standing GEO memo genuinely
is, so a finding would refuse a legitimate memo with nothing that closes it. The state
is a fact and not a violation, and L5 is that a fact costs a command rather than a file
read.

So the claim goes where the sections are already listed: per address, which live lines
point at it and whether its heading binds one. An adopting project sees its unbound
headings in one call, RK452's write is auditable instead of asserted, and an address
whose only claimants are in the ledger is named — the thing `ship` reported once and no
reader has held since.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin
