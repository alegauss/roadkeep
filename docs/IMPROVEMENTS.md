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

### §RK368 The correction a non-goal has no door for

RK367 changed one clause of a non-goal's reason and had to drop the bullet and write it
again, that being the only door. The lead is the address and `non-goal add` inserts
after the last one there, so a constraint that sat fifth of eight now sits eighth: a
reviewer reads a deletion and an addition where a word moved, and the order a reader
takes for the shape of the list changed for a reason no commit is about.

The ledger settled this one layer up. `record amend` exists so that a correction is not
a move — never drop-and-re-add, which shows a reviewer a deletion where a word changed —
and `section amend` is the same door for a design that would otherwise be write-once
until it shipped. The non-goal list is the third bullet grammar this tool owns and the
one that never got one.

The shape the other two settle: `non-goal amend <lead> --why …`, rewriting the reason in
place, filled to the same width, the bullet's position untouched. Not the lead, which is
the address — `drop` plus `add` is right there, and is what the skill already says a
changed lead takes. Which leaves whether that asymmetry needs stating in a refusal, or
follows from the argument closely enough to cost nothing.

### §RK377 A doubled anchor has no verb that repairs it

`_refuse_doubling` stops a *new* section from taking an address a sibling prose file
already declares, and `lint` reports every pair already there. Neither helps a corpus
that arrives with the collision: Turing adopted roadkeep with 13 anchors declared by
both `IMPROVEMENTS.md` and `STRATEGY.md`, and there is nothing to call.

The machinery is already written. `renumbering._rename_anchor` re-addresses a section
and every subsection whose anchor extends it, in one transaction. It is simply
unreachable here: `renumber` moves an *id*, and line 172 keeps the pointer as
`entry.task.ref` unless `ref_scheme == "id"` — so under `outline` the anchor never
moves, which is precisely the scheme a project with a hand-kept outline is on.

Nothing else is a door. `section amend` says so itself — "Neither is the anchor itself,
which is `renumber`'s" — and `add` plus `drop` is not a rename: it loses the section's
place in the outline, and `drop` refuses while an open line points at the anchor, which
is the case worth repairing.

What is missing is the reachable form: `section move <from> <to>`, or `--anchor` on
`section amend`, taking the refusals `add` already computes — refuse a target another
file declares, refuse an address history spent.

Turing's T902 is the case in hand.

### §RK381 A refusal on a short field costs the whole rationale a second time

`add` validates everything before writing, and the docstring says why: "a limit reported
after the prose exists is a limit discovered too late to save the tokens it was meant to
save." That reasoning stops one step short. Nothing is written, but the *body* is
already spent — it came in on stdin, and stdin does not rewind.

Measured, on one `add` against Turing: `--why` was 215 characters against a limit of
200. The refusal was correct and precise ("delete 15 characters — about 3 words").
Acting on it meant resending a 184-word `--section-body` heredoc unchanged, to fix
fifteen characters in a different argument. For an agent composing these, the body is
the expensive half by an order of magnitude, and it is the half that was never in
question.

`--section-body-file <path>` fixes it completely: the retry re-reads the file and costs
the corrected `--why` alone. It is also the more natural form for prose that was drafted
somewhere before it was filed, and it leaves `-`/stdin exactly as it is for the piped
case.

Cheaper still, and complementary: validate the scalar fields before draining stdin, so a
refusal that cannot succeed never consumes the body at all.

### §RK382 A symptom that discovery widens has no verb, only retire and refile

`amend` states the rule plainly: "The `symptom` is not amendable — it is the claim the
line is, so a different one is a different task." That is right when the claim is
different. It cannot distinguish a *different* claim from a *widened* one.

The case, from Turing. T917 was filed as "The showcase build rewrites a tracked file on
every run". Running the full matrix an hour later showed the same `gen-manifest`
stamping three marketplace apps too — same script, same defect, same fix, three more
instances. The task was not different; its symptom was now false, naming one app out of
four.

The doors available were all wrong. `amend --why` and `section amend --title` took the
correction, so the line said "showcase" while the prose beside it said "four apps" — the
divergence RK's own design note tolerates, here caused by the rule rather than by an
author. `retire` plus a fresh `add` would have been honest about the symptom and
dishonest about everything else: a new id, a dropped dep edge, and a retirement that
reads as abandonment.

What is missing is the narrow door: `amend --symptom` gated on the existing text being a
**prefix-preserving widening**, or an explicit `--widen` that records the old spelling
in the ledger rather than discarding it. The audit trail is the point — the reason to
refuse a silent rewrite is not a reason to refuse a recorded one.

### §RK385 Nothing notices that a new line asks for what a shipped entry already delivered

RK340 shipped on 2026-08-05: "outline anchors are one namespace across prose roles". On
2026-08-06 RK378 was filed asking for a per-role anchor namespace, with a rationale
naming the exact configuration RK340 had written. `add` accepted it, `lint` passed it,
`pick` offered it, and the duplication surfaced only when a worker claimed the line and
went looking for the code to write.

The ledger is the file that already held the answer, and it is greppable by construction
(L2). Nothing consulted it. `add` reads the backlog for the next id and reads nothing
else, so the one question worth asking before a line is written — has this shipped? — is
the question the write path never asks.

The refusal is the wrong shape here: a symptom that overlaps a shipped entry is often a
real second problem, and a hard block would be wrong more often than right. What is
missing is a *warning at write time* naming the entries whose symptom is close, printed
before the line lands, on the same argument as every other pre-write check — the saving
is the analysis, not the characters.

Two constraints bind it. No model and no prompts (L4), so the match is lexical and the
threshold is declared, not learned. And it stays advisory, so a false positive costs a
sentence read and never a re-filing.

