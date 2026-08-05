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

### §RK298 The scope that leaves with the claim that held it

Hit once per task across Block D. `agents.md` documents the commit as `claim <id>
--porcelain` piped into staging, and RK280 is the reasoning: `git add -A` sweeps up a
second session's work, so a claim carries the paths this commit owns. But the order the
work happens in is claim, code, `ship`, commit — and `ship` releases the claim, which
takes the scope with it. Reproduced on a scratch project: after `ship RK1 --why …`,
`claim RK1 --porcelain` exits 2 with "no live claim on RK1", and the move it names,
`status RK1 🛠`, exits 2 too because the ledger now holds the id. The verb that answers
"what does this commit own" is unreachable exactly where the commit is, and the
refusal's advice is a dead end rather than a detour.

Two shapes, and the choice is the design. `ship` could report the scope it released,
putting the answer in output the committer is already reading — the shape it uses for
the section it dropped. Or the registry could keep a released claim's paths until
something else claims that id, so `claim --porcelain` answers after a ship; that is a
longer-lived record, and RK119 was explicit that a claim is an expiry and not a lock, so
it needs an argument this section does not have.

What must not be the answer is a sentence in `agents.md` telling the author to read the
porcelain before shipping. Ordering held by prose is the drift this tool exists to
remove.

### §RK302 The door that admits the state four verbs refuse

`SectionExists` asks the document it is writing into and nobody else. RK297 taught the
*read* that an outline spans every declared prose file, and `_refuse_reuse` with it —
but that one catches a **retired** address, which is the case where history is the only
witness. A live one is visible in the sibling file, and no check looks.

Reproduced on a project declaring both roles: `section add IX --role improvements`,
`section add IX.1 --role improvements`, then the same two into `strategy`. All four
succeed and print their line counts. `lint` then reports four `section.ambiguous`
findings, and the message it prints is the argument for refusing at the door: *one
anchor names one section, so no pointer here resolves and every verb that reads one
refuses.*

So the write path builds a state its own gate calls unresolvable, and the four verbs
that would repair it are among the ones that refuse. `anchors` names the doubling now
(RK297) but names it afterwards, and `drop` is the only exit — which deletes prose
somebody wrote.

The shape is the one `_refuse_reuse` already has: the project's declarations rather than
the file's, asked one line earlier. What needs deciding is whether the refusal names the
sibling file's line number, which `declaring` can already reach, and whether a `--force`
exists at all — RK297's evidence says the doubled anchors in the corpora were made by
hand and not by this verb, so a door that never opens is the cheaper answer.

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

## Block D — The gate

## Block E — Adoption

## Block F — The plugin

### §RK267 A note that knows more than it says

RK155 made the MCP server say when its own modules moved after it imported them, because
a config key added in one commit made every write refuse `unknown key` while the CLI
accepted it. The note works. What it does with the relevance question is hand it back:
it lists every module `Engine.stale` found and closes with "re-run only where the
changed files are the ones that would decide this", which is the reader being asked to
know the call graph of a refusal they did not raise.

Measured while shipping RK255: a `why.too-long` refusal — decided by `schema.py`,
unchanged — arrived naming `cli.py`, `merging.py` and `provenance.py`, three modules
that could not have decided it. The note was 450 characters of correct and irrelevant
text on a refusal that had already said everything actionable in one line, and it fires
on every error in every session that edits this package, which is every session that
develops it.

The module that raised the refusal is knowable: the exception has a traceback, and the
frames above the server are this package's. Intersecting that with `Engine.stale` turns
the note from an inventory into a judgement — say nothing when the sets are disjoint,
and say which module when they are not. The risk is a refusal raised in one module
because a helper in another changed, which the intersection misses; that argues for
narrowing the sentence rather than suppressing it, and for keeping the full list behind
the one module that is named.

### §RK275 A check the agent it was built for cannot call

L5 is that every question is a command, so answering one costs no context. `merge
--check` is exactly that shape: it writes nothing, reads two facts, answers in three
lines. The MCP server exposes the query surface — `list`, `brief`, `budget`, `deps`,
`weight` — and not this one, so the agent the plugin exists for reaches it by shelling
out or not at all. In practice, not at all: nothing prompts the question, and an unwired
driver is silent until the merge it was registered for.

The reason it is absent is that `merge` is git's driver contract. Three positional
paths, a `--path`, an exit code git reads — none of that belongs in a tool an agent
calls, and the server was right to leave the verb alone. But `--check` is not that verb
sharing a name; it is a different command wearing the same subparser, which is why it
needed a flag.

The shape to decide: whether the server grows a tool for a flag — one subparser per task
is the mapping, and this the first exception — or whether `--check` becomes its own
subcommand, `merge check`, picked up by the rule the server has.

The second was argued for as cheap "before it is load-bearing". It no longer is: RK272,
RK273, RK274, RK277 and RK278 each put behaviour behind that flag, so the rename moves a
documented command with five decisions in it. Not an argument against — the measure of
what an exception would hold.

### §RK304 The bound that stayed prose

RK24's claim is that the input schema *is* the format's schema: `maxLength` is this
project's limits, `enum` is its declared markers, `pattern` is its id shape. The point
is the protocol refusing a wrong argument before the call, which is L1 one layer out.

`role` is the remaining closed set and it publishes neither. Measured on this
repository: `section_add`, `section_amend`, `section_drop` and `budget` each describe it
as *"which prose file"* and give the client nothing to validate against, so `role =
"notes"` is a well-formed call the server refuses. The set is not a guess — `config.has`
over `PROSE_ROLES` is the same narrowing `_paragraphed` already makes to decide which
limits to publish (RK259), so the answer is one line from a function that already
computes it.

Two things it is not. It is not `choices` on the parser: `--role` accepts a role the
*project* declares, and argparse would have to be rebuilt per project to say so. And it
is not a bound the client may skip — `argv` checks what it publishes (RK111's rule), so
whatever is added here is checked at dispatch too.

Worth deciding whether `--role` on `anchors` joins them. It narrows a listing rather
than choosing a write target, and RK297 made it the one flag that does not change the
number an author acts on.
