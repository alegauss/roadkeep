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

### §RK244 The third file, in the one command that still counts two

Reproduced on a project declaring all four files: RK2 paused in the store, and `retire
RK1 --superseded-by RK2` exits 2 with *"RK2 is in neither file, so it cannot be what
replaces RK1"*. Both halves are wrong. The id is in a file — the store — and the count
is stale: RK96 made it three files an id can live in, and `NoSuchReplacement` still says
two.

It is the failure RK92 named one layer over: a file loaded only where somebody
remembered to means a deferred id reads as "unknown" in every command that never heard
of it. The resolver was fixed then and `Backlog.load` reads the store for exactly this
reason, while this check builds its own set out of two `config.document` calls.

The state is also the *likely* one. Work is set aside because something else is going to
carry it, and the line that carries it is often the paused one somebody is coming back
to — so this refuses the supersession most worth recording, and the way round it is to
retire as abandoned, which deletes the pointer to the replacement RK32 exists to keep.

What to decide: `Backlog` is the reader that already answers this, and its `deferred()`
is the third lookup. Whether the answer should say *which* file it found the replacement
in is the smaller question — a paused replacement is a supersession waiting on a resume,
and a reader of the retired line has no other way to learn that.

### §RK249 Every other derived field is reported as one

`add --json` reports `id`, `file`, `line`, `rendered`, `length`, `section`, `needs` and
the event line. The id is there because it is derived and a caller cannot know it in
advance; the pointer is derived by the same write, from the same rules, and is not.
Where the anchor is the id it costs nothing to recompute. Where `ref_scheme = "outline"`
it is the field the caller named — and where the line derived it, the only readings are
the tail of `rendered` or the anchor embedded in the `needs` command string, both of
which mean parsing prose this tool otherwise refuses to make callers parse. Worse,
`needs` is null exactly when `--section` wrote the rationale in the same transaction, so
the composition RK93 recommends is the one that reports the anchor nowhere. Observed
while testing RK241 over MCP: the obvious read of the answer, `written["ref"]`, is a
`KeyError`. Add `ref` to the payload beside `id`, from the entry the write already
holds, so the two derived addresses a follow-up needs are read the same way — and so an
agent chaining `add` into `section add` reads a field instead of a sentence. `section`
already reports its anchor when a section was written; this is that value for the case
where one was not.

## Block C — Query

### §RK200 The record with no way to read it

RK175 closed the symptom it was filed for: a governed file whose bytes no verb wrote is
named as the turn ends. What it did not give is a way to *ask*. The digest sidecar is a
temp file whose name is a digest, the comparison happens inside a hook, and the answer
reaches exactly one reader at exactly one moment.

That is the arrangement RK161 ended for claims, and the argument is the same one: L5
says every question is a command, and "which lines are claimed" had to be answered by
finding a temp file. Here it is worse in one way — reporting **re-baselines**,
deliberately, so a turn that ends is a turn whose evidence is consumed. A session asking
afterwards what happened has nothing to read, and neither has the next one.

The obvious shape is the one `claims --prune` has: a read that says which governed files
are attested, which are not, and where the record lives — without moving the baseline,
because a query that changes the answer to the next query is not a query. Whether the
`Stop` block should stop re-baselining once such a read exists is the second question
and not this one.

What to check first is whether anybody wants it. The claim registry earned its read
because `pick` stepped over ids and could not say whose; this record has one consumer
and may not need a second.

### §RK245 The remainder is a budget too

RK185 published every aim in words, RK190 moved the read before the sentence, and RK201
put the surplus of an overrun in words as well. One number was skipped, and it is the
one an `amend` is actually bounded by: `Share.left`.

The line `budget RK244` prints is `symptom 120 of 120, 61 written, 59 left  aim 18
words`. `aim` is derived from `allowed` and describes the *whole* field, so beside a
partly written one it answers a question nobody asked — while `left`, the figure that
decides whether the correction fits, is in the unit RK185 established an author cannot
measure. Read together they are worse than either alone: "18 left, aim 30 words" invites
the reading that thirty words are available when about three are.

So `left` gets its word figure the way `allowed` did, and it **floors** — `left` is an
allowance and not a surplus, which is the opposite rounding from `words_over` and the
same argument RK201 made from the other side. `budget --json` gains the field beside
`left` rather than replacing it, because the characters are still what refuses.

Where it also has to land: `brief` prints the `why`'s share of the line it hands over,
so whatever `Share` grows is what a task started through `brief` is told, and the two
cannot be allowed to state it differently. The MCP `note` publishes the ceiling and not
the remainder, so it is untouched.

