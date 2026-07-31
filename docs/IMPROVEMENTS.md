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

### §RK67 The entry nobody can drop

The ledger is append-only by design: `ship` and `retire` move a line into it, `record`
writes one that never had a line, and nothing takes an entry out. That is right for
history and wrong for a duplicate — Shio's `SH347` is on lines 579 and 586 of its
changelog, so the file states one decision twice and `id.duplicate` reports it with no
command that can act.

`ship` cannot help: the id is already recorded, which is what RK62's closing path now
reads as a leftover roadmap line rather than a leftover entry. `retire` would add a
third. `--fix` repairs only what is derived. What is left is the hand-edit the hook
denies, which is the same dead end RK65 opened for a roadmap line.

So `record drop <id>` — the inverse of the door that wrote it, and narrow for the same
reason: it refuses unless the id appears **twice** in the ledger, because removing the
only record of a decision is deleting history rather than de-duplicating it. Which of
the two goes is the later one: the first is where the reader already found it.

Not a general delete. An entry that is wrong in its prose is `amend`'s question one file
over, and an entry that should never have been written at all is a decision the author
states in the commit that removes it.

### §RK70 The one write the denial cannot name

RK22's value is that the refusal *is* the command to call. For the non-goals it is not:
`Edit` on the roadmap is denied and the reason offers `add`, `status`, `amend`, `ship`
and `retire`, all five of which write task lines. What is left is `sed` through `Bash`,
which the barrier deliberately does not match and which `lint` does not judge, because a
bullet carrying no marker is prose. So the only content of the roadmap that is not a
task line is also the only content nothing governs — L1 holds everywhere except here.

A non-goal is structurally what `add` already governs, a lead and a reason, so `non-goal
add --lead "…" --why "…"` needs no new law: one renderer, and the fields refused at
input. Addressed by its lead, unique and checked. **No ids** — an id creates a
lifecycle, retire and rename, for a list of eight lines that changes once a year. The
trigger that would change that answer is already visible: Turing's backlog says "which
the Non-goals say is not the path", a reference resolving to nothing, which is the
defect RK15 catches for `→ §`.

The shape is opt-in under `[non_goals]` (L6), for RK66's reason: Shio and Turing wrote
theirs before the schema existed, and a default that reports fifteen findings on
adoption is a gate that gets bypassed. This repository opts in and is the fixture.

### §RK72 A non-goal that argues the schedule

The list says *No dates, quarters or estimates. A marker is maturity, not a schedule.*
The reason given is about scheduling, so by its own letter it does not reach a `P/M/L`
size bucket, which claims nothing about when. A proposal to add one arrived and the
non-goal did not settle it — three laws did, at the cost of an analysis where a lookup
should have answered. A constraint that must be re-derived every time it is tested is
one that will eventually be re-derived wrongly.

So it names the field, and carries the reasons the field fails rather than the reason a
date fails.

An effort letter would be the only field here that nothing can verify: every other one
is a derivable fact or a falsifiable claim, and nobody returns with `amend` to correct
an `L` that shipped as a `P`.

The unit does not cross the human/agent boundary. What an agent pays is context, and the
files a task touches is nearly flat — 4 to 14, median 9 — while the lines vary 27-fold.
The letter would price the axis nobody pays.

And it would poison `pick`, whose every tier is a fact today. Preferring the cheap
letter optimises commit count against build order, and the heavy tasks are the
architectural ones.

Waiting on RK70 is the point and not an accident: a non-goal is prose no command can
write, and the hand-edit is what the hook denies. This is that door's first concrete
customer.

## Block C — Query

### §RK68 The lead that is a guess

`brief` carries the non-goals as leads, and the lead is scraped: the first `**…**` run
anywhere in the bullet, or the text before the first `. `, over the bullet's first
physical line only. Both halves fail on the second live corpus. Turing's first non-goal
spans four lines, so the lead keeps three of the ten things it forbids and drops the SSE
bus, the anti-injection normalization and `TurToolCallbackPipeline.decorate`. Its second
reads `Structured output (LLM → JSON) is **not** a path`, where the bold is mid-sentence
emphasis — so the printed non-goal is the word `not`.

