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

## Block C — Query

### §RK1656 The answer a dismissed target has none of

`Backlog.resolve` reads the roadmap, the ledger and the deferred store, and a dep naming
an id none of them holds is `deps.unknown`: *in neither the roadmap nor the changelog,
so nothing can say whether it is done*. The dismissed store makes that sentence false —
it says precisely what was decided, and names the premise under which it stays decided.

RK92 is the same finding one store earlier. Before it, a dep on a paused line read as a
missing id: the gate reported it, `pick` could not rank the line waiting on it, and the
fix was a fifth `DepStatus` plus a `blocked-paused` readiness. The seventh role arrived
without the sixth.

What it costs is smaller than RK92's and is the same shape. Nothing *should* depend on a
dismissal — the entry is a finding nobody filed — so the honest answer is not
`DEFERRED`'s: a dep on one is work waiting on something this project decided not to do,
which is closer to `deps.retired` than to a pause. That distinction is the design:
whether the resolver gains a sixth status or the existing unresolvable branch gains a
second sentence.

**The measurement first.** Neither adopting corpus declares this store yet, so the
population is this tool's own suite — which is exactly the state RK1084 found for the
pair it wrote a rule for anyway, on the argument that a contradiction the format can
express should not be silent.

### §RK1663 The blocks a finished label is not in

RK1622 reads a pin's shape and gives it a row per block. The rows are the **roadmap's**
headings, so a label whose work is finished — its heading kept in the ledger and gone
from the roadmap — contributes to the total and to no row. Measured at the pins: Shio's
rows hold 280 of 668 delivered and Turing's 55 of 901.

The totals are right and the rows are not wrong about what they say; what they are is a
shape a reader would take for the corpus's. *Three blocks, 55 delivered* reads as a
small backlog, and the file it is about carries nine hundred entries.

RK429 is this distinction already made once. `Stage` tells a block that finished from
one that never existed, and `Census.elsewhere` exists exactly for the label the other
file declares — so the machinery for the honest answer is there and this reading did not
reach for it.

**What to decide is which set the rows are over.** The union of both files' headings
answers the corpus's shape and makes a row for every label; the roadmap's alone answers
*where the open work is*, which is a different and also useful question. A shape that
means to be cited should probably say both — open rows over the roadmap, delivered rows
over the union — and the cost of that is one more number per row rather than a second
reading.

### §RK1670 The door an undeclared role has

`Config.path` raises `this project declares no 'deferred' file (has: changelog,
improvements, roadmap)`, which is two thirds of what a refusal owes: it names the
absence and what stands in its place, so the caller can tell the question apart from an
empty answer. What it does not name is the verb — and `declare`'s own description says
outright *reach for it when a verb refuses over an undeclared role or table*, so the
door exists and the one refusal it was written for does not point at it.

RK1328 made the same repair one table over: `criteria.NotGoverned` said *`declare
criteria` opens the table* rather than naming a hand edit to configuration this tool
owns the writes to. A role is the same shape and reaches more callers — every read and
write that resolves a path goes through here.

What has to be decided is the site. This raise is in `config.py`, below `remedying` and
`provenance`, so a `Door` here would be an import the layering does not have; the plain
backticked verb `criteria.py` uses needs none, but `test_composing` holds its census
total over every function that composes a command, so the row and its run come with it.

## Block D — The gate

### §RK1665 The codes the scan cannot read

`test_backstop._written()` walks every `Violation(…)` in the package and takes the first
argument where it is a string constant. Where it is not, it widens the found set to
`COMPUTED` — the three character codes composed from a field name — and moves on.

`scoping` and `criteria` name theirs as module constants: `LEAD = "non-goal.lead"`,
`SHAPE`, `WHY`, and the three beside them. The comment says why, and it is right — *a
code spelled twice is a code that drifts once*. So `Violation(LEAD, …)` is invisible to
the scan, and six codes a write genuinely refuses are outside a register whose whole
claim is `covered == written`.

Nothing is wrong today: four of the six have rows anyway, and the two `lead` codes were
found by RK1627 joining to it and failing. What is wrong is that the closure cannot see
them, so a seventh added to either module would have no row and nothing would say so —
the silence the register exists to end.

The fix is the scan's and not the modules'. A name resolving to a string constant in the
same module is readable with the `ast` already parsed, so the reader gains a pass that
binds module-level string constants and looks one up where the first argument is a
`Name`. What it must not keep is the fall-through to `COMPUTED` on a name it could not
resolve: that branch is what hid these.

