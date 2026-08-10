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

### §RK1012 The two the backstop register found

RK1004's rows are three answers, and these are the only two of the third kind. `section
add` refuses a body with no prose and a heading with no title; a file carrying either
lints clean, measured on a fixture whose line points straight at the heading.

Neither is cosmetic, and the pointer is why. A line renders `→ §<id>` and the gate holds
that the address resolves — so a heading with nothing under it satisfies that check
while giving the reader none of what the pointer promised. `show` prints the section and
`brief` hands it to whoever starts the task: both answer with a title and a blank.

The five rows beside them are a different answer and stay silent: a heading is one line,
so a newline in a title is about an argument, and an address this scheme cannot read is
not parsed as a section at all, so the heading is prose. Those are not holes, and a code
for them would be a red nobody keeps.

The gate already walks every section for its budget and its query, so this is that walk
asking two more questions of what it holds — and both are the door's own rules, which is
what keeps the wording one sentence rather than a second judgement.

What proves it: a file carrying either exits 1, the register's two rows move to a gate
code, and prose under an unreadable address is still clean.

## Block E — Adoption

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

### §RK1007 The gate, at the column

The gate's report was built for a reader who is not looking at the file:
`file:line:column`, a code, and — since every finding names the command that closes it —
a complete argv with the id and the line number already substituted. That is, without
anything being added to it, the exact payload an editor's problems panel and its
quick-fix menu take.

So the mapping is a translation and not a feature. A finding becomes a diagnostic
anchored at its column, its code becomes the diagnostic's code, and `explain <code>` is
what the reader follows when the code is one they have not met. A finding whose remedy
is a complete command becomes a code action that runs it; a finding whose remedy is a
marked blank — a title, a shorter symptom, a reason — becomes no action at all, because
the tool does not compose prose and an editor is not the place to start.

Running it is the same child process as the list, on save and on demand. `repair` is the
one action that belongs to the file rather than to a line, and it exits non-zero while
anything is left, so a clean panel means clean.

### §RK1008 The door, not a text box

A view that only reads sends its user to a terminal to write, and the terminal is where
the format is typed from memory. That is the whole failure this project is about, moved
one window across.

The write is worth having only if it carries the schema with it. `budget --block <x>
--dep <id>` answers, before the first word, what the symptom and the why each have left
on this particular line — derived from the id, the marker, the deps and the pointer, all
known in advance. An input that shows that number counting down is L1 at the place a
person is actually composing, and it costs no analysis: the remaining characters are on
screen instead of being discovered by a refusal.

What it must not become is a second validator. The prompt shows the budget; `add` still
decides, and its refusal — which names every field it looked at, in one message — is
what the editor reports. Nothing is written to the file by the extension itself, ever:
the command writes, and the file watcher shows the result. That keeps one writer, which
is the property the round-trip law rests on.

### §RK1009 The fourth copy

Three copies of this tool can already be in play at once — the plugin the hook and the
skill come from, the action CI gates on, and whatever the caller runs — and they are
allowed to differ, which is why there is a verb that reads all three and answers
`agreed`, `behind` or `unpinnable`.

An editor adds a fourth, and it is the one most likely to be wrong: resolved from a PATH
the shell configured, a virtualenv the workspace happens to have activated, or a `uvx`
cache nobody pinned. The failure is quiet. A panel shows findings a commit will not
produce, or misses ones it will, and the reader has no way to tell which copy they are
looking at.

So the resolution is a declared setting, not a search: a workspace names the command,
and the view refuses to answer rather than guess. Whatever it resolves is then a fourth
row in the existing report, with the same three verdicts, and disagreement is stated in
the view rather than discovered when a hook denies a write the panel said was fine.

### §RK1010 Where the client lives, and what proves it

The action, the pre-commit hook, the plugin, the skill and the stdio server all ship
from this tree, and each is declarative: a YAML file or a Markdown file, no build, no
dependency tree. A packaged editor extension is not that. It is a compiled language, a
lockfile, and a publisher account, in a repository whose stated cost is zero runtime
dependencies.

The argument for keeping it here anyway is the one that decided the stdio server: the
failure to avoid is a second implementation of the rules, and the only thing that keeps
a client honest is a test that runs the client against the command that answers it.
Across two repositories that test belongs to neither, and the client grows a Markdown
parser the first time a round trip feels slow.

So: a subdirectory with its own manifest and its own job, gated on this repository's own
`docs/`, and a Python side that gains no dependency and no build step. The split stays
cheap on purpose — a client that never parses the file is a few hundred lines with
nothing to port — so if the publishing cadence turns out to fight a version this
repository bumps every commit, moving it out is a decision made later with evidence
rather than now without.
