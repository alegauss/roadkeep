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

### §RK348 The refusal that is about somebody else's line

Shipping RK325 was refused with `why: 173 characters, limit is 171: delete 2
characters`. Nothing about the call was over: the `--why` being written was 119. The
line at 173 was RK327's, which names RK325 as a dep — and `(deps: RK325)` becomes
`(deps: RK325 ✅)` when the ship re-derives it, two characters that leave the prose
budget two short.

The refusal is correct and unreadable. It names the field, the count and the limit, and
every one of those is about a line the caller is not editing and has no reason to be
looking at. What it reads as is *your sentence is too long*, so the author shortens the
one they just wrote, gets the same number back, and has to diff the file to find out
why.

The fact is in the transaction. `refresh` re-derives every dependent's annotation and
knows which line it was validating when the schema refused, so the id belongs in the
message — the same rule every other refusal here already keeps, which is that a length
is reported against `file:line` and never as a bare number.

Worth separating from the repair the author then needs. Trimming a dependent's `why` to
make room for a marker nobody typed is a real edit and a legitimate one; what is not
legitimate is discovering it by elimination. The design question is only whether the
annotation's growth should be *offered* — `--lines`-style — or simply named, and named
is the smaller answer.

### §RK349 One enrichment, four doors

RK312 taught `ref.missing` to name `anchors --block <x>` and the free address under it.
It is wired into `authoring.add`, around the one `place` call that command makes.

Every other write that validates a line reaches the same violation and gets the sentence
as it was. Measured while building RK327's fixture: `defer RK2` on a project whose store
declares `ref` refused with `ref: every task points at its rationale section`, naming
nothing — the exact text RK312 was filed against, one verb over. `resume` writes the
line back and validates it again, and `section add` reaches the same schema.

The asymmetry is worse than the original defect, because a caller who has met the good
refusal once now knows the tool can answer this and reads the bare one as *there is no
answer here*.

What makes it a small task is that the enrichment is already a function of a config and
a block: `_naming_the_anchor(config, block, error)` needs the block, and every door that
refuses a line has one — a `defer` reads it off the line it is moving, a `resume` off
the line it is writing back. So the repair is a shared wrapper at the seam every write
already passes rather than four call sites, which is what would otherwise drift.

Worth checking whether that seam is `place` itself. It has no `Config` today, which is
why RK312 went around it, and threading one in is the change that makes this one line.

### §RK350 The property the survey made and did not keep

RK339 gave `status` and `claim` a refusal naming their read-only near-twins, and found
the second pair by a one-off script: edit distance over the forty-one verbs, crossed
with whether each needs a positional. Exactly two pairs qualified.

That script is the whole finding and it was thrown away. The next verb added is measured
by nobody, so a third pair is found the way the first two were — by somebody typing the
report's name and reading `error: the following arguments are required`.

The shape to hold it in already exists one file over.
`test_every_module_is_named_in_the_layout_index` turned an index that silently stopped
being an index into a gate, on the argument that what held it was a habit; this is the
same argument about a list that grows the same way.

The property is decidable and narrow: for every pair of verbs within one edit where one
requires a positional and the other does not, the one that requires it declares a
`twin`. Both halves are read off the parsers — the distance from their names, the
requirement from their actions — so nothing here is a table to keep in step, which is
the trap `Prose` already avoided.

What it must not do is demand a sentence for every near-collision. `lint`/`list` and
`ship`/`show` are pairs where neither call fails in a way the other's name explains, and
a gate that asked for prose there would be answered with prose nobody needed.

## Block C — Query

### §RK345 The one budget with no pre-write read

`budget` answers what a line leaves its prose fields, what an anchor leaves a section
and what a non-goal may cost — every limit this format holds, read before the text
exists, which is L1's whole argument. `[budgets]` is the exception, and it is the limit
that binds hardest: `agents.md` here is 125 lines of 125, so any edit to it is a trade.

Measured while shipping RK330. Naming one new module in the Layout index costs a line
the file does not have, and `tests/test_linting.py` requires the naming — so two gates
meet at an edit composed against a number no command reports. What was done was two
`python -c` reads of the file, a subtraction by hand, and a second attempt when the
first spelling was one line over.

That is the analysis L1 exists to remove: the author is asked what to cut *after*
writing, which is the linter-shaped failure this tool was built to stop, one file over.
The answer has the shape every other budget read has — what the file costs, what it may
cost, what that leaves — asked of a declared budget rather than of a field, and derived
from the file on disk and `roadkeep.toml` with nothing to compose.

Not a second gate: `lint` refuses the file that went over (RK30), and a second reader of
one number is the disagreement RK50 removed. This one reaches the author before the
edit.

### §RK346 Two fields, one free address