This repository's own five leads are correct, which is the part worth saying out loud:
the fixture proves the reader only where the file was hand-written to the convention the
reader assumes.

So the lead is a bold run **at the start** of the bullet or nothing, the bullet is
joined across its continuation lines before it is cut, and the cut is stated where it
happens. And it is bounded like every other field of a brief — the chains stop at two
and a section has a word budget, while the non-goals are today the one field with no
limit at all, so a forty-bullet section replaces the file the brief exists to save.

Not a rewrite of anyone's prose (L4): what changes is which characters are quoted.

### §RK69 The list that binds a proposal it never sees

The roadmap tells an author to check the non-goals before proposing work, and `brief
<id>` is the only command that prints them — which is the moment a task *starts*, not
the moment one is *proposed*. `add` neither prints them nor is scoped by them, so the
constraint is carried by a sentence in a file, which is the arrangement §0.1 measured at
186 KB.

`roadkeep non-goals [--json]`, and the same tool over stdio: eight leads cost nothing on
the turns that propose nothing, and the guard's roadmap table names it, so a denied edit
teaches the read as well as the write. The skill says to call it before `add`.

What this is not, stated here so nothing promises it later: **presence, not
enforcement**. Deciding whether a proposed task violates a non-goal is a judgement about
meaning, and the tool has no model and will not get one (L4) — a keyword match over
eight bullets would produce a confident wrong answer, which is worse than the sentence
it replaced. An `add --acknowledge-non-goals` flag is the same theatre one step later:
an agent passes any flag it is asked to pass.

### §RK71 The weight the ledger already knows

Sixty-three shipped tasks here cost between 52 and 1384 lines in the commit that wrote
their ledger entry: p25 170, median 376, p75 574, p90 811. Eight are above 800 — RK2,
RK6, RK9, RK10, RK18, RK22, RK32, RK48 — and they are the architectural ones. The spread
is real and nothing in the backlog says it.

`history` can already answer it: the commit that added an entry is findable by pickaxe
over the ledger, so *what did a comparable task cost* is a query rather than an
estimate. Which is the point — a derived number cannot rot, costs nothing on the turns
nobody asks (L5), and anyone who doubts it can check it against git.

What it is for: **granularity, at the moment the line is written.** A block whose last
three comparables shipped at 800+ lines is a block where the next line is probably two
lines, and that is an authoring decision the tool can inform without predicting
anything.

What it is explicitly not for: **ranking work.** Every tier of `pick` is a fact — in
progress, declared priority, lowest ready id — and a cheapness tier would defer exactly
the eight tasks above, which are the ones with the most leverage.

And never a field on the line: §RK72 carries that argument.

💭 and not 📋 on purpose. It changes perhaps one authoring decision in ten, and the marker
set exists so that can be said instead of promoted.

## Block D — The gate

## Block E — Adoption

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

### §RK66 A pointer a project may not require

`ref_required` is a `Schema` field and no key reads it, so every project is held to
"every task points at its rationale section". Shio's own process guide says the opposite
and says it for the reason RK15 gives: *if a task has no rationale section, the line
carries no pointer — a pointer to nowhere reads as though the design exists.* Three of
its lines follow that rule and each one is a finding.

Both positions are defensible, which is exactly what makes this configuration and not a
default to argue about (L6). A project that derives its anchors from ids can require the
pointer, because writing the section is one command away and the anchor cannot be wrong.
A project that numbers by hand may have a task whose design is one line long — and
inventing a section to satisfy a linter is the accretion this tool exists to refuse.

So `ref = false` under a table that already governs the line's shape, defaulting to true
so nothing changes for a project that never declares it. `add` then stops refusing
without `--ref` there, and `lint` stops reporting a pointer nobody promised.

What stays unconditional is the other direction: a pointer that *is* written must
resolve. The choice is whether to demand one, never whether it may dangle.

## Block F — The plugin
