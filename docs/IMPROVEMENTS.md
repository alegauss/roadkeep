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

### §RK431 The id a sentence spent

Shipping SH207 meant recording a defect it had uncovered. The ledger entry said *"filed
as SH614"* — the id `next-id` had just reported — and then `add` handed the new task
**SH615**.

Nothing malfunctioned. `id_sources` scans the governed files for `SH<n>`, the entry had
just been written into one, so the highest id in the corpus was the one the sentence had
promised to a task that did not exist yet. The deriver cannot tell an id that was
*declared* from one merely *mentioned*, and every id starts as a mention.

The cost is quiet. The `add` succeeds, the number looks unremarkable, and the only
signal is a prose reference to an id nothing will occupy — in a file the guard forbids
hand-editing. It is also a gap `gaps` cannot cover: that verb explains an id in neither
file, and this one *is* in one.

Two candidate answers. **Warn on derivation**: when the id below the derived one appears
only in prose and never as a task line or ledger entry, say so — the reader knows
whether it was a promise. **Or reserve**: let `next-id --claim` hold a number, so the
sentence and the task agree by construction rather than by ordering.

Recovery was clean, worth recording: `record amend` existed, named itself in `record
--help`, and fixed the entry in place rather than deleting and re-appending it.

## Block C — Query

## Block D — The gate

### §RK430 One limit, two counters, and the emoji is ours

Shio's `ShRoadmapLineLengthRatchetTest` failed on a line `roadkeep stats` had just
reported as `longest SH611 at 320 of 320` — inside the limit. The Java gate measured
321.

Neither is wrong. Python's `len()` counts **code points**; Java's `String.length()`
counts **UTF-16 code units**, and a character outside the Basic Multilingual Plane is
one of the first and two of the second. The line held exactly one: `📋`, U+1F4CB, the
status marker — which roadkeep writes. The tool emits the character that makes its own
measurement disagree with the consumer's, then certifies a line the consumer rejects.

The failure lands in the wrong place: on the next person to run the suite, in a build
they did not break, on a file the guard forbids them to hand-edit. Diagnosing it cost a
full-suite run and a character-by-character count, because both numbers look right and
the difference is one.

Every backlog roadkeep governs has this, silently: the markers `[markers]` declares are
overwhelmingly astral-plane emoji (📋 💭 ⏳ 🛠 ✅), and any gate written in Java — or C#, or
against JavaScript's `.length` — counts them double.

The likely answer is to **measure in UTF-16 units and say so**: it is the stricter of
the two, so a line that passes is portable to a code-point counter and the reverse is
not. Declaring the unit in `roadkeep.toml` is the alternative. Either way `stats` and
the limit check must agree with the gate the project runs.

## Block E — Adoption

## Block F — The plugin
