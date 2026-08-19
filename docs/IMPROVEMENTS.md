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

### §RK1258 The first task in a block is shaped differently, and nobody chose that

`anchors --only-next` answers with a top-level family, and `add --ref XXXI` files the
task's rationale **as** that family: one `## XXXI <task title>` holding the prose. Every
later task in the block gets `--ref XXXI.1`, a `### ` child under it. So a block's first
task is structurally different from its siblings, and the difference is not a choice
anybody made — it is what the only available address produces.

Reaching the ordinary shape afterwards does not work either. `section_add --anchor
XXXI.1` charges the subtree to the parent, so a family with a lead paragraph and one
full-length task section is refused at 470 words against a 250 limit — while families
built the other way sit at 1239 words and are fine. Two doors to one structure, with
different limits on each.

Found in Shio, where it cost a red build. Its guards read rationale headings as `###
<FAMILY>.<n>`, which every task had produced until a block's first one produced `##
<FAMILY>`; three checks read past it and only the noisiest complained. Those guards are
widened now — but nobody met the shape in a hundred tasks because it appears only on a
block's first line, and it appears because no verb offers the alternative.

What is missing is one call that says *open the family, and file this task under it as
`.1`* — `add --ref XXXI.1 --section`, creating both. Then a block's first task and its
fifth look the same, which is what a reader assumes.

### §RK1261 The number that names the wrong field

Shipping a task whose design turned out wrong takes two arguments, and the refusal that
comes back describes one. Observed today: `--why` held 183 characters and
`--superseded-design` held 166, and the answer was `why: 385 characters, limit is 200
... delete 185 characters — about 29 words`. Read literally it asks for a `--why` of 15
characters, which is not what any of it means. The 385 is the rendered sentence — both
fields plus the parenthetical and the section address the ledger adds — attributed to
the field whose name is on the front.

The cost is a wrong edit. The obvious response is to cut the outcome sentence, which is
the half that has to survive: the ledger's entry is what remains after the design is
deleted. The half that can go is the supersession note, and nothing in the message
points there.

Two fixes, and the first is most of it. Name the parts in the number: what `--why` took,
what `--superseded-design` took, what the render added, and which one has room. `add`
already does this shape for symptom and why sharing a line, so the vocabulary exists.

The second is `budget`, which reports a shipping budget today without knowing that a
supersession will be appended to it. A task about to lose its design is exactly when
that budget is consulted, so the number it gives is wrong precisely when it is asked.

### §RK1262 The flag the message did not name

`ship <id> --part "..." --why "..." --remainder "..."` refuses a remainder with no
terminator, and it should: the remainder becomes the open line's why, and a why is a
sentence. What it says while refusing is `why: why is a sentence: end it`.

Both arguments on that command line are whys by the time the check runs - the one the
ledger entry takes and the one the reopened line takes - so the message is true and
still does not identify which string to fix. Measured from a session that had just
terminated its --why correctly, read the error as being about that argument, and had to
reason from the fact that nothing else could be wrong.

The field name the check reports should be the flag the caller typed, not the role the
value plays inside the transaction. Everywhere else a refusal names the thing on the
command line, which is why this one reads as a contradiction rather than as a hint.

Small, and the sort of thing that only shows up under a caller who is not looking at the
source - which is the caller this tool has.

### §RK1263 amend rewrites a section to change a word

Clearing a corpus of dangling section pointers is eight sections whose prose is right
except for one reference each. `section amend` is the only door — the hook denies the
hand edit, and rightly — and it takes the whole body.

So the fix for one stale pointer is: copy the section's table, json5 fence and block
quote out of the file, retype the one clause, pass all of it back. Eight times. Each
round-trip can drop a pipe from a row or a backtick from a fence, and nothing checks —
the body is prose to the tool, so a mangled fence validates exactly like a clean one.

It fights the word limit from the wrong side too. A legacy section already sits near the
limit for reasons the pointer has nothing to do with, so a four-character edit is
refused for length, and the way out is shortening prose the caller never came to touch.

What is missing is a way to say which bytes change. A `--replace old --with new` form,
refusing unless the old string occurs exactly once, makes the common case a one-line
call whose blast radius is visible in the call itself. The whole-body form stays for a
real rewrite, and the same shape serves `amend --why`, where correcting one clause of a
long ledger sentence means retyping it.

Filing this hit it once more: quoting a stale pointer as the example was refused as a
dangling citation.

## Block C — Query

## Block D — The gate

## Block E — Adoption

### §RK1259 The pause a project cannot take yet

`defer` exists because a pause spelled as a retirement is terminal, and it refuses when
`[files]` declares no `deferred` path. The refusal is exact — add the key, create the
file with its block headings — and it arrives at the worst possible moment.

Observed on an adopting project: its one open line was an idea waiting on a number no
task can produce — real traffic against a site not yet deployed. `pick` offered it and
would go on offering it, `brief` explained it, and neither said the only verb able to
set it aside was unconfigured here. The reason sentence was composed first and refused
second, which is the failure this tool names everywhere else: a limit reported after the
prose exists is a limit discovered too late.

Two doors, and they are not equivalent. `adopt` and `init` could write the store with
everything else, at the cost of a fourth governed file most projects never open. Or the
refusal becomes its own remedy: `repair` already applies findings whose fix is one
command, and this fix is one command — write the key, create the file, mirror the block
headings that already exist. Then the cost is a confirmation instead of a detour into
toml with a half-written sentence in hand.

Either way the cheap half is the earlier surface. `brief` and `pick` read the config
already, so they can say a line cannot be paused before anyone tries.

## Block F — The plugin

### §RK1260 Advice for a shell that is not there

Four field descriptions carry the same clause: `'-' reads stdin, which is how an
apostrophe or a backtick survives a shell`. It is good advice and it is addressed to
someone who is not there. Over MCP there is no stdin and no shell — the caller sends
JSON, where an apostrophe survives on its own — so the sentence spends tokens in every
schema an agent loads to describe a channel that agent cannot use.

The half that costs more is what stands in its place. The CLI answers a refusal cheaply:
`--section-body-file` means a body rejected at 257 words is edited in the file and
resent as a path. The MCP `add` has no such argument, so the same refusal costs the
whole 250-word body again — and length refusals are the common case, by design, because
this tool refuses before it writes. The surface where prose is most often composed is
the one where a rejected draft is most expensive to resend, which inverts the CLI's own
reasoning that a limit discovered late is a limit that failed to save anything.

Two candidate shapes, and they compose. Say the true thing per surface, so the MCP
schema describes JSON rather than shell quoting. And give the MCP verbs the file
argument the CLI already has, at which point a refusal costs an edit and a path in both
places. Neither needs a new concept — only the file path already implemented, exposed
where the agents are.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1257 The field with no door (block retitle)

A block's title is metadata, not a claim. `block add` refuses a label it already
declares — correctly, since reopening one is a different act — and there is no `block
rename`. So a wrong title has one exit: `retire` the tasks under it, `block drop`,
`block add` with the new title, `add` them back. That spends an id, writes a departure
that never happened, and deletes a rationale section that was right. It is what
`restate` exists to avoid for a symptom, and the argument carries over: the field is not
a claim the line makes, so correcting it should not read as abandoning work.

Found in Shio, and how it was found is the argument. A block was opened as *"what SH780
and SH807 fixed in one place and not the others"*, and a guard there refuses a heading
in the rationale file whose named ids have all shipped, since one reads as rationale for
finished work. The title was wrong on a rule its author had not considered — not a typo,
not a change of scope, a heading that should read differently. Its task was finishable
that session, so shipping it and dropping the block cleared the guard. Otherwise the
only exit was the expensive one.

`block retitle <label> --title` writes all declared files or none, as `block add` and
`block drop` do — the ledger included, since it keeps the heading history was filed
under and must keep it spelled the same way.
