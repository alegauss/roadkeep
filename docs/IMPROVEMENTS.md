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

### §RK1274 The door a decision leaves by

A decision leaves by one door, which is what separates the role from the ledger — and
that door was described and not built. The grammar declares 🗑 legal in the decisions
file, because `retire --superseded-by` is the ADR's Superseded-by read as this format;
nothing writes it there. Measured on the file this repository just opened: every line is
✅ and no call can make one anything else.

So the role records that a decision was made and never that it stopped holding, which is
the half an ADR is kept for. A reader finds a constraint and cannot tell a live one from
one three decisions have since replaced.

`retire` is the wrong verb and its shape is the right one. That one starts from an open
roadmap line, and a decision has none: the line it came from is in the ledger before the
decision is written. So the door starts from the decisions file itself, takes the entry
being replaced and the one replacing it, and does what `record add --supersedes` already
does one file over — write the forward pointer onto the entry that is now stale and
change its marker, in one write, because two records of one reversal that do not name
each other is the state RK395 closed for the ledger.

Nothing is deleted, which is the role's whole rule: both lines stay and the marker says
which is live.

### §RK1276 A pause is not a departure, at the one door that says it is

`criterion add --task <id>` resolves the address against the roadmap, correctly: a list
about work the ledger already holds is a question somebody answered by shipping. The
refusal says exactly that, and for one of the three absences it is false.

An id can be missing from the roadmap for three reasons and they are not one fact. It
shipped, it was retired, or it is **paused** — and a paused line keeps its id, its deps,
its symptom and its section, which is what separates a pause from a departure (RK96).
Its criteria are still the right question; the answer is `resume`, not a rewritten
claim.

The message sends the reader the other way: told the question was answered by shipping,
an author who paused the line yesterday reaches for a second id.

Every other write that reaches a line by id already draws this distinction: `amend`,
`restate` and `status` each refuse a paused one **naming the store and `resume`**, so a
refusal about a pause never reads like one about a typo. This is the same refusal at the
one door that has not learnt it, and the reader that knows the answer already exists —
`Whereabouts` is what the departure verbs ask.

Scope: the message and nothing else. Whether a paused task's list should be writable at
all is a separate question, and the answer this repair assumes is the one every sibling
verb gives — no, and say where the line went.

## Block C — Query

### §RK1275 The allowance for a transaction, not for a line

RK1261's finding, re-opened by the two flags filed after it. `brief` quotes what a
`ship` has left for its sentence and names one thing that will be appended to it: the
supersession clause, at 30 characters here. Two more writes have since landed and
neither is in that number.

`--recorded-in` composes into the same sentence. Its wrapper is derivable exactly as the
supersession's is — the anchor is the pointer the line already carries — and only the
path's own length is the caller's, which is the shape `--part` is already described in.
So the figure quoted at the moment a task is about to lose its design is wrong by a
clause whose size this tool knows.

`--decides` is the other half and it is not that line at all: it writes a line in the
decisions role, under that role's own limits, and no read quotes them. So the one
sentence this format asks an author to compose blind is the one recording what outlives
the code — refused after it is written, which is the failure L1 exists to remove.

Both are the same repair at two addresses: the pre-write read answers for the whole
transaction, which is what it already claims to do for `add --section`. What it must not
do is guess — a path nobody has typed has no length, so the wrapper is quoted and the
value is the author's, said as such.

### §RK1278 The declared value, beside the default

The shape answers two of the three things a reader wants about a key and stops at the
third. It says what this build uses when nobody declares it, and it says whether this
project declared it — and where the answer to the second is yes, the number printed is
still the first one.

So a project that set `symptom = 90` is told `default 120, declared here`, which is two
true statements arranged to read as one false one. The reader most likely to meet it is
the one hovering the key they are about to change, which is the moment the value matters
and the default does not.

The reason it is absent is the reason `declared` is read back off the file: a parsed
config carries the *effective* value and cannot say which of the two it is. That reading
is right and half-used — the same parse that answers whether a key is written also has
what was written there.

What it must not become is a second parse. What TOML hands back is a scalar, a string or
a list, and rendering one is what `_rendered` already does; resolving it into what the
schema makes of it would be this reader re-deciding what the parser decided.

The absence is a value, not an emptiness: a key nobody declared has no declared value,
which is a different fact from one declared as zero and is said as such.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

### §RK1277 Two clocks in one payload

Two facts arrive in one payload and they move on different clocks. Which keys this build
accepts moves when the *engine* moves, so caching it until an explicit refresh is right
and was the reason for the cache. Whether this project declared one moves when the
**file** moves, and it is in the same object.

So a hover says "not declared here" about a key somebody declared a minute ago, and goes
on saying it until the person presses refresh — for a reason no reader can see, since
the row beside it is correct.

RK1017 drew the line this crosses. It kept two caches on purpose — the engine's, reread
only on the explicit ask, and the file's, dropped on every save — because the two
questions have different answers about when they went stale. This read joined the wrong
one.

And the watcher never sees the file at all. It matches Markdown, which was every
governed file when it was written; the config joined `lint`'s checked list since, so an
external edit to it re-runs nothing. A save inside the editor is covered by the save
hook and an edit from a terminal is not, which is the harder half to notice.

The repair is the split RK1017 already made: the shape stays on the engine's clock and
what the project declared is read on the file's, or the whole read moves to the file's
clock and an upgrade is what the refresh button is for.

## Block H — The tool's own shape (what one verb costs to change)
