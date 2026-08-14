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

### §RK1187 The prose field the pipe convention skipped

RK329 made every prose argument read the pipe and RK1176 moved the claim into the
parser, resolved once in dispatch with the two-into-one refusal asked for every verb.
`add` declares two readers, the body and the `why`; `restate` declares none. So
`symptom` is the field the convention skipped, and `restate` is the verb with no pipe at
all — the one whose only prose argument is a symptom.

Refusing `-` by name is the wrong half of the door. A symptom carries the backtick, the
apostrophe and the `§` exactly as a `why` does, which the lines in this file
demonstrate: RK1184, RK1185 and RK1186 all quote a command in theirs. The field wants
the pipe for the same reason the `why` was the argument RK329 was really about, and it
is the field a shell most quietly corrupts, because a symptom that lost an apostrophe
still reads like prose somebody wrote.

Nothing downstream can catch it either, which is why the door is the parser's. A bare
dash is a one-character symptom: it clears every limit, renders, round-trips and passes
the gate, so the file keeps a claim no rule can call wrong. `restate --typo` is
untouched — a declaration is not prose — and `add --symptom - --why -` needs no new
refusal, being two arguments asking for one pipe, which dispatch already names.

## Block C — Query

### §RK1184 The criterion a design declares

RK492 gave a design its own fenced query and `remaining` runs it: one `<pathspec> ::
<regex>` per line, counted now rather than maintained as a number on the line. The
criterion that a task is done is the same read with the sign flipped — sites that must
exist rather than sites left — so it is a second fenced kind read by that parser and not
a second grammar.

What it is not: a verdict. The pattern is the author's claim and the count is the
answer, exactly as `remaining` states it, so `0` says the evidence is not there yet and
whether that is the work being done is the caller's judgement. The gate reports only a
block it cannot read, never a criterion unmet: work outstanding is not a defect in a
file, and a rule that failed a repository for unfinished work would be a rule every
green branch trips.

It is deleted with the section that made the claim, and that is right: the ledger's
sentence states the outcome, the criterion was about the work, and a shipped entry
keeping a query would leave a claim nobody can close. Under L4 the tool writes none of
it — the pathspec, the pattern and the decision that the pattern is evidence are all the
author's, and this only counts and reports.

### §RK1185 The criterion at the start, not at the ship

RK1184 makes the criterion a fact a design states; this is the call that hands it over.
`brief` is what starts a task — the line, the rationale, the deps resolved, the blocker
chain, what it unblocks and the non-goals, in one call — and a criterion read after the
code is written is one that shaped nothing. The order is the whole point: the claim the
work will be measured against arrives before the first edit, which is RK1174's argument
about the `why` budget made about evidence instead of about characters.

It is a count and a quotation, not a gate: `brief` refuses nothing, and a criterion no
site satisfies yet is the ordinary state of a task about to start. The cost is what
decides the shape — this answer is bounded to a tool result, so the block is printed as
the clauses the design declared plus the count each one matches now, and never as the
files behind them, which is what `remaining` is for once the work is under way.

A design declaring no criterion is answered and not annotated. Most tasks here state one
in prose and always have; a line that says nothing extra is a line whose author had
nothing extra to say, and printing an absence every turn is a nag the tool has no
standing to make.

### §RK1188 The one question before every add has no verb

`add --block <x>` is the first flag on the first write of any new task, and nothing
answers what `<x>` can be. `stats` prints letters and counts, never titles. `list
--block` and `delivered <block>` both demand the letter as an argument and refuse one
nothing declares, so neither can discover it. The guidance to place a task in the block
whose theme covers it is guidance against a fact the tool does not state.

So the author reads `docs/ROADMAP.md` with grep. That is the file the hook exists to
keep hands off, and the habit it teaches is the one every other refusal is spent
unteaching. Observed twice in one session on two different projects, the second time to
file this.

The shape is already there: `non-goal list` answers "what may I not propose" with no
argument at all, and this is its sibling — "where may I put it". Something like `block
list`, printing each block's letter, its title and its open count, in file order, since
order is what a reader takes for the shape of the plan. The counts `stats` prints are
the same read, so the two want to agree rather than be two answers.

Worth deciding: whether this is a new verb or `stats` learning the titles it already
walks past. The argument for a verb is that `stats` is a report about a file and this is
a question asked before writing to one, and `block add` and `block drop` already own the
noun.

### §RK1190 The allowance is knowable and the draft is not

RK190 made the allowance knowable before the first word exists, and that is not this.
`budget` answers "this line leaves 174 characters for `why`, this section 250 words". It
cannot be handed the draft. So the only thing that measures prose against its limit is
the write that refuses it.

Measured on one session driving another project: eight refusals on length, several of
them three or four retries for a single task, each costing the whole field again. The
refusals are good — they name the count, the limit, the deficit, and which paragraph is
longest — and none of that is reachable until something has been sent.

`--section-body-file` and `--body-file` already remove the *re-send* cost, which is the
half that was solvable without a new read. What stays is the round trip and the
guessing: told "delete 3 words", an author cuts and sends again, and the second answer
is "delete 1".

The shape is `budget --anchor RK12 --body-file draft.md`, and the same for a `why`, so
the subject flags that exist say what the draft is measured against. It counts with the
writer's own counter — a second one that disagreed would be worse than none.

Two things to settle. Whether it exits non-zero when over so a script can gate on it, or
stays a report like the rest of `budget`. And whether **stdin** is accepted here: a pipe
does not rewind, but this writes nothing, so the objection that shaped the writing verbs
does not apply.

## Block D — The gate

### §RK1172 Two phases, and the five inputs a rule reads