### §RK1666 The sentence above the key

`govern <key> <n> --because "…"` wraps the caller's argument into comment lines above
the key and writes `roadkeep.toml`. What refuses a bad value is `readable()`: the
composed text is parsed back before the bytes land, which catches a value TOML cannot
carry and is blind to everything inside a comment.

So a mangled run lands. Reproduced on a scaffolded project: `--because "Menu Ã©
semeado"` wrote `# Menu Ã© semeado`, the write reported success, and `lint` did not list
`roadkeep.toml` among the files it read. `char.mangled` is a rule this build has and
applies to a task's fields, a section's title and a block's — every composed field but
this one.

RK1570 is the same finding one field over, and RK1627's register is what named this: the
row for `because` is the only `round-trip` kind in it, which is the register saying out
loud that the strongest thing between this value and a governed file is a TOML parse.

What it wants is the three rules a title already takes — no newline, no leading `#`, and
the codec rule — because a comment is one line and `#` is what opens it, so the
vocabulary is already right. `--instead` is the same argument at the same door and takes
them with it. What is not obvious is whether the gate should read that file for
characters too, which is a second question about a file no role declares.

### §RK1667 The quote no one spelling carries

RK1635 built the instrument and the instrument answered. `provenance.quoted` spells one
double-quoted span for every shell, and a door run through `cmd`, PowerShell and `sh` in
turn does not arrive intact in all three: an embedded quote and a trailing backslash
break two of them, a dollar sign expands in two, `%VAR%` expands in one, and a backtick
is a command substitution in `sh` and an escape in PowerShell.

The backtick is the row that costs something. This project writes about its own verbs in
backticks, so a failing `add --symptom` whose claim names `pick` composes a `report`
door that, pasted into the Git Bash prompt this repository is developed at, runs
whatever is between them and hands the tool a symptom with the span gone.

No single double-quoted spelling closes the table, because each of the three expands
inside quotes what the other two keep literal. So the shapes are the question: whether
the door is composed differently per shell, whether the argv is carried some way other
than a pasted line, or whether the fields that reach a door are refused these characters
at the write — which is L1's own answer and the one this format already gives to an
invisible codepoint.

What it must not become is a quoter that guesses which shell a reader is at:
`provenance` refuses to describe a machine, and a spelling right in one family and
silently wrong in another is that description made anyway.

### §RK1668 The thirteen doors the census named

RK1640's census cut 406 bare verb-leading spans down to the 27 carrying a field an
author fills, and read each. Thirteen are commands a caller is being offered — `block
add <label> --title …` writes the first heading, `section show <anchor>` prints the
prose as it is, `priority add <token>` writes the first entry — printed with no
invocation in front of them.

That is RK1589's defect thirteen times over. What it costs is exact: a caller pastes the
line and their shell has no such command, which on this project's own platform is the
failure RK1667 measured from the other side. The other fourteen spans are prose for four
stated reasons and `BARE` says which.

The repair is one token per site and the cost is not there. `census()` is every function
that calls `invocation()`, and `SITES` is held total against it with every row `run` or
`deliberate` — a state RK1599 reached by emptying the work-list over sixteen sittings.
Prefixing thirteen messages adds thirteen sites, and a row that cannot say its door was
executed reopens that list.

So the question is not whether to prefix but what each new site owes. A door carrying
the invocation is one `runs` can execute, which is the point; the fixture each needs is
the refusal's own state, and two of the thirteen refuse about a project that declares no
config at all.

What it must not become is thirteen `unreached` rows. That is the work-list back, bought
with a token.

### §RK1669 The rows a transport does not have

`_one_answer` composes the rows off the declaration, so a call naming no subject is
answered with every subject its parser declares. On the terminal that is the whole set
and correct. Over MCP it is not: `cost` declares seven and the tool exposes four,
`deny`, `notes` and `near` being withheld with reasons that say why a caller there is
not offered them — so three of seven rows name flags that caller cannot pass, and a
retry passing one is refused again by `additionalProperties: false`.

The rule is one rule and the surfaces differ, which is the arrangement RK1260 already
met one field over: the pipe clause is unsaid over a transport that has no stdin. What
is missing here is the same subtraction, and the dispatcher is the wrong place to make
it — it does not know which surface it is on. So either the refusal takes the exposed
set from its caller, or `serving.call` filters the rows it hands back, and which of
those it is turns on whether a refusal composed in `cli` may be shaped by anything above
it.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

## Block I — The documentation area (what an adopter reads before there is a session to ask)
