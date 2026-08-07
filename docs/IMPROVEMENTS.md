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

### §RK385 Nothing notices that a new line asks for what a shipped entry already delivered

RK340 shipped on 2026-08-05: "outline anchors are one namespace across prose roles". On
2026-08-06 RK378 was filed asking for a per-role anchor namespace. `add` accepted it,
`lint` passed it, `pick` offered it, and the duplication surfaced only when a worker
claimed the line and went looking for the code. RK382 repeated it a day later against
RK178.

A lexical match at write time, above a declared threshold, was the mechanism proposed
here. This ledger labels four supersessions and two survive in history as filed;
measured against those, it **does not separate them**. Over the symptom alone RK340
places 9th of 382. Over symptom and `why`, RK378 → RK340 ranks 1st at 0.277 while RK382
→ RK178 ranks **33rd** at 0.125 — against a median 0.208 for an ordinary line's nearest
*non*-duplicate, so the true match scores below the typical false positive. Narrowing to
rare tokens moves the two ranks apart and lifts neither. An alphabet of identifiers is
emptier still: 192 of 382 entries name none.

The reason is in the pair. RK382 and RK178 state one problem in disjoint vocabularies,
which is what a problem discovered twice looks like — recognising it takes meaning, and
L4 has no model.

So the threshold is the wrong instrument and the symptom stands. What is untried is
exactness rather than similarity: a read the author is told to make before proposing, on
`non-goal list`'s precedent, where the tool states what a block already delivered
instead of guessing which entry is yours.

### §RK399 Name the marker field once across the verbs

`add --status 💭` and `resume <id> --marker 💭` write the same field, read from the same
`[markers] open` list, and are spelled differently. The skill's prose calls it a marker
throughout — "the shipped marker never reaches the roadmap", "`--marker` is where you
say which it was", `[markers]` is the config section — so a caller who has read the
skill reaches for `--marker` on `add` and gets an argparse usage dump with no hint that
the field exists under another name.

`status <id>` being a third spelling is fine: that one is a verb because moving a marker
is an act. The flag is not.

Take `--marker` as an alias on `add` (and `--status` on `resume`, so neither direction
is the wrong guess), or rename one and keep the other accepted. Whichever way,
"unrecognized arguments" is the wrong answer to a caller who named the field correctly
and the verb's synonym for it wrongly.

### §RK400 Name the parent a ship just emptied

`ship` deletes the task's own `§<id>` section and already names any section whose prose
cited what it deleted. Under an outline it leaves one thing standing that nothing names:
the **parent** the deleted children hung under. That paragraph was written as an
introduction to them — it states the problem they solve, in the present tense, often
under a banner about what is or is not worth building.

Shipping the last of `§X.1`–`§X.4` therefore leaves `§X` telling a reader the work is
open, sometimes that it is on hold, and always describing a defect the ship just
removed. It is the first thing anyone reads about that family and the only part of it a
ship never touches.

The fix is one line in the ship's answer, alongside the citation one: *"§X now has no
subsections — its prose introduces work that shipped"*. Deciding what it should say
instead is a `section amend`, and a judgement; noticing is not.

## Block C — Query

### §RK396 A dep on a partially shipped task is annotated as satisfied

Turing's T927 was shipped with `--part "the seven with a same-major patch"`. The line
stayed open and marked ⏳, exactly as designed: seven advisories were remediated, one
needs a major migration.

A task filed afterwards with `--dep T927` was written as:

```
- 📋 **T933** (deps: T927 ✅) ...
```

The ✅ is wrong in the way that matters. `T927` is `⏳ open` — `show` says so on the same
corpus, in the same breath. The annotation is derived from the ledger holding the id,
and `--part` puts it there while the work is unfinished, so the two readings disagree.

The consequence is the one dep annotations exist to prevent. A reader picking work sees
a satisfied dependency and starts; if what they needed was the unshipped half — here,
the react-router migration rather than the version floors — they are blocked by
something the roadmap told them was done. `pick` and `deps` inherit the same reading.

The fix is to source the annotation from the line's own state rather than from the
ledger's membership: shipped when no open line carries the id, and something
distinguishable when one does — `T927 ⏳` reads correctly and needs no new vocabulary,
since the marker is already the line's.

## Block D — The gate

### §RK380 A block can carry open lines for months and be found missing only by the first ship

Turing's Block BV carried eight open lines and no `## Block BV` heading in
`CHANGELOG.md`. Nothing said so. The first `ship` refused:

