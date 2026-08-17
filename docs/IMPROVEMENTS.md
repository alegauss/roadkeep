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

### §RK1211 The one address this tool spells for you

`anchors --next` on an outline with nothing in it answers *no outline family exists yet,
so none is spent — `add --ref I.1` opens the first*. `I` is roman, and it is written
into that sentence by hand rather than derived: the file has no family to read a system
off, which is why `next_family` answers None here at all.

So one half of this command declines to guess and the other half guesses. `numeral`
reads roman and decimal, `spell` writes back in whichever was read, and both exist
because the numbering is the author's (L4, L6): a project outlining `1`, `2`, `3` is as
ordinary as one outlining `I`, `II`, `III`, and it is told to open `I.1`.

Following that advice makes the file this tool then cannot read. Measured: a project
holding `1` and `1.1` was offered `I.1`, took it, and its top levels became `1` and `I`
— two systems tying at 1, which is RK1210's nondeterminism. The message is the door into
that defect, and the defect is invisible from the message.

Two readings are available. Naming no address — *`section add <your first family>` opens
the outline* — costs the caller the one decision only they can make. Naming both —
*`I.1` or `1.1`, whichever this project numbers in* — shows the choice exists, which
today's sentence hides. What it must not do is keep one spelling: a first address
chooses the system for every address after it, and this tool has no opinion (L4).

### §RK1216 A query that never ran, reported as a migration finished

Measured in pportal on 2026-08-16, declaring the first queries that project has. Two
sections were given `lib/src :: <regex>`, which reads as a directory and which Path.glob
matches as one file entry that is not a file. Both answered:

    PP30  0 site(s) left in 0 file(s)

The regexes were right. Counted by hand over the same trees they find 14 and 420.
Corrected to `lib/src/**/*.c` the tool agrees exactly, so nothing was wrong but the
glob.

What makes it worth a line is which way the failure points. remaining's own docstring
says a query answering 0 says the pattern no longer matches, and that is the reading an
author gets: the migration is done. The true reading here was the opposite - the query
never ran over anything. A tool whose failure mode is indistinguishable from success, on
the one question it exists to answer, is reporting a number nobody can trust without
re-deriving it, which is what the query was meant to replace.

The tell is already printed - `in 0 file(s)` sits beside the count - so this is about
which of the two the eye lands on, not about missing information. Two candidates. Say it
in words when the pathspec matched nothing, since a query over no files is a different
event from a pattern with no sites. Or refuse it: an author who declares a query over a
path that does not exist has made a typo, and lint already refuses a pointer at a
section nothing answers for the same reason.

## Block D — The gate

### §RK1192 The check nobody runs

`install --check` already answers this exactly, and that is the problem: it is a command
nobody thinks to run. Nothing prompts it, no failure names it, and a project only
reaches it by already suspecting what it reports.

Measured, in a session on another project. The committed launcher there predated RK1116,
so it forwarded only `guard` and `mcp`; the MCP server had not connected; and the skill
that session read named that launcher as the entry point. Every door was shut, and the
way out was guessing a version directory under the plugin cache — the one route no
document mentions, because it is not supposed to be one.

The gate is what runs anyway. `lint` fires on every turn through the `Stop` hook, it
already reports drift between what a file says and what the tool would write, and a
wired surface behind the version answering is drift of that kind. The finding names
`install`, which is the complete command that closes it, so `repair` closes it too.

Two things to settle. **The comparison is against the answering engine and not the
newest one**: three copies are allowed to differ and `engines` adjudicates that, so this
must not become a second opinion about which version is right. And **a project that
deliberately pins an older surface must be able to say so**, or the finding is noise a
reader learns to skip — which is how a gate stops being read.

### §RK1202 A gate whose failure looks exactly like its consent

Measured in pportal on 2026-08-16. A file containing the bytes `not json at all`,
redirected into `guard`, produces no output and exit 0. That is byte for byte what a
governed path being allowed looks like, and what a session with no engine looks like,
and what a payload naming an ungoverned file looks like. Four states, one answer.

The cost is not hypothetical. A pportal session probed this guard by piping a payload
from PowerShell, whose pipe does not deliver the UTF-8 the reader wants, saw exit 0, and
wrote a project note asserting nothing denied a hand-edit there. The guard was working:
the same payload written to a BOM-less file and redirected in gets the full denial. The
note was wrong for four days and the design it accused was fine.

The asymmetry is what makes it bad rather than merely quiet. `allow` must be silence,
since printing `permissionDecision: "allow"` would grant a write the harness had not
decided to grant. Nothing forces a *failure* to be silent too. A payload that will not
parse is not a decision about a tool call; it is the gate not running, and the only
audience is a person checking it is alive.

The remedy is one line to stderr on a payload that does not parse, which the harness
ignores and a person reads. Exit 0 should stay: a gate that fails a turn because it
could not read its own input is the failure the launcher exists to avoid.

### §RK1203 The path.missing door on a ledger line names a verb that refuses it

