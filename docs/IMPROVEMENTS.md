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

### §RK1168 A namespace is a migration, not a config key

`section move` is the model to copy: it re-addresses a section and takes its subtree and
every `→ §<anchor>` naming it, or it takes none of them. Declaring `[refs]` is the same
kind of event at file scale — every heading in that file changes address at once — and
it carries nothing.

Measured adopting it on Viglet Turing, where two prose files had 13 doubled addresses.
`[refs] strategy = "S"` re-addressed 48 headings and put `section.ambiguous` at 0, and
left 28 of that file's own citations behind:

    7   became ref.dangling — the address exists in neither space
    21  kept resolving, into the OTHER file's section of the same address

The second half is the dangerous one: both files declared that address — which is why
they collided at all — so the citation still resolves and `lint` says nothing. Repairing
all 21 moved the total from 46 to 46.

Two asks, and the first is worth little without the second:

- **Carry the citations.** When a namespace is declared or changed, re-address
  that file's own citations in the same transaction, as `move` does for the
  pointers at a section. A body it cannot rewrite should refuse the call whole.
- **Report the ones that cross.** A citation resolving into a different prose
  file, where the citing file declares that same address, is a finding — a
  reference the author cannot see is wrong.

Without them, adopting the config key means a hand-rolled classifier and one `amend` per
section, which is the migration the key looked like it was.

## Block B — Authoring

## Block C — Query

### §RK1174 The budget shown is not the budget the next write is measured against

Measured across four ships in one session: three were refused for `why.too-long` on the
first attempt, and each refusal cost a round trip the budget line exists to prevent.

The budget `brief` prints is real and it is the wrong one. `brief DD53` said `budget why
16 of 165 left`, which is the roadmap line's allowance. The `ship` that followed writes
a *changelog* line, whose allowance comes from a different limit and a different symptom
position: the refusal said `limit is 184 ... the line's own limit of 320 leaves 300 for
prose, and the symptom takes 116`. Two numbers, 165 and 184, for a field an author
thinks of as one thing, and only the one that does not apply is shown before the write.

The refusal itself is good — it names the limit, the arithmetic and how many words to
cut. What it cannot do is arrive early. An author composing a ship's `--why` is
composing against a ceiling derived from the ledger's limit and the symptom already on
the line, and the tool holds both the moment `brief` runs.

So the fix is upstream of the refusal: `brief` should print the allowance for the write
the author is about to make, not only for the line that already exists — or both,
labelled, where the difference between them is itself the thing worth seeing.

## Block D — The gate

### §RK1165 A run is one fact, said once

`gaps` on this repository prints **503 lines**, and 499 of them are one fact. Every row
of the run reads the same way — *never carried: the whole history mentions it nowhere* —
with only the number changing, from 501 through 999.

Measured: the never-carried ids are a **contiguous run of 499** plus exactly two singles, at 80 and
224. The run is a numbering jump — this backlog restarted its series at a thousand — so it is
permanent, unactionable, and 499 rows on every run for ever.

The two singles are the signal: each is a number the counter spent and no commit ever
carried, which is the reading RK95 built. They are findable today only by paging past
the jump.

This is RK1143's rule one command over — a row that is never the next step makes the row
beside it unread — and the shape is already in the format: a **range** is how this tool
spells many ids at once. One line for the run, rows for the singles.

What needs deciding: whether a run is collapsed by size or by *reason*. A jump in the
series and five ids somebody burnt in one afternoon are both contiguous, and only the
first is permanent.

Worth stating because it decided the prose above: naming those ids here is refused
(`body.promise`, RK431), an id in this prefix that no line carries being read as spent.
The rule found this section, which is the rule working.

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

### §RK1169 The tool declares itself once, or six tables declare it again

`src/roadkeep/serving.py` derives every property's type, description and bounds from the
argparse action, which was the right call and stopped one file short. What it could not
derive it tabled: `TOOLS` says which arguments a caller may set, `_BOUNDS` narrows them,
`WITHHELD` says what a refusal must explain, `_CONDITIONAL` says when a project opens
one, `_DIVERGENT` says where the served name is not the command's, and `_DESTS` maps an
option back to its dest. Six facts about a verb, keyed by that verb, written in the file
that is not its parser.

None of them is wrong, and that is the finding. Each is held true by a test asserting
the domain is total — `test_every_tool_is_a_subcommand_the_cli_accepts` in
`tests/test_serving.py` is one — so what this costs is not a defect waiting to happen
but tests written to prove that two places agree about one thing.

A parser already carries `handler`, `reads_only`, `reads_stdin` and the flags that turn
a read into a write, all through `set_defaults`. Exposure and bounds are the same kind
of fact and belong there. Moved, the tables go and so do the tests that held them,
because a fact stated once cannot disagree with itself.

What is derived stays derived. The config still narrows a conditional field, since L6
says a project declares that shape and this surface never holds a second opinion about
it.

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