```
no heading declares Block BV in docs/CHANGELOG.md
```

which is a good refusal — it names `block add BV --title "<its title>"` and even warns
that `B` shares a prefix with `BV`. The cost is *when*. A ship is the end of a task: the
code is written, the tests pass, the commit is drafted, and the author is now told the
backlog was mis-set-up before any of it started.

`add --block BV` is where the fact is available and where nothing is at stake yet. It
has the config, the label, and `declaring`-style access to the ledger. Either refuse
there with the same message, or write the heading in the same transaction, the way `add
--section` writes the rationale rather than leaving a pointer to nothing — the precedent
is in this tool and the argument is the one that verb already makes.

`lint` is the other half: a roadmap block with open lines and no ledger heading is a
finding, and reporting it costs one pass rather than one ship.

### §RK391 The door the scaffold closed, and the three still open

RK390 made `init` refuse two `--block` values sharing a label, because one heading twice
is a file no verb can address. It was one door. A roadmap edited by hand, brought under
the tool by `adopt`, or merged from two branches reaches the same state, and there:

    lint            docs/ROADMAP.md: 2 line(s), clean
    add --block A   files under the *second* heading

That is L1 read the wrong way round. The law is that the schema is enforced where the
text is created and `lint` is the backstop — not that the write path is the only way in.
Every other rule here has both ends: a symptom too long is refused by `add` and reported
by the gate. This one now has the first and not the second.

What the gate would say is not obvious, and it is the reason to decide rather than to
default. `block.repeated` naming both line numbers is the honest report. But the
changelog and the rationale file are filed under the same headings, so the rule is about
a label across the governed set, and a project mid-adoption may have a duplicate it has
not reached yet — which is an argument for the finding and against making it the thing
that stops a first `lint` from ever passing.

Also worth naming: `add` picking the last of two is not a decision anybody made. It is
what scanning to the end leaves, and whichever way the gate goes, a verb resolving an
ambiguity by position is the part that should not survive.

### §RK398 The version bump the hook writes is never staged again once both files are dirty

Measured over eight commits in one session. The two version files stood dirty at the
start — another session had left them so — and every commit afterwards printed `carries
an edit this hook did not write; version bumped in the working tree, staged nothing`.
The checkout reached `0.1.392` while `HEAD` still said `0.1.388`: two shipped commits
carried no bump, and RK153's guarantee was off.

RK320's guard is right about what it refuses: `git add` takes a path and not a diff, so
staging a file that already carried an unstaged edit files that edit under this commit's
message. What it has no exit from is the state it creates. It writes the bump into the
working tree unconditionally, which *is* an unstaged edit to both files, so the next
commit reads `foreign` again. Only a hand-staged commit ends the loop — and the hook is
what starts it.

The repair the shape suggests is a comparison rather than a flag. What makes an edit
foreign is that it is not the one this hook wrote, and the bump is derived from the
committed number: read the index, derive what would be written, and stage where the tree
holds exactly that. A file differing by anything wider stays refused, which is the case
RK320 measured.

Left undone because it is shell in a hook that must never block — every path out exits 0
— so the change wants its own commit and its own test.

## Block E — Adoption

## Block F — The plugin

### §RK366 A shipped text whose wrap nothing holds

Measured on the file as it ships: 299 non-blank body lines, 223 of them (74%) between 85
and 96 characters, 24 over 110, the widest 283 — and six orphans under 30 mid-paragraph
(`not on PATH.`, `refusals, with`, `silence). On a`). One pattern produced all of it:
text appended to a line rather than the paragraph re-wrapped, which leaves the insert's
tail short and the line it landed on long.

Nothing renders differently and nothing costs more tokens, so the cost is **review**: a
diff of a 283-character line is a whole-paragraph diff, in the file every adopting
project loads on the turns that touch a governed file. A change somebody skimmed here is
a rule every agent reads.

The decision is which of three, and the third is legitimate. A width in `roadkeep.toml`
with a `lint` finding makes it configuration rather than convention (L6), and puts this
tool a step from a Markdown formatter it has no reason to be. A `--fix` repair is worse:
re-wrapping a paragraph is rewriting somebody's line, and only the *derived* is repaired
(RK16). Or nothing is held, the file is re-wrapped once by hand, and the cost stays with
the reader who has the diff.

What would decide it is whether an edit here was ever actually mis-reviewed, which `git
log -p` on this file can answer and this section cannot.