RK340 made the free top-level address a question per namespace: two prose files that
each number their own outline have two answers, and one number across both hands the
shorter file the taller one's. The listing prints a line for each. The JSON grew a
second field beside the first — `next_families`, a row per namespace — and kept
`next_family` as it was.

Which is the shape a compatible field usually has and is not one here. `next_family`
answers for the *unprefixed* namespace, so on a project that declares `[refs]` for both
its prose roles it answers for a namespace that no longer exists and returns null; on
one that declares it for a single role, it answers correctly for the other and says
nothing about which. A client written before RK340 reads a number that is right by
coincidence.

Two readings with no way to tell them apart is what `ref.ambiguous` says about an
address, one layer down. The remedy is the one this format applies to a line: an answer
whose meaning is stated, and a caller wanting one namespace names it — which the row
already carries. What the older field costs is a decision about this tool's own JSON
surface, and it is a small one: the command is a read with no writer downstream.

## Block D — The gate

### §RK320 A hook that stages more than it wrote

RK153's argument stands: a checkout whose plugin version never moves is one the session
keeps running the old copy of, so `.githooks/pre-commit` bumps on every commit and never
blocks. To make the bump part of the commit it has to stage what it wrote, and it does
that with `git add -- src/roadkeep/__init__.py .claude-plugin/plugin.json` — two paths,
whole.

Whole is the problem. Measured in one session: another agent had edited
`.claude-plugin/plugin.json` in the working tree, removing a key deliberately; the next
commit was an unrelated fix, the hook staged the file to write the number into it, and
the key removal landed under that commit's message. Bisecting the manifest now names a
commit whose subject is about something else, and the author who made the change has no
commit carrying it.

This is the failure a scope exists to prevent (RK280), arriving past it: `claim <id>
--path` says what a commit owns and `ship` prints the `git add --` line for exactly
that, and then a hook stages two more paths nobody declared. What needs deciding is
whether the bump can stage only its own diff — the number is one line in each file — or
whether it refuses when either file carries an edit it did not make.

### §RK326 A queue the gate cannot read

`Config._check_priority` already states the rule this asks for: an entry `pick` cannot
resolve "is a queue the author believes is in force and is not", and a silent one is
worse than none. It then checks the spelling alone — is the token an id of this project,
or `Block X` — a config parser having no roadmap to resolve it against.

Measured on a scratch project: `priority = ["QQ1", "Block Z", "QQ9"]` with QQ1 shipped,
no heading declaring Z and QQ9 in no file lints clean, while `pick` answers "the
declared priority names nothing ready" — one sentence covering three deaths and naming
none. Written as deps, two of those tokens are `dep.unknown` and `dep.no-block`.

Once RK325 puts the list in the roadmap the resolution is the one `backlog` already
does, so the codes are the states a token can be dead in: shipped, retired, set aside,
naming nothing, naming a block whose every line has left, and named twice — at
`file:line:column` like everything else here (RK34).

Two states are **not** findings. An entry naming a task that is merely blocked is a
queue doing its job. And a declared block holding nothing yet is legitimate, `block add`
writing the heading before the lines, so it is a note — told apart from an emptied block
by whether the ledger has entries under that heading.

A `priority` left in the config is the third: read, and named as a note beside the
section that now holds the order.

### §RK328 The dead entry is mechanical

RK16 splits the gate's findings in two: mechanical, recomputed from what is already
there, and editorial, needing a decision a tool making it would be writing prose. A
queue entry whose task shipped is squarely the first. There is exactly one repair, it
chooses nothing, and no sentence of anybody's is touched — the same class as a stale dep
annotation.

RK327 closes the common case: a departure takes its own entry out, so the queue cannot
go stale through the door work normally leaves by. What is left is the drift every other
file already has a fixer for — a hand edit, a merge that resolved into a list naming
both sides' ids, an adopted backlog whose order predates the section. `fixing` is where
a governed file's mechanical repairs live, and after RK325 this is a governed file.

Two things stay editorial, and they are why this is not "make the queue match". **Order** is the
author's whole statement, so nothing here reorders. And an entry naming a task that is merely
*blocked* is live: dropping it would delete a declaration because a dep has not landed yet.

What that leaves is the state the complaint was about — a queue accumulating the ids of
finished work — cleared by the command the `roadkeep-lint-fix` hook already runs, with
every entry it dropped named in the report rather than removed in silence. A fixer that
shortens a plan quietly is the one thing worse than the stale entry.

### §RK333 One tool, two names, and the refusal knows neither

RK58 put the MCP route ahead of the shell form on one argument: the plugin that refused
the edit is the plugin that installed the tool, so naming it is naming something
certainly present. Measured against the published payload, with `claude --plugin-dir
<tree> -p "<enumerate them>"` from a project that is not this one, the tools come back
as `mcp__plugin_roadkeep_roadkeep__add`. The bare name is what a *project* `.mcp.json`
produces — this checkout, and any project `install` wired — and the docs are explicit
that a matcher written against it never fires for a plugin server.

