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

### §RK1302 The door a partial leaves unnamed

Measured on quickshell. QS3 delivered a corpus and a harness; its remainder was two
consumers needing a parser and a renderer, neither written. `ship --part` recorded that
and left the line at ⏳, which is right. The next `pick` handed QS3 straight back, from
the in-progress tier and ahead of everything, and would on every call until two other
tasks ship.

The remedy is one command, `amend <id> --dep <the work the remainder waits on>`, and
after it `pick` moved on. Nothing said so. The partial's answer reports the entry, the
marker and the remainder, and stops exactly where the caller needs the next sentence:
what the line is now waiting for.

That is worth closing here rather than in a habit: this is the one ship that
deliberately leaves work open, and the state it leaves is the one the ranking trusts
most. A caller who does not know the remedy re-picks the same line, works around it with
an id typed by hand, and the file keeps saying in progress while nothing is.

Two shapes fit. The narrow one: `--part` names the door in its answer, the way every
other refusal here names a complete argv. The wider one: `--part --dep <id>` amends the
group in the same transaction, since the moment the remainder is described is the moment
its blockers are known.

Falsified when a `--part` whose remainder waits on unshipped work leaves the caller to
discover `amend --dep` by being handed the line twice.

### §RK1311 One field, three surfaces that do not know it

Observed in pportal, 2026-08-22, attaching a requirement to five existing lines.

`amend --requires console` alone is refused: "nothing to amend: pass --why, --dep or
--ref". The flag is in the parser, is documented in the help two lines above the
message, and works - but the guard that decides whether anything was asked for does not
count it. So the only way to attach a requirement to a line that already exists is to
pass a field that is not changing, which for one of the five meant re-sending a `why`
that then failed the line limit because the annotation had made the line longer. Two
round trips for a field the verb has.

The confirmation is the second half. Passing `--requires` alongside an unchanged `--why`
answers "unchanged: every field already reads that way" - and writes the requirement
anyway. Both cannot be true, and the one that is printed is the one that would stop a
caller retrying. It was only visible because the roadmap line was read directly
afterwards.

`show` does not print requirements either. A line carrying `(requires: console)` shows
deps, marker, section and budget, and nothing about the thing it is actually waiting for
- which is the field a caller asks `show` about when `brief` stops offering the line.

Three surfaces, one field, and the field itself is right: requirements are exactly what
deps cannot express, and declaring them moved this project's queue from a task that
could not be started to one that could.

### §RK1312 A sentence the file wrapped is still that sentence

`section amend --replace` matches the bytes on disk, and the bytes on disk are reflowed.
A section is written to a prose width, so any sentence longer than that width is stored
with a newline and some indentation inside it - and a caller quoting the sentence, which
is how the prose reads to anybody looking at it, is refused for text the section plainly
carries.

Observed in pportal, 2026-08-22, twice in one task. Both times the fragment was a full
sentence copied from `section show`, which prints the prose as it is - so the command
the refusal recommends is the command that produces the text the refusal rejects. The
way through was to shorten the fragment until it happened to fit inside one stored line,
which is guesswork with a round trip attached.

It also makes `--replace` weaker than it looks. A short fragment is what fits, and a
short fragment is what "occurs exactly once" refuses - so the two rules push in opposite
directions, and the caller lands between them.

Matching against the prose with its wrapping collapsed would close it: the same
normalisation that writes the file, applied to the needle before looking. What comes
back out is rewrapped anyway, so nothing about the stored form has to change.

Worth saying that the refusal is good otherwise: it names the section, says the text is
not there, and points at `section show`. It is right about everything except that the
text IS there.

## Block C — Query

### §RK1303 The three budget blocks, and the two that say the same thing

A `brief` answers with three budget blocks: `budget`, the line as it stands; `shipping`,
the line as the ledger would hold it; and `deciding`, the line as a decision record
would. Measured on quickshell's QS8, the three came to some sixty per cent of the
payload, and `shipping` and `deciding` were byte-identical — same fields, same limits,
same numbers.