### §RK247 A retired anchor is invisible

On `ref_scheme = "outline"` an anchor is retired when `ship` deletes its section, but
the changelog entry that cited it keeps the pointer. Reopening that family is a real
move — a block whose work resumes — and the caller has to pick the next free number with
nothing to read: `section add`'s refusal lists the anchors that *exist*, which after a
fully-shipped family is none of them, so \"the next one\" looks like .1. Observed on a
project where §XXXVII.1 through §XXXVII.16 were all retired and all still cited: the
safe number was found by grepping the ledger by hand. Two fixes compose. Have the
refusal list retired anchors beside live ones, sourced from the pointers history still
carries. And let `section add` derive the next free child of a family the way `add`
derives an id — one past the highest ever used, not one past the highest surviving.

## Block D — The gate

### §RK239 The state every verb refuses and the gate does not report

Measured while shipping RK232, and the number is the argument: Turing at `f08304fcb1`
declares thirteen anchors in both `IMPROVEMENTS.md` and `STRATEGY.md`. One is pointed
at, and `lint` reports it. The other twelve are reported by nothing.

Four readers already treat that state as unresolvable. `show` and `brief` refuse to pick
(RK186), `ship` keeps the section rather than choose which of two a line meant (RK196),
`defer` reports the ambiguity instead of naming a file (RK229), and `_pointed_at`
charges own prose because the gate does (RK232). So the tool has a settled opinion — one
anchor names one section — and the only check that says it out loud fires from the
pointer end, which reports the state when a task line happens to reach it and stays
silent otherwise.

That is the wrong end. The claim is about the prose files: `_declared` already builds
the index, and a finding at each of the two headings is what an author can act on.
`--fix` cannot repair it, which of the two is the design being editorial (RK16), and it
has to stay separate from `ref.ambiguous` rather than replace it: a pointer resolving to
two is what a reader of the roadmap hits, and that is worth saying at the line as well.

Worth deciding with it whether this is one finding or one per heading. Two is the shape
`id.duplicate` uses, and it is the one an editor can act on twice.

## Block E — Adoption

## Block F — The plugin

### §RK250 The fact observed is a directory relation, and the sentence is about a launcher

RK246 asks `Engine.carried_by` whether the package directory sits under the project
root, and that answer is sound: a plugin's copy is a cache elsewhere. What the message
then says is more than that answer contains — "wired by `.mcp.json` to
`scripts/roadkeep.py`, which carries no version". A project that `pip install -e .` into
a `.venv` inside its own repository has its package under the governed root too, and
gets a sentence naming two files it may not have; so does a checkout wired by a plugin
marketplace pointing at a local path. The claim that survives every one of those is the
one the relation actually establishes: the code answering lives inside the tree being
governed, so nothing the harness versions addresses this process and restarting the
session is the remedy. That is the whole instruction, and it is true in each case. This
is the same defect RK242 and RK246 each removed one instance of — a note asserting a
mechanism that is not in play — so the fix is to say the fact and the remedy and stop
naming the launcher. Where the wiring itself is worth reporting, `sys.argv[0]` is the
launcher that started this process and is observed rather than inferred; naming it is
then a fact and not a guess dressed as one.

### §RK251 The refusal path is the last place to raise

RK241 gave `add` a second conditional argument and split the one hardcoded sentence into
`_WITHHELD`, a table keyed by dest. Two tables now have to agree with
`Tool.conditional`: `_CONDITIONAL`, which decides whether the field is open, and
`_WITHHELD`, which says which declaration would open it. A missing `_CONDITIONAL` entry
raises in `Tool.exposed`, on every `tools/list` — loud, immediate, and caught by any
test. A missing `_WITHHELD` entry raises only inside `_withheld`, which runs on exactly
one path: a caller passing the closed field. So the surface whose whole purpose is to
name what may be set instead fails as an unhandled exception, and it fails for the
caller who most needs the sentence. Two things close it, and the cheap one first: a test
over `TOOLS` asserting every dest in every `conditional` has an entry in both tables,
which is the same shape as the tests already holding `writes_when` against its parser.
Then `_withheld` reads with a fallback rather than an index, because a note that cannot
explain itself should still let the refusal through — the "no such argument" clause
above it is correct and complete on its own, and dropping the second sentence is the
failure mode this file can afford. `_bounded` is already written that way, skipping a
dest no bound names.