Found adopting Turing, whose ledger holds 755 entries written before the tool existed.
`lint` reports `path.missing` on a **changelog** entry — T759 names
`frontend/apps/site/scripts/emit-model-catalog.mjs`, true when it shipped and false
since the catalog moved to its own repository — and emits exactly one door: `amend T759
--why …`, kind `compose`, with the matching MCP call.

Following it produces `no open task T759 in docs/ROADMAP.md: it is already in the
changelog`. `amend` loads the roadmap, looks the id up in `roadmap.by_id()` and raises
`NotOpen` for anything the ledger holds; it was built to correct an open line and says
so. So the one remedy offered for this finding is the one verb that structurally cannot
perform it, and an agent that trusts the door spends a call learning the door is shut.

Two things are wrong and only one is the door. A ledger entry recording a path that was
real at ship time is not drift — it is what history is *for* — so the check itself wants
a notion of "true when written". And the remedy, if one is offered at all, has to name a
verb that reaches the ledger: `record amend` exists for that file, and the 200-character
cap on `amend --why` would refuse this 1,600-character entry even if it did.

Minimum: stop emitting an unfollowable door. Better: let a ledger path be resolved
against the commit that shipped it.

### §RK1206 The remedy composed from a field the finding did not read

The finding names one address and its remedy names another. On a project whose
`ref_scheme` is `outline`, a line pointing at `§I.1` with no such section is reported as
`TT1: points at §I.1, which is not in docs/IMPROVEMENTS.md` — correctly — and the
command underneath it reads `section add TT1 --title …`. `TT1` is the task's id; the
missing section is `I.1`. Run as printed, it writes a section the line does not point
at, and the finding survives with a second orphan beside it.

RK14 and RK326 settled that every finding carries the command that closes it, and the
whole value of that is that the command is *runnable*. A remedy composed from the id is
right under `ref_scheme = "id"`, where the anchor is the id — which is this repository,
and so the shape its own conformance fixture can never catch. It is wrong under an
outline, where the pointer is the address and the id is not one.

The fix is that the remedy is composed from the same field the finding reads. The gate
has the anchor in hand: it is what the resolution failed on, and it is already printed
in the sentence one line above. Nothing needs deriving.

Worth checking at the same time whether any other finding composes an address rather
than reading one, since this class is invisible here by construction: a repository on
the id scheme cannot tell the two apart, and the corpora at `tests/corpora.py` are what
can.

### §RK1214 An engine that is found and then explodes

Measured in pportal on 2026-08-16, mid-task. A `section add` that had worked four times
in the same minute came back as a traceback: ImportError, cannot import name NotOpen
from roadkeep.backlog, while importing roadkeep.cli. The engine the launcher resolved
was the sibling checkout, whose working tree was part-way through a refactor. Nothing
was written, and the roadmap was left holding a line whose section did not exist - lint
red, mid-task.

The launcher's own docstring makes this a defect rather than bad luck. It says: never
block a turn, and if no engine can be found every mode exits 0 and emits nothing, so a
missing roadkeep degrades to unenforced and never to a broken session. A checkout
mid-refactor is not missing. It is found, chosen, and then it explodes - the failure
that rule exists to prevent, arriving through the one door it does not cover.

The resolution order already has the material for a fix. _resolve tries ROADKEEP_HOME,
then a sibling, then a cache, then a clone, and stops at the first path that exists.
Existing is the wrong test: what the caller needs is an engine that runs. Importing the
chosen one and moving to the next candidate when that raises would cost one try block
and would have turned this into a slower command rather than a failed one.

This is separate from RK1200, which is about which candidate is picked. This one is
about what happens after a pick that turns out to be wrong.

### §RK1217 The ledger's paths are checked against the wrong tree

Turing's `T759` entry names `frontend/apps/site/scripts/emit-model-catalog.mjs`, a
script that existed when the work shipped and was later extracted into its own
repository along with the model catalog. The entry is accurate. The file is gone. `lint`
reports it every run, and will keep reporting it.

`_candidates` already forgives a path that moved **within** the repository —
`tree.anywhere` catches a rename — but one that left it entirely has nowhere to be
found, so the rule reads a correct statement about the past as drift.

What makes it worse than noise is the door. The remedy composes `amend --why`, which
replaces the entry's whole sentence under `[limits] why` at 200 characters — while
`[limits.changelog]` lets that same entry run to thousands, and `T759` spends about
1,500 of them on what was built. The offered fix for a stale path is to delete the
as-built record that made the entry worth keeping. Nobody takes that door, so the
finding stays forgiven by baseline forever.

The tree the question is about is the one the entry was written against, and git knows
it: the revision that added the line, or failing that, whether the repository ever held
the path at any revision. Either reading answers `T759` and still catches what the rule
is for — a path this repository never had.

If walking history per entry is too slow for a hook, ask the working tree first as now,
and only for a token that fails ask whether history held it.

## Block E — Adoption

### §RK1193 Adoption stops one step short of a pinned engine

`roadkeep-launch.py` resolves an engine — `$ROADKEEP_HOME`, then a sibling checkout,
then a cache — and `install` wires a project's four surfaces. Neither *puts an engine in
the project*. So an adopter that wants a pinned, stable copy has to write that
themselves.