That identity is not a coincidence of one line. Both are the same closed line: no deps,
no pointer, the shipped marker. They differ only where a project's `[limits]` gives the
decisions role its own numbers, which is a table most projects never write. So on every
project that does not, the second copy states nothing the first did not.

The read exists to replace opening the file, which makes it the read a tool result
truncates first — `[reads] brief` and `budget --brief` both already exist because that
is known. What they measure is the total; what this line is about is the share of that
total which is a repeat.

Two doors, and which is right is the design: emit `deciding` only where it differs from
`shipping`, naming that it was elided; or fold the three into one block with the fields
that vary marked per stage. The first is smaller and keeps the shape callers already
parse.

Falsified if the two blocks diverge on a project with no `[limits]` table per role,
which would make the repeat a coincidence of one corpus rather than a rule.

### §RK1304 What the priority is waiting on

Observed over four consecutive sessions on a port whose roadmap declares Priority as
Block H then Block I. Every task in both blocks is blocked, so brief falls through to
the lowest ready id and reports: picked - lowest ready id; the roadmap's queue names
nothing ready.

That sentence is true and it stops one step short. Block H holds one line, blocked on a
single task in another block. Nothing in the answer says so. The caller who wants to
work on the priority has to open the roadmap, read the priority list, find the block's
lines, read their deps, and look each one up - which is the reading brief exists to
replace, done by hand, at the exact moment the answer was least obvious.

The data is already there. brief computes unblocks for the task it picked, so the graph
is walked in that direction; what is missing is the inverse question asked of the
priority blocks rather than of the pick. Something on the order of: priority Block H is
1 line, blocked; RK-nnn would release it - alongside the pick rather than instead of it,
because the pick may still be the right call when the blocker is expensive.

The case that makes it worth having is the one where the blocker is cheap and nobody
looked. Four sessions of falling through to the same partial is what prompted this.

### §RK1305 Budget answers for a retirement too

Measured while retiring a task in an adopting project. The reason was refused three
times in a row - 250 characters, then 212, then 205, against a limit of 200 - and each
rewrite cut a clause out of the one field whose whole job is to carry evidence. The
sentence that finally landed says less about the measurement that settled the decision
than the first draft did.

Each refusal did its job: it named the limit and how much to delete. What none of them
could do is what `budget` already does before a line is added or a completion written -
answer, before a word exists, how much room this particular retirement has. A
retirement's reason shares the rendered line with the symptom it is retiring, and a long
symptom leaves a short reason, so the usable maximum is not the published one and cannot
be guessed from it.

The skill asks a retirement to open with the decision, give the evidence in numbers
where there are numbers, and say where the conclusion now lives. That is three clauses,
drafted against a budget the author cannot ask for. Extending `budget` to answer for a
retirement costs one more shape of the same reading and removes the loop that trims
evidence away.

### §RK1306 The two clauses the shipping budget does not price

Measured on quickshell: five ships, five refusals — QS8, QS9, QS10, QS87 and QS88 each
took a `why.too-long` before landing, and every one passed `--recorded-in` or
`--superseded-design` or both.

`brief`'s `shipping` block states the ledger allowance correctly — 189 for QS87, the
number the refusal quoted back. What it does not state is that the two optional clauses
are spent from it. `--recorded-in src/Quickshell.Render/GlyphAtlas.cs` took 64 of QS8's,
`--superseded-design` took 45 of QS87's, and parenthesising them added 28 more. None of
it is visible before the write, so a `why` composed to the published allowance is
refused by arithmetic the caller could not have done.

The refusals themselves are excellent — each names what every argument cost and what is
left for the outcome, which is why the second attempt always lands. The whole complaint
is that there is a first attempt.

