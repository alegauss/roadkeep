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

### §RK1187 The prose field the pipe convention skipped

RK329 made every prose argument read the pipe and RK1176 moved the claim into the
parser, resolved once in dispatch with the two-into-one refusal asked for every verb.
`add` declares two readers, the body and the `why`; `restate` declares none. So
`symptom` is the field the convention skipped, and `restate` is the verb with no pipe at
all — the one whose only prose argument is a symptom.

Refusing `-` by name is the wrong half of the door. A symptom carries the backtick, the
apostrophe and the `§` exactly as a `why` does, which the lines in this file
demonstrate: RK1184, RK1185 and RK1186 all quote a command in theirs. The field wants
the pipe for the same reason the `why` was the argument RK329 was really about, and it
is the field a shell most quietly corrupts, because a symptom that lost an apostrophe
still reads like prose somebody wrote.

Nothing downstream can catch it either, which is why the door is the parser's. A bare
dash is a one-character symptom: it clears every limit, renders, round-trips and passes
the gate, so the file keeps a claim no rule can call wrong. `restate --typo` is
untouched — a declaration is not prose — and `add --symptom - --why -` needs no new
refusal, being two arguments asking for one pipe, which dispatch already names.

### §RK1196 The two places a false premise is also written

`restate` exists because a premise turned out false, and it is deliberately narrow: the
id, the deps, the marker and the section all stay, because the work never changed and
only its description was wrong. That narrowness is right. What is missing is that this
is the one verb here which knows a claim was wrong, and it says nothing about the two
other places that claim is written down.

Measured on a real task. A line asserted a build died on a stale artefact with a
particular error; investigation showed a different error and a different cause.
`restate` took the new symptom and reported `the premise this line asserted turned out
to be false` — and left a `why` still explaining the old premise and a section arguing
from it, both of which had to be noticed by the same author, from memory.

The precedent is `ship`: it names any section whose prose cited what it deleted, and
says that citation is your next edit in *this* commit, because a stale pointer reads
like a typo from the next command on. A `why` arguing a premise the line no longer makes
is the same defect with no pointer to catch it.

The answer is a report and not a refusal. Whether the `why` still holds is a judgement
about meaning, which this tool has none of — so it names `amend` and `section amend`
with the id already substituted, and leaves the reading to the author.

### §RK1198 The path to a first add is discovered one refusal at a time

Observed filing three tasks into a project whose `ref_scheme` is `outline`, into blocks
whose every line had shipped. Each refusal is individually correct and names the next
verb. Together they are a staircase: `add` refuses for a missing `--ref`; `anchors
--block` refuses because no open line in that block carries a pointer; `anchors
--only-next` answers a free top-level; `add` refuses because no heading declares the
block; `block add` writes it; `add` refuses again because the anchor has nothing to
extend; `section add` writes the family; `add` lands. Six calls before the first write,
and the prose was ready at call one.

The information was there at the first refusal. `add` knew the block, whether a heading
declared it, that its families were spent and what the next free top-level was —
everything the remaining five calls established. Reporting one step is right when a
caller is one step from done and wrong when they are six, because a staircase discovered
a stair at a time reads as a tool changing its mind.

So: when the first refusal can compute the whole path, print it — the ordered verbs with
their arguments filled in, not a description of them. RK1188 is the sibling question
(*what are the blocks called*); this is *what does filing into this one take*.

Worth deciding: whether `add` grows a `--plan` that prints the sequence without writing,
or the refusal carries it. The refusal is the moment the author is actually in.

## Block C — Query

### §RK1188 The one question before every add has no verb

`add --block <x>` is the first flag on the first write of any new task, and nothing
answers what `<x>` can be. `stats` prints letters and counts, never titles. `list
--block` and `delivered <block>` both demand the letter as an argument and refuse one
nothing declares, so neither can discover it. The guidance to place a task in the block
whose theme covers it is guidance against a fact the tool does not state.

So the author reads `docs/ROADMAP.md` with grep. That is the file the hook exists to
keep hands off, and the habit it teaches is the one every other refusal is spent
unteaching. Observed twice in one session on two different projects, the second time to
file this.

The shape is already there: `non-goal list` answers "what may I not propose" with no
argument at all, and this is its sibling — "where may I put it". Something like `block
list`, printing each block's letter, its title and its open count, in file order, since
order is what a reader takes for the shape of the plan. The counts `stats` prints are
the same read, so the two want to agree rather than be two answers.

Worth deciding: whether this is a new verb or `stats` learning the titles it already
walks past. The argument for a verb is that `stats` is a report about a file and this is
a question asked before writing to one, and `block add` and `block drop` already own the
noun.

### §RK1190 The allowance is knowable and the draft is not

RK190 made the allowance knowable before the first word exists, and that is not this.
`budget` answers "this line leaves 174 characters for `why`, this section 250 words". It
cannot be handed the draft. So the only thing that measures prose against its limit is
the write that refuses it.

Measured on one session driving another project: eight refusals on length, several of
them three or four retries for a single task, each costing the whole field again. The
refusals are good — they name the count, the limit, the deficit, and which paragraph is
longest — and none of that is reachable until something has been sent.

`--section-body-file` and `--body-file` already remove the *re-send* cost, which is the
half that was solvable without a new read. What stays is the round trip and the
guessing: told "delete 3 words", an author cuts and sends again, and the second answer
is "delete 1".

The shape is `budget --anchor RK12 --body-file draft.md`, and the same for a `why`, so
the subject flags that exist say what the draft is measured against. It counts with the
writer's own counter — a second one that disagreed would be worse than none.

Two things to settle. Whether it exits non-zero when over so a script can gate on it, or
stays a report like the rest of `budget`. And whether **stdin** is accepted here: a pipe
does not rewind, but this writes nothing, so the objection that shaped the writing verbs
does not apply.

### §RK1199 The second figure, and the ten it does not have

Measured on one task, with both numbers printed by this tool about the same line and
nothing between them changing its symptom.

`brief --claim` said:

    budget    why 19 of 160 left
    shipping  why 29 of 170 left on the ledger line a `ship` writes, which is the limit
              that refuses it

The `ship` that followed said:

    why: 183 characters, limit is 180 (the line's own limit of 320 leaves 299 for prose,
    and the symptom takes 119)

RK1174 put that second figure there precisely so the ceiling a ship enforces would
arrive before the write, and 320 − 299 = 21 of structure against the roadmap line's 31
is the difference the two verbs already agree on. The remaining ten are not: `brief`
predicts 170 where `ship` allows 180, so it is measuring the ledger line against a
structure ten characters wider than the one written.

The direction is the safe one — under-reporting never refuses a sentence that would have
been accepted — and it is still wrong in the way that matters. The figure exists to be
composed against, so ten characters it does not have to spend is a clause cut for
nothing, and a reader who trusts it and then sees `ship` allow more has been told two
things.

Worth establishing first: whether the ten are the dep annotation, which a ledger line
does not carry and a roadmap line does, and whether the same gap appears on a `--part`
and on a line with deps, where the structures differ again.

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

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