So both names are right, each in one scope, and `guarding` states one of them
unconditionally: `mcp__roadkeep__{name}` is built at line 266, `commands/add.md`
declares `allowed-tools: mcp__roadkeep__add`, and the skill tells the reader to prefer
`mcp__roadkeep__*`. In the plugin's own audience, all three name a tool the session does
not have — which is worse than the shell form the refusal demotes, because that one at
least fails loudly.

What is undecided is how the guard could know. The hook payload says which tool was
denied, not which server offered the alternative, and the two spellings differ by the
plugin name, which `${CLAUDE_PLUGIN_ROOT}` implies but nothing in argv states. Naming
both is the cheap answer and doubles the sentence; deriving it needs a fact the hook is
not given.

### §RK335 What the third job cost to buy

RK334 is right and this is its bill. `curl -fsSL https://claude.ai/install.sh | bash -s
stable` is the documented install and the shortest thing that works, and it is also a
remote script fetched fresh on every push to main, in a workflow whose `permissions:`
key is absent — so the job takes whatever the repository default grants, which is the
one number nobody looks at until it matters.

Two halves, and only one is a decision. The permissions block is not: `contents: read`
is what `publish.yml` already declares for a job doing more than this one, and the gate
declaring nothing is an omission.

The installer is the decision, and the documented routes differ in what they cost to
keep. A pinned version (`bash -s 2.1.89`) makes the reader reproducible and stops it
tracking the loader an installing user gets, which is the whole reason the channel is
`stable` rather than a number. The apt repository is signed with a key whose fingerprint
is published, so the trust moves from a URL to a key, at four more lines and a
distribution this job does not otherwise care about. The release manifest is GPG-signed
too, which is that trust with the version pinned back on.

What makes this a line rather than a shrug: this repository's argument is that a gate is
only as good as what it reads, and the newest job reads a tool it fetches unverified
every time.

## Block E — Adoption

### §RK305 A majority that measures the backlog, not the file

RK288's guard is right about the alarm it silences and wrong about how it decides. It
prints `--ref-scheme <other>` only where the other scheme accounts for more headings
than the declared one — a proxy for *this file is really addressed the other way*.

The proxy holds on a static file. It does not hold here. This repository's rationale
file carries a permanent preamble anchored `0.1`-style and one `RK<n>` section per
**open** design, and a ship deletes the second kind. So the ratio falls with every task
delivered, and at the moment the open designs stop outnumbering the preamble the tool
tells a fully conforming file to be read the other way. Measured while shipping Block B:
five and five, one ship from the alarm, on a file reporting every heading conforming.

What the count cannot see is that the two kinds of heading are not competing readings of
one file. One is prose the project keeps and the other is a queue. A file whose declared
scheme parses **every** heading it was asked about has no minority reading to report,
whatever the ratio — which is the condition RK288 was actually written about, and the
one the majority was standing in for.

### §RK315 A fixture a second session can edit

This repository's docs are the conformance fixture on purpose, and
`test_a_file_that_mixes_anchors_is_not_told_to_switch` reads `docs/IMPROVEMENTS.md` from
the live checkout to assert that a file mixing both anchor shapes is not told to switch.
Measured across three runs of the same commit: one red, two green, with a concurrent
session shipping tasks into that file throughout — the ships delete id-anchored
sections, which is the ratio the assertion turns on.

A fixture git holds is a fixture any process in the checkout may rewrite, so this
failure names the scheduler rather than the code. The round-trip property tests read the
same tree and survive it, because they assert a property of whatever they read; this one
asserts a count. What needs deciding is whether the assertion belongs against a copy
taken at collection, or whether a count over a file the backlog erodes is the wrong
assertion whoever is writing it — RK305 already names that ratio as fragile.

### §RK347 The collision an estimate is taken to find

`adopt` exists so the commitment is priced before it is made: what parses, what
conforms, the longest field against its limit, the markers to declare. `--sections` is
that read for a rationale file, and it takes one path.

Which is right for every limit it reports and wrong for the one RK340 added. An address
is doubled only across two files, so a per-file estimate cannot see it by construction —
and this is the finding an adopting project meets most: measured in one,
`IMPROVEMENTS.md` and `STRATEGY.md` both open at `I` and both declare a `III`, which is
four `section.ambiguous` on the first run of the gate, against files the estimate had
called conforming.

The read exists: `history.doubled` answers it over the project, and `anchors` already
prints it. What is missing is that `adopt` asks — and that having asked, it names
`[refs]` as the declaration that makes the two sets two, which is a line of
configuration rather than a renumbering of somebody's document.

The estimate stays a read that writes nothing and exits 0 (RK18): what is added is a
figure in it, not a refusal. An adopter told the number before they commit is the whole
point of the command, and this is the one they are most likely to be surprised by.

## Block F — The plugin