The documentation already promises this: `brief` is described as printing "the whole of
what the ship will compose — the ledger sentence's allowance, what each of the two
clauses appended to it costs". The payload carries the first half only.

Two shapes. Rows in `shipping` for each clause, costed from the id and the anchor, which
are known — the path is not, so that row would be per-character. Or `budget <id>
--shipping --recorded-in <path> --superseded-design "<draft>"`, pricing the exact call,
as `budget --block --why --body` already prices an `add`.

Falsified if a ship carrying both clauses can be composed from `brief` alone without a
refusal.

### §RK1307 The answer the terminal gets and the payload does not

Measured on quickshell, after QS12 shipped and took its own criteria with it.

`criterion list --task QS12` prints, to a person:

    docs/ROADMAP.md: no criteria for QS12 — `criterion add --task QS12 …` opens the list

That is the whole answer: which empty, and the command that fills it. The same call with
`--json` returns `{"criteria": [], "blocks": [...]}` and nothing else — and that array
mixes block letters with the ids of tasks carrying criteria, so learning QS12's list is
*gone* rather than never opened means noticing QS12 is absent from a list of something
else.

The MCP tools serve the JSON, so every agent gets strictly less than the person at the
terminal, and loses the two things this verb is documented for: which empty, and the
door.

This is the second of its shape. RK1306 is the first: the shipping budget states the
ledger allowance and not what the two clauses spend from it, which the refusal names
perfectly once the write has failed. Both are the human path carrying a sentence the
machine path drops.

Two shapes, and the second is the interesting one. Add an `empty` word and a `remedy`
argv to this payload; or treat it as a class, auditing every verb whose human output
ends in a named command and asserting in a test that the same call's `--json` carries
it. The first fixes one read; the second stops a third being found by an agent rather
than here.

Falsified if some payload already carries its remedy, making this one verb's oversight
and not a boundary nobody drew.

### §RK1309 The budget a line does not have yet

`add`'s own help states the rule this misses: "Nothing is written unless every field
passes: a limit reported after the prose exists is a limit discovered too late to save
the tokens it was meant to save." The prose fields are exactly where it still happens.

Observed in pportal, 2026-08-22. A section body was written to a file, passed with
--section-body-file, and refused: 266 words against a limit of 250. The refusal is a
good one - it names the overage, the remedy in words, and which paragraph is longest. It
arrives after the paragraph has been written, which for an agent caller is the cost the
rule is about, and the second attempt pays for the whole body again.

`brief` already prints this budget well - "budget why 69 of 195 left, aim 10 more words,
278 for prose". But `brief` speaks about a task that EXISTS. A caller composing a NEW
line with `add --section` has no id yet, so there is nothing to brief, and the numbers
it wants sit in roadkeep.toml under names it has to know to look for.

The gap is narrow and so is the fix: the same budget, addressable before the line is
minted. `budget --block <x> --section` would answer it, or `add` could take the heading
alone and report what a body under it may weigh, which is one round trip instead of two
and no wasted paragraph.

### §RK1310 Finding the anchor a sentence is in

Observed in pportal, 2026-08-22. A line count stated in the prose had gone stale, and
the correction is `section amend <anchor> --replace <old> --with <new>`. The anchor was
wrong: the claim sized one C file, the task about that file was one id, and the sentence
sizing it lived in the section of a DIFFERENT id - the one covering three such files
together.

The refusal was a good one. It said the text does not occur in the section named and
pointed at `section show`, which is the right next command. What it could not say is the
thing the caller wanted: that the text occurs once, and where. Every fact needed to say
so had just been read.

The general shape is that `amend` and `section amend` are addressed BY anchor and the
caller often knows only the text. A pointer resolves an id to a section; nothing
resolves a sentence to one. So the loop is show, read, guess again - and for an agent
caller each turn of it is a file printed into a context window.

`section find <text>` would close it: the anchors carrying that text, with a count each,
so a caller can see at once whether `--replace` will be accepted and by which anchor. It
reads and writes nothing, which is why it can be cheap.

