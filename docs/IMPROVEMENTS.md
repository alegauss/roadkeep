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

### §RK1180 Two kinds of block wearing one shape

`ship` reports "Block x is finished: nothing open" and points at `block drop`. That is
right for a block that is a **project** — a capability with an end, whose last task
really is the last one.

Some blocks are not projects. Shio's Block N is titled "realignment of what already
shipped": it is where a finding goes when something that shipped turns out to be
incomplete against a law or blind to half a repository. A category like that receives
work forever and is empty only in the sense that nobody has filed the next one yet.
Measured, in one session: declared, emptied and dropped **three times**, each drop
followed within the hour by a finding that re-declared it.

The cost is not the churn in the file. It is that the host project hangs a
**block-completion sweep** off the signal — four public surfaces brought up to date, a
coverage matrix resolved, a docs build — and that sweep is designed to run once per
capability. Running it three times for one block means twice re-reading surfaces nothing
changed on, and it trains the reader to treat the completion notice as noise, which is
the worse cost.

A block could declare which kind it is: a project empties once and is dropped, a
standing block empties often and stays. `ship` would say "caught up" rather than
"finished" for the second, and `stats` could distinguish a zero that is done from a zero
that is merely current.

## Block B — Authoring

## Block C — Query

## Block D — The gate

### §RK1172 A rule is a record, the way a remedy already is

`src/roadkeep/remedying.py` states the argument outright: keyed centrally,
`tests/test_remedying.py` can assert the domain is total over every code the package can
emit, which turns adding a check without stating its repair into a red. That is right,
and it is only half applied — the *remedy* is a table and the *check* is not.

The check side is about sixty functions in `src/roadkeep/linting.py`, each with a
signature invented at the call site: `(config, role, document)`, `(config, tree)`,
`(config, documents, since)`, `(backlog, task, file, lineno)`. What each one scans is
implicit in its parameters, and `_examine` is the hand-wiring that knows which to call
with what. Nothing states the set, so nothing can be total over it.

As a record — the code, what it scans, the predicate, and whether `--fix` may close it —
`_examine` becomes a loop over a declared domain, `src/roadkeep/fixing.py` reads the
derived flag instead of `REPAIRS`, and a rule that scans something new says so rather
than adding a parameter to a call.

The scan kinds are the design question worth answering first, because they are what the
record's shape is: a role's document, the tree, the backlog, the sections, the config. A
rule that fits none of them is the evidence the set is wrong.

### §RK1173 The door belongs on the rule, not beside it

This is the second half of its dep and deliberately not folded into it, because the two
are separable and the first is worth shipping alone.

RK420 put the remedy in one table keyed by code, and gave the reason: a remedy computed
at the emission site would be seventy remedies to keep in step with seventy messages,
and the one that fell behind would be invisible. Every word of that holds. What it could
not do at the time was put the remedy on the rule, because there was no rule to put it
on — the checks were functions, so the only thing both sides could agree on was the code
string.

With the dep shipped there is a record, and the door is a field on it. The table and the
emission site stop being two files that a test proves consistent, and
`test_every_code_the_package_can_emit_has_a_door` stops being needed for the reason it
was written: a rule with no door does not compile into a rule.

What must survive the move, because it is the part that is load-bearing: the four kinds,
the marked blank where the prose is the author's by L4, the two doors where the choice
is editorial, and the config reads that keep a door true on a project whose paths and
pointer scheme are its own. None of that is a table; all of it is the field's type.

## Block E — Adoption

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

### §RK1179 The one refusal that is not a refusal

`scripts/roadkeep.py` imports `roadkeep.cli` after its screen, with the comment "after
the screen, never before". The screen covers the interpreter and the package being
absent. It does not cover the package being present and unparseable, which is the state
a checkout is in for as long as somebody is editing it — and every project running the
tool from a checkout shares that state.

Met from another repository mid-task: a `budget` call came back as a nine-line traceback
ending `IndentationError: unexpected indent` at `backlog.py`. Nothing in it says which
checkout answered, that the checkout is the thing that is wrong rather than the call, or
that the caller's own files were untouched. Compared with every other refusal this tool
writes — a code, a sentence, and the argv that closes it — it is the one path where the
tool stops being the thing that explains itself.

`engines` already answers the neighbouring question, reporting `agreed`, `behind` or
`unpinnable` across the three copies that can be in play. It cannot help here, because
reaching it needs the same import.

So the screen is the place: catch the import, say which path was imported and that it
does not parse, and name the one line of the traceback that identifies the file. The
workaround a caller finds on their own is a clean worktree of the tool, which works and
is not something the tool should let them discover by inference.
