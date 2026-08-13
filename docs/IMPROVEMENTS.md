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

## Block D — The gate

### §RK1154 Which spelling a test means

Three assertions in `test_guarding` say *this message does not name the shell*, and they
say it as a substring test: `assert invocation() not in said`. On a checkout
`invocation()` is `python scripts/roadkeep.py` and the test means what it says. After
`pip install`, it is the console script — `roadkeep` — and every served name contains
it:

```
assert 'roadkeep' not in 'roadkeep governs docs/ROADMAP.md — … `mcp__roadkeep__brief` starts …'
```

So the assertion fails on the one environment where the message it guards is *most*
likely to be right, and it fails for a reason that has nothing to do with the claim:
`mcp__roadkeep__brief` contains `roadkeep` because this tool is what serves it. Three
tests, all green locally, all red in CI, and RK444's finding — the one guaranteed
message must name the engine that answers — is not what any of them measured there.

What the claim actually is: no line spells the **command**, which is the engine followed
by a verb. `mcp__roadkeep__brief` never is, whatever the engine is called, because a
tool name has no space in it. So the test reads for `invocation()` immediately followed
by a space, and not for the name alone — one predicate, in one helper, for the three
that make the claim.

The general shape is worth naming: an assertion about a *rendering* that reads the
rendering's own vocabulary out of a function whose answer changes with the install.
`invocation()` is right to change; a test comparing against it has to say which spelling
it means.

## Block E — Adoption

### §RK1150 A version skew wearing a typo's message (RK1150)

Reached from Shio, filing RK1149. The MCP server resolves roadkeep from the plugin cache
and the project resolves it from a checkout, so the two can differ. When they did:

    roadkeep: D:\...\roadkeep.toml: unknown key 'headings.permanent'
    (allowed: headings.word)

Every word true, and the conclusion it invites is wrong. `headings.permanent` is not a
typo and not somebody's invention — it is a key a *later* roadkeep added, read by a
binary that predates it. The message's own `allowed` list is the older schema, presented
as though it were the schema. The cheapest action it suggests is deleting a key the
project needs, and the second cheapest is editing a config that is already correct.

Nothing in the sentence can be used to reach the real answer, because the one fact that
separates the two readings — which roadkeep is running — is absent. The tool prints its
version in the MCP handshake and in `--version`, and not in the refusal that needs it.

So: name the running version in every config refusal, and where a key is unknown say
which of the two states it is. A key no version has ever declared is a typo; a key this
version does not have is an upgrade. They are different findings and they currently
share a message.

Cheap, and it is the first thing a reader needs on a machine where two copies are
installed.

## Block F — The plugin

### §RK1152 A refusal a caller cannot act on names the wrong line

`ship DD34` was refused three times in a row, each time with a message that opened by
naming the `--why` passed to the command:

```
why: 164 characters, limit is 163 ... delete 1 character - about 1 word
  ... - on DD35's line (docs/ROADMAP.md:15), whose dep annotation this write
  re-derives, and not on the text passed to this command
```

The clause that matters is at the end, after the remedy. A caller reads "delete 1
character" and edits the string it just passed, which cannot help: the overflow is on a
*dependent's* line, because shipping re-derives `(deps: DD34)` into `(deps: DD34 ✅)` and
that tick is two characters wider. Unblocking one ship meant amending DD35, then DD36,
then DD37 — each discovered only by re-running `ship` and reading the next refusal.

Two things would fix it independently. The refusal could lead with whose line overflowed
and what to run (`amend DD35 --why ...`), rather than leading with a remedy that applies
to a different string. And it could report **every** line the write would overflow, not
the first, so one edit round closes it instead of three.

The check itself is right: a line that will not fit after a derived write should refuse
before writing rather than truncate. What is wrong is that the message is addressed to
the wrong text.

## Block G — The editor surface (the backlog where the file is open)
