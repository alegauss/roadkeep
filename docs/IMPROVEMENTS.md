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

### §RK426 One refusal per call, not one per field

`add` refuses the fields at input, which is the right design and the reason nothing
half-written reaches the file. It refuses them **one at a time**. A call whose `why` is
245 characters and whose `--section-body` is 302 words is refused twice: once for
`why.too-long`, and then — after the sentence has been rewritten and the whole call
resubmitted — for `body.too-long`, a limit the first refusal already knew was breached.

Measured filing four tasks across two projects in one session: seven refusals, of which
two were the second limit of a call whose first had just been fixed. Each costs a full
resubmission, and `--section-body-file` exists precisely because resubmitting the prose
is the expensive part — so the tool has already conceded that a refusal's cost is the
re-passing, and then makes the caller pay it for a field it never looked at.

The remedy is to validate every field and report every breach in one refusal, in the
order the schema declares them. The message shape is already right — each finding names
its code, its measurement and its delta — so this is a change to how many findings
print, not to what one says.

`--json` gains the same: a caller correcting programmatically wants the list, not the
first entry of it.

## Block C — Query

## Block D — The gate

### §RK418 The number that could not answer this question before

The verb that reads the three copies back compares the two that state a version, and it
compares the **release string**. That is the exact fact an earlier task proved
insufficient: two `src/roadkeep/` trees, fourteen files apart, both answering the same
number — which is why the running engine carries its directory and its commit at all.

So the reader is one step short of its own evidence. Both copies carry a revision: the
running one from git, the installed one from the marketplace row that records the sha it
was built at. Both are read, both are printed, and neither is compared.

The case that gets through is the one a machine developing this tool is in every day. A
checkout at the plugin's own version, with uncommitted work, writes; the plugin judges;
the numbers match and the verb says they agree. The files do not.

What is *not* obvious is what agreement should mean once the commit is in it. A checkout
whose files are modified is not at any commit the plugin could match, so the honest
answer may be three states rather than two — agreed, behind, and unpinnable — and a
boolean that collapses the third into either of the others will be wrong for one of
them. That choice is the task; the numbers to make it with are already on the screen.

### §RK425 The named repair that makes it worse

`block.repeated` names its repair — *both regions hold work, so the repair is a merge by
hand* — and that sentence is correct and insufficient. Two facts decide whether the
merge succeeds, the gate knows both, and neither is said:

- **A rename is not a merge.** The obvious reading of "one label is one heading" is to take the
  label out of the second heading. That detaches every entry beneath it: the region ends and the
  lint becomes `block.missing` for each. Measured, renaming five headings produced 83 findings and
  had to be reverted.
- **A region ends at the next heading of *any* level.** A `###` cannot group entries inside a
  block, so the grouping title has to stop being a heading — a bold paragraph works. That is why
  the second attempt fails after the first is undone.

The cost is not reading time. `ship` refuses a repeated label outright, so the caller
holds an unrelated diff and a task they cannot land, and each wrong repair is a
write-and-revert of a file the guard otherwise forbids them to touch. Three of twelve
blocks were unshippable here.

The fix is in the message: say what the entries must do — move into the one region,
keeping the file's existing order — and what the title must become, with both as
`--json` fields. The tool knows both regions' line ranges, so printing them is the whole
of what a caller works out by hand.

### §RK427 The finding in one file, the door on another

RK325 moved the queue out of `roadkeep.toml` and into a `## Priority` section of the
roadmap, for a good reason: every token in it names work, and work leaves, so the config
was the one file nothing governed. A project that has not migrated still declares it in
the config — and `lint` still reads it there, which is right.

The two halves disagree about where the queue is. `lint` reports `priority.shipped` and
names **`roadkeep.toml`** as the location. `priority drop <id>` — the verb whose whole
job is that repair — refuses with *no priority heading in docs/ROADMAP.md*, having never
looked at the file the finding named. So the gate reports a defect in a file the door
will not open, and the only way out is the hand-edit the tool exists to replace.

Measured: shipping a task whose id led the queue produced the finding, and the drop that
answers it could not run.

Three ways to close it, in increasing order of what they cost. `priority drop` and `add`
operate on whichever declaration `lint` read, since it already resolves that. Or the
refusal names the migration as the fix and prints the tokens to move. Or `lint` declines
to report a finding no verb can repair — which is the worst of the three, because the
drift is real.

The first is the one that matches how the codes are supposed to work: a finding names a
door, and that door opens.

## Block E — Adoption

### §RK402 The tree that ships the plugin is told to wire the guard a second time

`install --check` is what holds this checkout's own wiring in step. Run here it reports
`1 surface(s) differ`, permanently: `.claude/settings.json` `would update`, because the
guard's hooks are not in it.

They are not in it because this tree ships them as a **plugin** — `hooks/hooks.json`,
referenced by `.claude-plugin/plugin.json`. Writing them into the project settings too
would run the guard twice on every turn, which is precisely the reason the same command
already skips two other surfaces by name:

```
not written  .github/workflows/roadkeep.yml: this tree *is* the action, and its own
             workflow already calls the gate — a second one would run the same lint twice
not written  .claude/skills/roadkeep/SKILL.md: this tree ships skills/roadkeep/SKILL.md,
             so a copy of it here would be the drift `install` exists to remove
```

The hooks are the third member of that set and the only one missing from it.

The cost is the signal, not the file. A check that can never report clean is one nobody
reads, so the drift it exists to catch — a `.mcp.json` that fell behind, a launcher path
that moved — arrives inside a report that already said "1 differs" yesterday.

The repair is a skip with a reason, spelled as its two siblings are, conditioned on the
tree providing the plugin rather than on this repository's name.

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
