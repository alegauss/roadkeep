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

### §RK342 RK342

`claim <id>` is the read-back: it names the declared scope, prints the `git add --`
line, and reports what the tree holds that no claim covers. Measured on a fresh
repository, one path declared, nothing else touched by hand:

    loose    README.md   (no claim names it)
    loose    ROADMAP.md  (no claim names it)

Both are writes of the claiming transaction itself. `brief --claim` moves the marker to
in-progress, and every governed write carries the README refresh RK188 added, so the
files the report calls unowned are the ones the command opening the claim wrote for that
id.

`ship` already has this right — its stage line is the scope plus what the departure
wrote, `src/thing.py CHANGELOG.md ROADMAP.md IMPROVEMENTS.md README.md` — so the
knowledge exists one command over and is not consulted here. The asymmetry is what makes
it a defect rather than a preference: `loose` reads as *a file somebody else touched*,
so the author declares the governed paths by hand to silence it, and the scope now
carries paths that were never the work. That is the analysis `claim` exists to make,
made wrong, on the first call of every task.

What a repair cannot do is hand every dirty governed file to whoever asks: a roadmap the
tree holds may hold another session's add. The distinction available is the id the
transaction that wrote the line already knew — a governed file whose diff is this task's
own line is `mine`, and one that is not stays `loose`.

## Block C — Query

### §RK303 First match, at the one door that had not learned it

RK172 taught resolution that a pointer addresses every governed prose file, and RK186
taught `show`. Two roles declaring one anchor is the ambiguity and not a first match:
`_rationale` answers *"§X is declared by both: one anchor names one section, and a
pointer resolving to two resolves to neither"*, and `lint` reports `section.ambiguous`
at both headings.

`body_budget` (RK283) resolves the role by walking `PROSE_ROLES` and taking
`declaring[0]`. Reproduced on a project holding §IX.1 in both files: it answers
`improvements, 2 written, 248 left` while `show` refuses the same anchor. So the read
built to state a limit before the prose exists states one for a section the author
cannot address — and the number is right about a file that was picked rather than named.

It reaches two commands: `budget --anchor`, and the `section` field every `budget` now
carries (RK301), where the anchor is the line's own pointer and the caller never typed
it.

The direction is the one every other reader took, and the refusal already has its words.
What is worth deciding is whether `--role` stays the way through — it is the caller
naming which of the two they mean, which is the only thing that resolves the ambiguity
without a verb choosing.

### §RK324 Two readers of one marker, and only one of them refuses

Measured on an adopting repository: `show T275` answers `✅  shipped`, and `brief T275`
answers `✅  ready` — same id, same file, same line, one word apart. `brief` then goes on
to print `unblocks 0 of 8 open` and the whole non-goal list, which is the shape of an
answer about work that has not happened.

The marker is right in both. What differs is the second word, and that word is the one a
caller acts on. `brief` exists so an agent can ask what a task costs before starting it,
which means a loop that picks an id from anywhere other than `pick` — a commit message,
a changelog entry, a user naming one — gets `ready` for a task already in the ledger,
and nothing in the rest of the output contradicts it. The rationale section is gone, so
the brief is thin rather than wrong-looking.

`show` already computes the answer, so this is not a question needing a new derivation:
it is one derivation with two readers, which is the shape of RK303 as well. Whether
`brief` should refuse a shipped id outright or answer with `shipped` and no cost is the
decision to make. Refusing is consistent with `amend`, which will not touch a shipped
line; answering is friendlier to the loop that asked, provided the word it leads with
cannot be read as an invitation.

### §RK336 The one address anchors does not report

`anchors` knows this. It reads the retired addresses as well as the live ones — the
whole reason it can say `0 live, 1 retired` — and printing the table puts the highest
family that ever existed on screen. What it never prints is the sentence a caller
writing a new section needs: the next family nothing has ever declared.

Measured in an adopting project. `add --block F --section "…"` refused with
`ref.missing`; the highest live heading was `§XL`, so `--ref XLI` was the obvious next,
and it was refused too — correctly, because `XLI` had been declared and shipped away,
and reusing it would have made the entries citing it cite something else. `XLII` was the
same. Finding `XLIII` took a `git log --all -p` over the prose file. Two refused writes
and a history walk for one Roman numeral, and every fact needed was already inside the
table `anchors` had printed.

This is not RK312, which is about the refusal naming no command and about which family a
*block's* existing prose lives under. This is the opposite question — a family nobody
has used — and the never-reuse rule makes it uncheckable by eye. Both land in the same
command, hence the dep.

One row, outside the per-family table because it is not about a family: the next free
address, in the declared scheme. `add --section` can then default to it, turning the
common case into no argument rather than a lookup the caller performs and retypes.

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
