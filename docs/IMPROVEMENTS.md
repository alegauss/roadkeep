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

### §RK1453 The one sentence nothing can rewrite

Every other governed sentence has a door back. A roadmap line has `amend` for its why
and `restate` for its symptom; a ledger entry has `record amend`, which the help text
argues for carefully — `drop` and `add` "would remove the entry and append a new one
under its block, so a ledger read in the order work landed stops being one". The
sentence `ship --decides` writes into `DECISIONS.md` has nothing.

`supersede` is not it, and says so: it is for a decision replaced by another, appends a
forward pointer, and requires both ids to be decisions the file already records. A typo
is not a replacement, and inventing a second decision to correct the spelling of the
first corrupts the record worse than the typo did.

Met while shipping FB5 in a consuming project: `--decides` was passed ASCII-only to
survive a shell, and the file now permanently reads "Menu do site novo e semeado" where
it should read "é semeado". The guard denies the hand-edit, correctly. There is no third
option.

The file's rule is that nothing in it is ever deleted, and that rule is right. But
correcting a sentence in place is not deleting an entry — it is what `record amend`
already does for the ledger, with the same argument. The door is missing, not forbidden.

### §RK1454 A refusal that is right, and reads as a fault

A project's end-of-block sweep tells the agent to run `block drop <x>` once nothing is
open — a heading standing over nothing is what that verb removes. Run at the boundary of
a block whose deliveries used `ship --decides`, it refuses:

    docs/DECISIONS.md files FB2, FB5 under Block D: a heading over work is not an empty
    heading, and removing it would file all of it under the block above

The refusal is correct. The heading addresses the decisions, not only the backlog, and
dropping it would refile them silently. What it does not say is what the caller should
do instead — and the caller was told this was the last step. An agent reaching it has
finished the sweep, hit a non-zero exit, and has to decide alone whether that is its
problem.

`block list` already knows the answer: it prints `empty` and `finished` as different
states, and a block anchored by decisions is the second. So the ending exists in the
model and is missing only from the message. Refusals elsewhere carry the alternative —
an unknown flag prints `takes` and `by order`, a bad `why` prints the gate code and what
closes it. This one prints the reason and stops.

Naming the outcome in the refusal — this block ends as `finished`; the heading stays
because the decisions file addresses it — turns a dead end into an answer, without
changing what the verb does.

## Block C — Query

### §RK1455 The block list nothing answers

Measured on 31 August 2026, filing against a FreeWilly backlog. Two new tasks had to be
placed, and the placement rule is to reuse an existing block — so the question to answer
first was what the blocks are.

Nothing answers it. `list` answers lines: unscoped over the ledger it returned 117,815
characters and was refused for exceeding the token ceiling, and `--block C` wants the
label being looked for. `status`, `remaining` and `pick` all answer about tasks. What
the caller does next is grep the governed file for `^## `, which is the one move the
hook exists to prevent and the one that worked. A rule the tool cannot serve got broken
by a caller trying to follow it.

So: a listing that answers the structure rather than the contents. `blocks` — each
label, its title, how many it holds open and how many the ledger records under it. Those
are figures `status` already computes one block at a time; what is missing is asking for
all of them without knowing their names. It would be the first call of a session that
has to file something.

The other half is the refusal. A listing that overruns should say which blocks it would
have printed and how many lines each holds: that answer is smaller than the one refused
and closer to what was wanted. A character count and a stop is what sends a caller to
the file.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK1451 The read that reconciles the copies, blind to one

Observed in Japode/cloud, which holds a vendored `.roadkeep/` from an earlier `install
--vendor`. Two engines are in play and the same command answers differently depending on
which one runs it:

    roadkeep engines                        writing 0.2.58    D:/Git/alegauss/roadkeep
    launcher engines                        writing 0.1.1269  ./.roadkeep/src/roadkeep

Both exit 0. Both say `plugin — no plugin is registered for this project`. Neither has a
row for the other, so the read that exists to reconcile the copies in play is the one
place a second local engine is invisible.

It decides who writes. `.mcp.json` runs the launcher, and so does the guard, so every
tool call and every denied hand edit went through 0.1.1269 — while a shell reaching
`roadkeep` got 0.2.58, two minor versions ahead. In the session that found this the MCP
server was down for an hour, so the whole write path happened to go through the newer
one; had it connected, the tools would have written under 0.1 and the shell's `lint`
would have judged it under 0.2, each reporting agreement.

Distinct from the three this block already closed. RK79 had two engines both answering
one version, and RK1167 had `engines` naming a version replaced in the registry — there
the number was wrong. Here each copy states its own version correctly, and the defect is
that the listing has no row for a copy that is not the one answering.

No prose was damaged: both engines called the governed files clean.

### §RK1452 One home, two versions, and a verdict of agreed

Reproduced in Japode/cloud in one session. The MCP server was started from
`.claude/hooks/roadkeep-launch.py`, which resolved a vendored `.roadkeep/` holding
0.1.1269. Later, `install --vendor` replaced that directory in place with 0.2.4. Python
had already loaded its modules, so the server kept running the old code:

    launcher --version   (disk)   roadkeep 0.2.4    .roadkeep/src/roadkeep
    engines  over MCP    (live)   0.1.1269          .roadkeep/src/roadkeep

One path, two answers, and the second is the one every tool call and every guarded hand
edit goes through. The payload says `"agree": true, "verdict": "agreed"`.

That verdict is the defect rather than the version. This verb's own contract is that
copies may differ and what is not survivable is being unable to say which one answered —
and here it names a version that path has not held since the vendor ran, then certifies
agreement about it. A caller has no way to notice: the number is plausible, the home is
right, and nothing in the answer is stale-looking.

Kin to two this block already closed, and the maintainer should judge whether it is one
of them. RK1167 also ended with `engines` naming a version replaced and not on disk, but
from registry rows rather than a live process; RK153 is about a session keeping an old
copy running. Neither has the in-place swap under a server that then certifies itself.

Cheap tell: the loaded version against what that home states now, read at answer time
rather than at start-up.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