Related: RK382 is the symptom that changed; this is the symptom already answered.

### §RK388 The line no round-trip covers

Under `ref_scheme = "outline"`, `section amend I --body …` rewrites the heading above
the body it was asked to change:

| on disk | after the amend |
|---|---|
| `## §I A design` | `## I A design` |
| `##  I   A design` | `## I A design` |

Both parse. The reader takes the sigil as optional here — a bare `0.1` is what an
outline heading looks like on disk — and then `anchor_text` writes the canonical form,
so a file that opened with `§` loses it on the first write to any section in it. `lint`
reports the same file clean, and `adopt --sections` reports `1 conform, 0 would change`.

L3 is round-trip **or refuse**, and this is neither. What holds it is `Document`, whose
mutators refuse the whole file when a line they parsed would render back differently —
and that check runs over entries. A rationale file has none, so `non_canonical` is `()`
for every prose file ever measured, not because they round-trip but because nothing
looked.

What is not obvious is which way the repair goes. Refusing the file is L3 as written and
turns an existing `§`-under-outline project into one no verb will write to until it is
migrated. Accepting the sigil as canonical under both schemes keeps those files writable
and makes the anchor two spellings, which is what RK340 spent a task removing. The third
answer is that the reader stops accepting what the writer will not reproduce.

### §RK395 A shipped entry that gets reverted stays in the ledger saying it shipped

Turing shipped T922 and T924, then reverted both an hour later: they had read a
deliberate configuration change as an accident. Recording that took three attempts at
the wrong verb.

`retire` starts from an open roadmap line, and `ship` had already removed it. `record
drop` refuses anything but a duplicate — rightly, and its message is the argument:
"removing the only record of a decision is deleting history rather than de-duplicating
it." What remained was `record add`, writing the revert as a new entry.

That is the correct model — the ledger is history, and both the ship and the revert
happened — but the two entries do not know about each other. A reader who finds T922
sees an entry that says it shipped, with no forward pointer to the one saying it did not
hold. `retire --superseded-by` exists for exactly this shape one file over; the ledger
has no equivalent.

What is missing is small: `record amend --superseded-by <id>`, or a `record revert <id>
--why`, that writes the new entry *and* appends the pointer to the old one in the same
transaction. The precedent and the wording are already in `retire`; only the target file
differs.

## Block C — Query

### §RK379 The refusal for a missing anchor does not name the anchor to use

`_check_ref` returns one static string — "every task points at its rationale section" —
and nothing else. Under `ref_scheme = "outline"` that is every `add` an author writes
from memory, because the anchor is not derivable from the id and so cannot be defaulted.

The value the message wants already exists. `anchors --family <x>` ends with `next
§LXIX.9 — nothing ever used it`, computed from the live headings and the retired ones
history holds. The refusal is raised in a schema check that does not have the corpus,
but the caller that reports it does: `add` has the config and the block, and the block's
existing lines say which family this line joins.

Measured on one session against Turing: four `add` calls, each costing a refusal, an
`anchors --family` and a retry. The retry is free once the first message says `--ref
LXIX.9`.

The same argument as RK144's, one field over: a refusal that states the rule without the
value teaches the schema, and a refusal that names the value ends the turn.

### §RK383 The free-address help says one outline spans both files, which a declared namespace makes false

`anchors --role` documents itself as narrowing the listing and never the free address —
"the free address stays the project's either way, since one outline spans both". The
comment above `_anchors` says the same thing in the same words. Both were written when
one outline did span both files.

RK340 ended that. `next_family(spread, space)` is computed per namespace, and RK346 made
`--json` answer one row per namespace precisely because a single free address stopped
being the truth. So on any project that declares `[refs]`, the sentence the caller reads
before running the command contradicts the number the command prints.

The damage is not a wrong answer; it is a caller who believes the answer is project-wide
and picks a top-level out of the other file's namespace, which is the collision `[refs]`
exists to end. Help that was accurate is worse here than help that was missing: nothing
prompts a re-read.

The repair is two sentences, conditioned on nothing: state that the free address is per
namespace where one is declared, and that a project declaring no `[refs]` has one
namespace and therefore the old behaviour. That keeps a single sentence true for both
shapes instead of documenting the default and leaving the configured case to be
discovered.

Related: RK340 shipped the namespace, RK346 shipped the per-namespace answer, and this
is the prose neither of them carried forward.

### §RK389 A dep naming two real ids is accepted as one thing outside the backlog

`--dep` is repeatable and takes "an id, 'Block X', a range, or work outside the
backlog". The last arm is free text, so anything the first three do not match is
accepted as-is. `--dep "T919 + T922"` therefore lands as a single external dep.

The result parses and reads plausibly. `deps` is where it surfaces:

```
T919 + T922  unresolvable external outside the backlog: nothing here will
             ever mark this done
chain    T923 → T919 + T922  — outside the backlog: shipping cannot satisfy it
```

Both ids are real, one already shipped. The line claimed to be blocked forever on
something that does not exist, and nothing said so at write time — `add` succeeded, and
the finding required a separate `deps` call to notice.

Free text is the right arm to have: Turing's T902 legitimately depends on `roadkeep
RK378 + RK377`, this tool's backlog, which is exactly what it is for. The gap is that
the two cases are indistinguishable to the writer.

The cheap discriminator is already computable: if the free-text value **contains** one
or more ids matching this project's `prefix` pattern, it is almost certainly a compound
the author meant as separate `--dep` flags. Refuse it, and say so — "`T919 + T922` names
2 ids; pass `--dep` once each" — rather than storing a dependency nothing can ever
satisfy.

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
