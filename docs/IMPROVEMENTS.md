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

### §RK78 ship deletes what it did not name

Observed on Shio at SH326. The rationale file nests: a level-2 section groups an epic
and each task keeps a level-3 section under it. `ship` deleted the level-2 by taking
everything up to the next level-2, which swallowed four level-3 children — two of them
the rationale of tasks that are still open, so the roadmap then pointed at sections that
no longer existed. 160 lines went in one transaction that reported dropping one section.

The gate caught it: `lint` reported two `ref.unresolved` immediately after. That is the
right instrument in the wrong order — it names the damage after the write rather than
refusing it, and the operator's only remedy was `git checkout` on the whole file, which
also discards the part of the ship that was correct.

Two things to settle. A drop has to be bounded by the next heading of **any** depth
greater-or-equal, not the same depth. And a transaction that would orphan a live pointer
should refuse before writing, the way `add` already validates every field first — the
reasoning `add` states for itself ("a limit reported after the prose exists is a limit
discovered too late") is the same reasoning, one verb along.

## Block C — Query

### §RK83 Ready is two different states

`pick --block P` answered with the lowest ready id and said so. The block held both
designed tasks and ideas, and the id it chose was an idea — a design session, not an
implementation. A caller who asked to execute a block wants the second kind, and had to
override the answer by hand on every iteration of a long run.

The markers already carry the distinction and the tiers do not read them. Whether that
is a new tier below the declared priority, or a flag, or only a sentence added to the
`because` line — "the pick still needs designing" — is the open question. The last is
the cheapest and may be enough: `pick` already explains which tier answered, and the
complaint is not that it chose wrongly but that it chose silently.

Worth noting what should not change: a block whose ideas are never offered is a block
whose ideas are never designed. The bias belongs to the caller's intent, not to the
tool's ranking, which argues for the flag over the tier.

## Block D — The gate

### §RK84 A gate on a corpus with standing debt

Adopting projects arrive with history. One live corpus lints at 317 problems, none of
which the current change caused, and the number moves by one or two per task. `lint`
exits non-zero on all of it, so on that repository the gate cannot be wired to CI, and
the question actually asked after every write — did I add anything — has no command.

It was answered by hand: stash the three files, run `lint`, unstash, run it again,
compare the two summary lines. That worked and it is not something a hook can do. It
also nearly hid a real defect: the count fell by eight on the run that deleted 160 lines
of rationale it should not have (RK78), and the drop looked like an improvement until
the two `ref.unresolved` entries were read individually.

`--since REV` exists and answers a different question (a rationale edited without its
line, RK36). What is missing is a baseline: the violations at a ref, subtracted from the
violations now, exiting non-zero only on the difference. That is also the shape that
lets a repository adopt the gate before it has paid off the debt.

## Block E — Adoption

### §RK21 Rollout

Turing, Dumont and Cursarei, each with its own `roadkeep.toml`. Four projects sharing
one format is what makes cross-project context transferable; one project with a format
is a preference.

### §RK75 The heading word is a convention

`_BLOCK_LABEL_RE` in `document.py` is `^Block (?P<label>…)`, and `_BLOCK_DEP_RE` in
`schema.py` spells the dep the same way. That is right for the two corpora the format
was read off and wrong for every other one measured: Dumont files all 34 shipped entries
under `## Track A — …`, Turing writes 22 sub-blocks as bare `## D.1 — …`, and cursarei
numbers `## Fase 0 — Higienização`. Three of four adopting projects, and each one gets a
finding per line for using its own vocabulary.

By L6 that settles it: a word a project chose is configuration, not format. What must
stay a fact is the *shape* — a heading declares one label, a task names one heading, and
a dep on a heading resolves against the same list — because that is what `pick`, `stats`
and every block dep are over.

So `[headings] word = "Track"`, defaulting to `Block` so nothing changes for a project
that never declares it, and read by the parser and the dep grammar from one place. A
project whose sub-blocks carry no word at all is the harder half and is not this: `##
D.1` would need the word to be optional, which makes every `## Objetivo` a block. That
is a second decision and belongs to whoever takes it, not to the key that fixes three
files.

### §RK77 The corpus no configuration reaches

Shio and Turing adopted because their lines already *were* this format under other
numbers; Dumont adopted because its roadmap was empty. cursarei is the case none of that
covers, and it is the honest test of L6: four gaps, each needing a different key, none
fixable together.

**The marker holds a space.** Its lines are `- [ ] **C40** · …`, and the parser reads the
first whitespace-delimited token — which is `[`, never `[ ]`. Declaring the checkbox in
`[markers]` does nothing, so all 16 open lines are invisible rather than rejected.

**The heading has no label.** Five read `## Fase 0 — …` and five `## Trilha contínua — …`.
RK75's configurable word does not reach this: the five Trilhas share both words, so there is
no label to be the block, and what tells them apart is prose.

**The separator is `·`.** Twelve lines split symptom from why with a middle dot where the
render writes an em dash — and by L3 a line that does not round-trip is one the tool refuses
to write the whole file for.

**The ledger is keyed by release.** `## Não lançado` over `#### NEW FEATURES` over
`* **Título (C26)** — …`, the id inside the bold title. Nine of twelve entries carry it
where nothing looks.

So the answer is not a `roadkeep.toml` here. A config whose every read is zero claims a
governance it does not have, which is the drift this tool exists to refuse.

## Block F — The plugin

### §RK79 Two engines, one version string

Measured on a live session. `python -m roadkeep.cli` resolved to the developer checkout;
the hooks and the MCP server ran the plugin cache. Diffing the two `src/roadkeep/` trees
found 14 files differing and two modules present in one and absent from the other. Both
`plugin.json` and the package report `0.1.0`, so nothing observable distinguishes them —
and the checkout was two commits ahead of the remote the cache is fetched from, which
means `/plugin update` would not have closed the gap either.

RK57's launcher docstring already names this failure class: "a plugin that silently ran
an older installed copy is the hardest kind of stale". The fix it shipped puts the
plugin's own `src` first, which defends against a stale *installed* copy and cannot
defend against a stale *cache*. The direction it does not cover is the one a developer
of this tool hits every day.

The cheap half is making the two distinguishable rather than making them the same: a
version that carries the commit, or a startup line naming which tree answered. Being
unable to tell is what turns every other symptom into a guess, which is why RK81 is
filed as depending on this one rather than as a defect in its own right.

### §RK81 The agent-native surface is the one that did not load

A full session of driving roadkeep ran `python -m roadkeep.cli` through Bash,
discovering flags with `--help`. `brief --block P` — one call that returns the pick, its
rationale, its deps and the binding non-goals — was used only after four calls had done
the same job worse, because nothing announced it. `list --marker` was found the same
way, late.

That is the cost of the tool schemas not being in context. An MCP server puts every
command's parameters in front of the caller before the first call, which is the
discovery mechanism `--help` archaeology substitutes for badly. The plugin declares the
server and no `mcp__roadkeep__*` tool was offered in the session.

Whether the server fails to start, starts and registers nothing, or was never launched
is not yet established, and RK79 is why: with two engines answering the same version, a
diagnosis run against one says nothing certain about the other. So the order is RK79
first. Worth stating that the CLI is not the fallback here but the workaround — a tool
whose own commands have to be excavated is one an agent will keep using at four calls
where one would do.

### §RK82 The read verbs arrive after the read

Observed directly. A session opened with a `grep` of the governed roadmap and a load of
the project's own skill in the same batch of calls, so the instruction not to read the
file arrived in the same result set as the file's contents. Nothing that was resident
beforehand mentioned that reading was covered — the always-loaded line says the three
files are "owned by roadkeep, never hand-edited", which is a rule about writes.

The asymmetry is the point. The write side has an instrument: a PreToolUse hook that
refuses and names the command. The read side has prose in two non-resident places. A
convention with no instrument is one every fresh session rediscovers by breaking it, and
this one costs tokens rather than correctness, which is why it survives.

Two candidates. A `SessionStart` hook injecting one line — the three files, `brief` to
start, `ship` to finish — costs about twenty tokens once and removes the class. A
PreToolUse matcher on the read tools that **warns** and names `brief`/`list` would catch
what the line missed. It must never refuse: `lint` emits file-and-line, and editing the
prose of those files is legitimate work.

### §RK85 The report the reporter cannot write

Four projects now drive this tool through agents, and the defects they find are found in
sessions that end. What reaches the maintainer is a sentence composed after the fact, in
the genre this repository exists to distrust: the 142-word roadmap line is the same
author, writing the same way, about a different subject.

The asymmetry is that the losing session holds everything an identification needs and
none of it is prose. The argv, the exit code, `roadkeep.toml` as it was read, the engine
that actually answered, and the input line with its `file:line:column` are all facts the
process already has. RK79 is the dep because the engine field is the one that decides
whether a report is a defect at all: with two trees answering `0.1.0`, a stale plugin
cache and a real bug are indistinguishable, and the maintainer pays for the difference.

The shape that keeps L2 is a capture, not a client: re-run the failing command under
observation, emit the facts, and stop. No network in the default path, no state file in
the adopting repository, nothing to authenticate. What it emits should be a task line for
*this* backlog, symptom and `why` already inside the limits, so the schema is enforced in
the session where the claim is made rather than in the maintainer's review of an issue.
Delivery is a separate command somebody types, and is filed separately.
