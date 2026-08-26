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

### §RK1361 A decision keeps its body, or the reasoning leaves with the section

RK1269 chose the ledger's shape and was right about the line: an id, a marker, one
falsifiable claim, a reason. It also dropped the pointer, on the argument that the line
is written at the moment its section is deleted and that a section copied whole is the
accreting rationale file this tool refuses. Both halves of that hold. What it leaves is
that the alternatives rejected and the consequences accepted have no governed home at
all — `--recorded-in` addresses a file this tool does not read, and a docstring above
the code answers what was built, never what else was weighed.

The body proposed here is not that section moved. A design section says how the work was
built and is correctly deleted when it ships; a decision's body says what was weighed
and what it costs, which is the half no store keeps. So `decisions` joins `PROSE_ROLES`
with a budget of its own, its sections living in its own file and never deleted — the
one departure stays `supersede`, and a superseded entry keeps its body, that being the
record of what the replacement was needed against. The accretion risk is real and is
answered the way every other prose file here answers it: a word limit at the write, and
a file that grows only by decisions somebody actually made.

## Block C — Query

### §RK1362 The spec is already composed; nothing can hand it over

`brief` answers with the symptom, the non-goals that bind it, the `## Done when — <id>`
list and the design section — which the skill already calls the spec, and which RK1265
completed when the criteria reached the line. So the document exists. What does not is
any way to hand it to something that is not this session: a reviewer on a pull request,
a second agent on a branch, a CI job asserting the criteria — each would have to run the
read and cannot, and the read is bounded at 3,300 characters because it is sized for a
tool result rather than for a file.

`export --spec <id>` is the same projection with a file's ceiling instead of a result's,
beside `--readme` and `--site`, which is where the derived-writes argument already
lives: idempotent, stamped with nothing, and every character having passed a write that
validated it. It composes nothing new and holds no second grammar — a spec that drifts
from its four stores is a spec derived twice, which is the failure `--contents` exists
to prevent one file over. Not speckit's generation, which L4 forbids, and which is the
half of speckit this format deliberately has no model for.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1360 The served surface is the project's, not the package's

Measured before proposing it: 66 tools, 64,612 of 64,700 held — 88 units of headroom,
and the reason it is that tight is that the list is composed from the package's parser,
so roadkeep, Shio and Turing publish the same 66 whatever each declares. `[files]`
already narrows the enum of a `role` argument to the declared roles; it does not decide
whether the tool exists. So a project that never files a decision pays `record_add`'s
1,752 units in every session, and `[tools] session` has been re-argued eight times
against a total no single project actually spends.

The consequence is the one that matters for every vocabulary after this: a new role
costs every adopter, so each is argued against a ceiling the arguing project is not even
using. Narrowing publication to `config.has(role)` inverts that — the ceiling becomes
what this project can call, the budget stops being a constant about the package, and
`cost --tools` answers per checkout rather than per build. What has to stay honest is
the refusal: a tool absent because a role is undeclared must still be reachable as a
message naming `declare`, or an agent reads the absence as the verb not existing.