Two now have. Shio and freewilly each carry a 147-line `install_roadkeep.py` plus a
`.cmd` wrapper, byte-identical apart from one comment, vendoring into a git-ignored
`.roadkeep/` with `ROADKEEP_HOME` pointing at it. That is the `node_modules` shape and
it works — but it is the same code in two repositories, which is the drift this tool
spends its own backlog refusing elsewhere.

Why an adopter reaches for it at all, measured on one machine: **six** engines were
resolvable — 0.1.841 and 0.1.820 under `~/.claude`, 0.1.678 and 0.1.645 under
`~/.claude-pessoal`, plus two marketplace clones — and a live checkout can be
mid-refactor, which cost a session an hour to `ImportError: cannot import name
'_print_claim'` out of a half-edited tree. Add that a changing absolute path is a fresh
authorization prompt every time, and pinning stops being a preference.

The shape the two copies converged on, if it is worth adopting: pick by **version**
rather than by position (ask each candidate `--version`, take the highest), skip a
working checkout unless `ROADKEEP_SRC` names it, exclude `.git` so the vendored tree is
an artefact and not a second repository, and verify after copying that the target
answers the version that was chosen.

`install --vendor` would make it one command and one implementation.

### §RK1200 The engine a vendoring project cannot reach

The committed launcher resolves an engine from three candidates: `$ROADKEEP_HOME`, a
sibling checkout at `../roadkeep`, and a cached clone. A copy vendored *inside* the
adopting repository is none of them, so a project that carries one has to reach it
through the environment variable — and that is where it breaks.

Measured on an adopting project. Its `settings.json` sets

    "env": { "ROADKEEP_HOME": "${CLAUDE_PROJECT_DIR}/.roadkeep" }

which is the spelling `install` itself writes into every hook `command` in the same
file. The harness passes `env` values through verbatim, so the variable arrives with its
braces intact, `Path(home)` names nothing, and resolution falls through to the sibling —
a neighbour's working tree, a version ahead, and mid-refactor for part of a session,
during which the guard denying hand-edits of the governed files was running a traceback.

Nothing said so at any point. `_resolve` returning the second candidate is
indistinguishable from a project that meant to use it, and the drift report then names
that checkout as the one to run `install` from, which is the copy the project did not
choose.

Two halves, and the first is the smaller. **Expand the variable** — both `${...}` and
`$...`, because a settings file may carry either and being wrong is silent. **And make a
vendored copy a candidate**, ahead of the sibling: vendoring exists precisely so a
neighbour's tree is not a dependency, and a repository that carries `.roadkeep` has
already said which engine it means.

## Block F — The plugin

### §RK1218 Two commands to file one task

Filed from fourteen sessions driving another project's backlog, where every task cost
the same two commands: `add` writes the line and prints that the pointer it just wrote
resolves to nothing, then `section add` writes the prose it points at. Between them the
roadmap is in a state this project's own lint calls ref.unresolved.

The window is short and nothing was lost in it, so the cost is not corruption. It is
that the tool says it has left the docs wrong and then asks you to fix that yourself,
once per task, forever. A caller interrupted between the two commands - or who forgets,
which is why the warning exists - leaves a dangling pointer for lint to find later.

The separation is defensible: a line is a claim and a section is an argument, and being
made to write them apart is what stops a one-line symptom standing in for a rationale.
That is worth keeping. What is not worth keeping is that the defensible order is the
only order, when the caller already holds both halves at the moment they run `add`.

So let `add` take the section with it, by the same `--title` and `--body-file` it would
be given next, and write both or neither. The two-command path stays for the caller who
wants to think between them. The budget refusal has to apply to the combined form too,
or this becomes a way to smuggle prose past the limit `section add` enforces.

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)

### §RK1209 The composer tested against itself

Four tasks found the same defect and no test found any of them. RK1149: the retry a
refusal offered had to be retyped. RK1198: the path into a fresh block was six calls
discovered one at a time. RK1205: the `section add` an `add` handed over was refused.
RK1207: the refusal for that family named no verb.

Each was covered. `test_the_command_offers_a_follow_up_that_runs` is the sharpest
reading — named for the claim, asserting the sentence was printed, never running it,
green for as long as the command it described refused. Matching a composed command tests
the composer against itself.

The three tasks that fixed one each wrote the same instrument by hand: RK1149 executes
its retry, RK1198 walks its four steps, RK1207 runs the chain it names. Three copies,
one shape, and the next composed command is covered by whichever session remembers to
write a fourth.

`invocation()` is called at 56 sites, so the population is enumerable and already named
by one function. What a sweep needs beyond that is the placeholders: `<its title>` and
the trailing ellipsis stand for prose only the author writes (L4), so a harness fills
them per verb — three entries covered every step of RK1198's path — and runs what is
left.

Not every site is reachable. So the sweep is a **declared** set with the unreached ones
carrying a reason, the shape `test_surfaces` uses for a write that is wired or exempted:
an exemption nobody can see reads exactly like a rule being kept.
