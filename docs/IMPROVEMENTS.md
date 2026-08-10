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

### §RK499 Three codepoints the grammar reads as a separator, admitted by the door

Measured by RK498's register: of the 84 codes the gate emits, these are three of the
five a write accepts. Reproduced on `add --why`, `amend --why`, `restate --symptom` and
`record add --why` — every door that takes prose — with `char.tab`, `char.invisible` and
`char.space` reported afterwards.

The inconsistency is inside one field. `why.whitespace` refuses a leading or trailing
space at the write and says so, while a tab three characters in is written and left for
the gate. A caller cannot learn a rule that holds at one end of the string and not the
other.

Why it matters more than it looks: the format separates fields with a space, so a tab or
a no-break space is a separator the grammar reads as part of a field — the line still
round-trips and still parses, and what it parses to is not what was meant. That is the
class L3 exists for, arriving through the one door that was supposed to keep it out.

`lint --fix` repairs all three, which is the argument for refusing rather than
rewriting: a fixer that silently edits prose is what L4 forbids at the write, and a
refusal costs the caller one retry with the character removed.

What proves it: the four doors refuse each of the three, the register's rows for them
move from `open` to `refused`, and a field with no such codepoint is written exactly as
before.

### §RK500 Two deps a write states about a backlog it is holding open

The other two of RK498's five. `add --dep RK999` is written and the gate reports
`deps.unknown`; `add --block A --dep "Block A"` is written and the gate reports
`deps.cycle`, the line being inside the set it waits on.

The first is worse than it reads, because the write already treated the token as an id:
the next derived number stepped over RK999, so the id was spent by a line that names
nothing. A dep the write cannot resolve is therefore not ignored — it costs an address.

Both are answerable from what the verb has in hand. `Backlog` is loaded to place the
line and to derive the id, and it is the same reader the gate asks; nothing here needs
git, a second file or a listing.

The boundary is `deps.retired` and `deps.stale`, which stay the gate's: those become
true when a *later* write moves the line the dep names, and the write that stated it was
correct when it ran. What is claimed here is only the pair a write can decide about the
tree in front of it.

What proves it: both are refused naming the dep, `gaps` is still what a caller reaches
for when an id really did leave, the derived id no longer steps over a token nothing
carries, and the register's two rows move to `refused`.

## Block C — Query

## Block D — The gate

### §RK1000 L6 is reachable and unreached, and the other two are not

The register's three empty holders are in three different states, and only one of them
is a task. L2 is satisfied by an *absence*: a property would quantify over the services
this package does not open and the schemas it does not migrate, which is not a set. L5
needs a declared inventory of the reads before a property has anything to sweep, and
that inventory is its own line. L6 is neither, and its row says so in as many words —
*reachable and unreached*. A source scan for a literal limit, prefix, marker or path
outside `config` is decidable, and nobody has written it.

What makes it the one to spend first is the consequence and not the ease. L6 is the law
an adopting project rests on: prefix, paths, markers and limits are that project's, read
from that project's own `roadkeep.toml`. A literal that slipped into the package does
not fail here, where this repository's own numbers happen to match what was hardcoded —
it fails in Shio, in Turing, or in a fork whose prefix is three letters, as behaviour
nobody can derive from the config they wrote.

The surface is this package's modules, which RK496 finally gave an address. What the
scan must not do is flag the defaults themselves: `config` is where a default is written
down, so a scan that cannot tell a default from a leak is a red nobody keeps.

### §RK1001 A recurrence is a hole in a holder, and it is declarable

Twelve of the fifteen rows carry a holder, and that number is what makes this question
askable for the first time. A defect in a class one of those twelve claims to cover is
not new work: it is a hole in the holder, which enumerates less than its row says. The
fix belongs in the test, and the code it would otherwise patch is a symptom.

Nothing tells the two apart today: they are one shape in `stats`, in the ledger and in
the log. The only reason RK497 was recognised as a family is that somebody probed three
more codes by hand afterwards and filed §RK498 — an act of attention, performed once,
that nothing schedules.

It cannot be inferred: matching a symptom to a class takes meaning, and L4 forbids the
model. It can be **declared** — a design names the row it instantiates, in the shape
RK492 established for a machine-readable claim inside a rationale section. A second task
naming a row that has a holder is then a recurrence by count and not by judgement, and
the count points at the property.

A row with no holder is the other answer, and it stays silent: an instance of L2, L5 or
L6 is a rung, correctly, because nothing ever claimed to hold it.

What proves it: a design naming a row that does not exist is red, and each held row can
say how many instances it has taken since it was written.

### §RK1002 The id rule is enforced at derivation, not where prose is written

RK431 made deriving an id read prose, and that is right: a ledger entry promising *filed
as RK499* before the line exists has to reserve that number, or two things carry one id.
Nothing here changes it.

What deriving cannot do is tell a promise from an illustration, and it says so — the
warning hedges, *if that sentence promised this task*. Refusing to guess is correct,
because deciding would take the model L4 forbids.

The defect is where the rule is enforced. §RK498 was composed with `add --dep RK999` as
an example, `section add` validated the body, and nothing was said. The consequence
arrived two sessions later, inside another command's output, as a warning nobody has to
act on — and the gate has no code for it: `id.duplicate`, `id.format` and `id.two-files`
are the three, and the tree was clean throughout.

Measured: structure on a task line went from 41 characters to 43, so every line written
from now on has two fewer for prose. A digit costs two because the id is written twice,
once as the address and once in the pointer, and a careless five-digit token would have
cost four.

This is L1 read backwards, and the second case of that shape in three days — RK497
closed the same gap where ledger prose is composed.

What closes it: the write path refuses an id-shaped token no line carries, naming both
ways out — a token outside this project's prefix, or the id actually claimed.

## Block E — Adoption

## Block F — The plugin
