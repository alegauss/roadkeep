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

### §RK1030 The statement that was not the problem

A `roadkeep.toml` whose first three bytes are `EF BB BF` makes every verb of this tool
answer the same line:

> `roadkeep: Invalid statement (at line 1, column 1)`

Line 1 column 1 is `prefix = "RK"`, which is correct, and the message points at it. What
is wrong is a byte no editor shows, in the file a project writes before it has run
anything — and on Windows the default route writes it: PowerShell 5.1's `Set-Content
-Encoding utf8` and `Out-File` both add the mark, which is how this was found.

`config.py` opens the file `rb` and hands the bytes to `tomllib`, which refuses a
preamble by specification. So the diagnosis belongs here rather than upstream, and it is
the same argument RK1023 made about the pipe: the author cannot fix it from where they
are standing, because nothing in their command names the encoding that added the byte.

**Not the same fix.** Stripping it silently is right for a prose field and wrong for a
config: this file is the project's declaration, and a tool that quietly accepts one
encoding variant of it teaches nothing. So the answer is the message — name the mark,
the file, and the one-line command that removes it — with the edit left as the author's.

What proves it: a config carrying the mark answers with the byte and the fix rather than
with a statement that is correct, every other TOML error is unchanged, and the sentence
names the file the caller has open.

## Block B — Authoring

### §RK1026 The one refusal roadkeep did not write

`ship SH625 --note "…"` prints argparse's usage line, the full list of thirty-odd verbs,
`unrecognized arguments:` followed by the entire rejected value, and then the `report`
hint. The flag meant was `--why`. Nothing in that output says so.

Every other refusal in this tool is written to be acted on — `body.too-long` gives the
count, the limit, the delta and a per-paragraph breakdown; a forward reference names the
hazard and the two ways out. This one is the parsing library's default handler, and it
fires *before* any of that exists, which is why it reads as coming from a different
program.

Two things make it worse than a plain unknown-flag error. The verb list is the least
relevant thing on screen when the verb was right and the flag was wrong. And echoing the
rejected value — often a paragraph of prose meant for `--why` — buries the one line that
matters under text the caller just typed.

The fix is an error handler that, for an unrecognised option, names the nearest of that
subcommand's own options. `--note` against `--why` is not an edit-distance hit, so the
useful form is *"ship takes: --why, --part, --lines, --superseded-design"* — the verb's
own surface, which is short, rather than the tool's, which is not. Same law as RK1025,
at the other end of the CLI.

### §RK1027 A guard that is right about the hazard and wrong about the cause

Writing prose that mentions a sibling task not yet added is refused: *"names SH653,
which no line carries: an id in this project's own prefix is read as spent, so the next
`add` derives past it — spell the example outside SH, or name the id actually meant."*

The hazard is real and the guard should stay. Both remedies it offers assume the id was
an error — an illustration that borrowed the prefix, or a typo. Neither covers what the
caller was actually doing, which is authoring two tasks that reference each other, in
the only order a shell allows.

The correct advice is *add the other task first, then write this section*, and it is
absent. So the caller either learns the ordering by failing once, or edits the prose to
remove a cross-reference the backlog wanted — the outcome that costs something, and the
silent one.

It is cheap to tell the difference. An id inside the project's prefix that is **at or
just past** the derived next id is a forward reference to work in flight; an id far
below it is a retired or mistaken one, which is the case `gaps` already answers. The two
deserve different sentences, and the first should name the reordering rather than the
rename.

### §RK1028 The mark the other reader kept

RK1023 took the byte order mark off the pipe. The other reader kept it: `--body-file`
and `--section-body-file` open a path as `utf-8`, and every mainstream Windows editor —
Notepad, VS Code's "UTF-8 with BOM", PowerShell's `Out-File` and `Set-Content -Encoding
utf8` — writes one.

Reproduced in three commands: a body file whose first three bytes are `EF BB BF`,
`section add X --body-file body.md`, and the mark is in `IMPROVEMENTS.md`. `lint` then
reports **clean**.

That is what makes this worse than the pipe was. Stdin was loud — `char.invisible`
refused the field — so an author knew. Here nothing does: the writer accepts it, the
gate's invisible scan reads task lines and not section bodies, and L3 preserves the byte
for as long as the file lives. It is invisible in an editor by definition, so the first
reader to notice is whoever greps the heading and finds nothing.

**Two halves, and the second is the durable one.** The read is `removeprefix`, as
`verbs/reading.py` now does for the pipe — one mark, at position 1, the encoder's and
not the author's. And the gate's invisible scan should reach a section body: the
argument that closed the pipe is one nothing holds about any other route in.

What proves it: a body file opening with the mark writes prose that does not, the same
codepoint further in is still the author's, and a file already carrying one is red at
the gate rather than clean.

## Block C — Query

### §RK1029 The read RK1024 did not reach

RK1024 charged an ancestor at `add` and said so at `anchors`. The read those two exist
to save a retry on is the one still answering about the child alone.

Measured in a scratch project whose `§IX` is a live design spending 29 of its own 30
words: `budget --anchor IX.1` answers `body 30 words, aim 28`. The room is one word, and
the `add` after it is refused — correctly, and after the prose exists, which is the
sequence this tool was built to end.

The number is not hard to find: `charged()` already answers what the gate bills an
ancestor, and `sections.add` already walks every one of them. What is missing is that
`Body` carries a single limit, so there is nowhere to put the second fact — which
ancestor binds, and what it leaves.

**The shape to avoid** is a second number replacing the first. A child of a container
nothing points at is charged its own prose, and an ancestor's figure there would price a
section against a heading nobody bills. So this is a row and not a substitution: the
field's own limit, and beside it the address that binds where one does.

What proves it: a child of a full parent is answered with the room it actually has, a
child of a container is answered as it is now, and the number `budget` states is the
number the `add` after it accepts.

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)