The failing `amend` could also name it directly, which is the same lookup one step
earlier and turns a refusal into an instruction.

### §RK1314 The sentence that rode along with the key set

`roadkeep config` prints, under `[criteria]`, the sentence "`[non_goals]` - the two
fields the roadmap's other bullet has (RK70)". That is the other table's docstring, and
it names the other table.

One value reader is right, and RK1265 argued it: `[criteria]` is the same two numbers
about the positive twin, so `_scope` takes the table name and only the problems it
reports differ - two copies would be two opt-ins that came to accept different shapes.
What followed the docstring across is not that. `describing` maps both addresses to
`_SCOPE_KEYS`, so the sentence rides along with the key set.

It matters because of what this read is for. `config` exists so a key is written from
what the build accepts rather than from memory, and the sentence beside each row is the
package's own words about that key, which is the whole reason nothing on that surface is
a second copy of a rule. A row whose words describe a different table is worse than a
row with none: nothing in it disagrees with itself, the two tables carry the same two
key names, and the reader has no way to tell it from a correct row.

The fix is a sentence about criteria taken from where that table is documented, read per
table rather than per key set.

## Block D — The gate

### §RK1308 Two findings, one exit code

Observed in pportal, 2026-08-22, mid-task. `roadkeep lint` exited 1 on a backlog that
had just been written by `ship` and had drifted in no way at all. The finding was
`install.stale`: the wired skill was behind the engine answering. Nothing about the
three governed files was wrong, and the report said so in the same breath - "311
line(s), 32 section(s) ... clean" - while still returning 1.

That exit code is the whole contract of the CI job roadkeep publishes. So a repository
whose only gate is `roadkeep lint` goes red on every push, for every contributor, until
somebody runs `roadkeep install` - which is not a backlog edit but a write into
.claude/, and in a project holding one task to one commit it has to become a commit of
its own, unrelated to whatever was being shipped.

Worse, the remedy the finding names does not clear the report. After `roadkeep install`
the run is clean and still prints `engine.disagreement`: the gate is 0.1.1100 and the
wired plugin is 0.1.1090, which moves by `/plugin update` and not by anything lint
offers. A line that appears on every successful run is a line people stop reading.

Two findings, two audiences, one exit code. What the gate is for is whether the governed
lines drifted; whether this checkout's installed surface matches the engine is
maintenance, and true of the machine rather than of the branch.

## Block E — Adoption

### §RK1313 The two tables the scaffold stopped writing

Observed on a tree `roadkeep init` had just created, 2026-08-23. `criterion add --block
A` refused with "roadkeep.toml declares no [criteria]", and `add --requires hardware`
refused with `requires.unknown`, naming a table the file does not carry.

RK1040 already settled this shape. `init` writes `## Non-goals` into the roadmap and,
for the same reason, writes `[non_goals]` empty into the config: a schema applied to
prose nobody wrote to it reports on adoption, but a section the scaffold just emptied
has no prose to report on, and leaving it ungoverned refuses the one verb that fills it.
The comment above that table in `render_config` says so.

RK1265 added the positive twin and RK1297 added the requirement vocabulary, and neither
reached the render. So the two verbs that arrived last are the two a fresh project
cannot call, and the remedy each refusal names is a hand edit to configuration this tool
owns - which is what RK1264 built `declare` to remove, and which over MCP is not an edit
at all.

They are not one fix. `[criteria]` is an opt-in, so the empty table is the whole of it.
`[requirements]` is a vocabulary: `declared = []` governs nothing and changes only which
refusal the author reads, so what belongs there is the commented stanza - the shape
`[ids]`, `[headings]` and `[ledger]` are already written in, which is written only where
a project departs from what every project starts with.

## Block F — The plugin

## Block G — The editor surface (the backlog where the file is open)

## Block H — The tool's own shape (what one verb costs to change)