`remedying.py` states the argument outright: keyed centrally, a test can assert the
domain is total over every code the package emits, which turns adding a check without
stating its repair into a red. Only half is applied — the *remedy* is a table and the
*check* is not.

**Measured, because the scan kinds are the record's shape.** `_examine` makes **24 calls
across 16 signatures**, clustering into five inputs: the governed **tree**, the
**documents** carrying task lines, **one role's document**, the **prose** files with the
**anchor index** derived from them, and a git **revision** where a rule compares against
a baseline. Each is a fact about the project, and a record naming which a rule wants is
a loop where hand-wiring is.

**Three rules take none of them.** `_grammatical`, `_untainted` and `_ordered` are
handed the *findings so far*: they fold a file's non-canonical lines into one defect,
drop what another finding already explains, and put the report in its printed order.
Those read the report rather than the repository, and a flat domain has nowhere to put
them.

So the set has **two phases** and not one list: rules that read the project, and rules
that read what those produced. The record carries its input kind; the phase orders the
loop, and a rule reading findings declares it instead of being sequenced by where its
call sits.

What needs deciding next, once the record exists: whether `--fix` reads a field on it —
`fixing.py` keeps `REPAIRS` today — which is RK1173.

## Block E — Adoption

### §RK1186 The prose file a scaffold cannot create

The strategy file is a fully governed prose role and has been since RK172: a pointer
resolves against it, RK186 taught `show` and `brief` to name the file that declares an
anchor, RK196 kept the drop working across roles, RK229 carried it through a `defer`,
RK230 let the one-write door reach it, and RK340 gave it its own namespace. Every reader
is finished. The one command that creates a project's files is not: `init` writes the
roadmap, the ledger and the improvements file, and nothing names the fourth, so a
project that wants it hand-edits the configuration and creates the file — the two steps
a scaffold exists to remove.

The reason to want it is the split, not the file. A task's rationale answers why this
line exists and is deleted when the line ships; a document above the line outlives every
task filed under it, which is what a project working from a specification needs and what
the improvements file, by its own rule, cannot hold. `add --section` deriving
improvements stays exactly as it is: naming the role at both ends is two places that can
disagree, and a project declaring both makes the choice by calling `section add --role`.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1169 What is left of the six is one

`src/roadkeep/serving.py` derives every property's type, description and bounds from the
argparse action, and tabled what it could not. The first slice moved one: `WITHHELD` had
**no reader in the package** — only a test comparing it against the parsers — so each
reason now sits on the argument it explains, and both the table and that test are gone.

The remaining five were measured against the same question, and three answer it
differently:

- **`_BOUNDS` and `_CONDITIONAL` are keyed by *dest*, not by verb.** `symptom` means one thing
  wherever it appears, and one row answers for every verb that takes it. Per parser, one answer
  becomes six copies — this task's own drift, pointed the other way.
- **`_DIVERGENT` belongs to the served surface.** Its rows name JSON-Schema bound tables, so
  declaring it in `cli.py` would make the command surface import the server's vocabulary,
  inverting a dependency that runs one way on purpose: `serving` imports `cli` lazily and never
  the reverse.
- **`_DESTS` stays, as this already said**, owed a derivation checked against the parsers.

So what is left of the claim is **`TOOLS`**: which verbs are tools, and which of their
arguments a caller may set. That is the substantial one, and its facts are per verb and
per argument — the shape the first slice proved.

What needs deciding: whether exposure is a list declared beside the verb or a mark on
each `add_argument`. The second is where the fact belongs and the larger edit.

### §RK1170 One result, two registers, one place

`src/roadkeep/rendering.py` was cut out of a `cli.py` that had reached 8,489 lines, and
its own docstring says why the printers went first: theirs is the cut with no import
cycle. That was a fix for a file's size, and it is measurably not a fix for where a
verb's answer lives.

Counted now: `src/roadkeep/verbs/` makes 386 `print` calls of its own against 102
delegations, so the rule "the sentence is in the renderer" holds for about a fifth of
the printing. `weight` is the shape of it — the plain answer is spelled inside the
handler and `_weight_json` is in the other file, so one verb's two registers are two
files apart, and neither file holds both.

The two registers are meant to differ. Plain stdout is the value a shell composes with;
`--json` carries the provenance that makes an answer auditable. So the fix is not one
output. It is one **result** — a dataclass the handler returns — with both registers
derived from it beside the verb that computed it. The payload then carries what the
plain answer showed by construction, where today that is a test.

Do this before splitting the parser: once a verb owns its result and both its registers,
moving it is a move and not a rewrite.

### §RK1171 The module boundary is orthogonal to the change axis

Measured over this package: the command surface — `src/roadkeep/cli.py`,
`src/roadkeep/verbs/`, `src/roadkeep/rendering.py`, `src/roadkeep/serving.py` — is 7,781
of 24,405 code lines, or 32%. The kernel that the whole tool is about is 1,532, or 6%.
The essence is a sixteenth of what the surface costs.

The cause is not that any file is badly written. It is that the decomposition is by
**layer** — every parser together, every printer together, every served declaration
together — while the unit of change is the **verb**. So one verb's facts sit in five or
six files, and the last forty commits touch a median of nine to twelve files each.
`anchors` appears in sixteen modules; `remaining` in thirteen.

The fix is the law this project already applies to the line format, aimed one layer out:
the verb is one declaration, and `cli`, `serving` and `rendering` interpret it instead
of holding three parallel registries of it. `build_parser` becomes an index over those
declarations rather than a two-thousand-line function that every task appends to.

Its two deps are what make this mechanical rather than a rewrite. What must not be
reached for: entry points or dynamic discovery, which cost startup, need a dependency,
and take away the totality the gate is checked by; and a generator, which would move the
authority out of Python and out of reach of a type checker.
