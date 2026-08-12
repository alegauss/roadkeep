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

### §RK1112 Show prints the subtree, amend takes the body

`section show <anchor>` prints the section **and its subsections**. `section amend
<anchor> --body-file` accepts only the section's **own** body — its own help says so:
*"The subtree is not touched: a subsection is amended by its own anchor."* So the
natural round-trip, show a section, edit one sentence, amend it back, is refused on any
section that has children.

**Reproduced in claude-tray**, correcting one citation inside `§XXIII`, which has six
subsections:

```
$ roadkeep section show XXIII --role improvements > body.md   # 1692 words: XXIII + .1 … .6
$ roadkeep section amend XXIII --body-file body.md --role improvements
roadkeep: refused, nothing written:
  body: 1692 words, limit is 300: delete 1392 words; a section this long is two sections, or a
  paragraph that belongs in the commit; by paragraph ¶1 60, ¶2 63, … ¶20 is the longest
```

The refusal is correct about the number and wrong about the cause, and it names neither
`show` nor the subtree. An author reads *"delete 1392 words"* and *"a section this long
is two sections"* as a verdict on prose they did not write, on a body they only meant to
pass through. The workaround is to slice the file by hand between the heading and the
first `###`, which is the hand-edit the guard exists to stop.

**Two candidate fixes, and the choice is editorial.** Either `show` grows a default or a
flag that prints the own body alone, so the round-trip is closed; or `amend` detects
that the body it was handed begins with this section's own text and continues into its
declared children, and says *that* instead of counting words. The second also catches
the copy-paste case where no `show` was involved.

## Block C — Query

## Block D — The gate

### §RK1111 A namespaced citation read as its namespace

`ref.dangling` extracts the citation `§S` from the prose `§S:V` and reports it as an
anchor no file declares. `§S:V` is the namespaced address of STRATEGY.md's fifth section
— `anchors --role strategy` lists `S:V  1 live` in the same working tree — so the rule
is red on prose that is correct.

**Reproduced in claude-tray**, whose `[refs] strategy = "S"` gives the second prose file
a namespace:

```
$ roadkeep lint
STRATEGY.md:67  ref.dangling  §S:VII cites §S, which is not in IMPROVEMENTS.md or STRATEGY.md
$ sed -n 67p STRATEGY.md
- **No paid tier, no accounts, no license server.** Changing this would invalidate §S:V.
```

That line carries no bare `§S`; its only citation is `§S:V`. Engine roadkeep 0.1.728
(06cca7f). Capture: `.roadkeep/reports/20260812T154201Z-lint-ad6b4e3c.json`.

**Why it matters more than one line.** The rule's own message is that a dangling pointer
and a typo cannot be told apart from the next command on — which is exactly what a false
positive does one level up: the finding cannot be told from a real one, and the fixes
available to the project are to reword correct prose or to hide the citation in a code
span, which removes the relation the rule checks. Every project that namespaces a second
prose file inherits it.

**Where the fix probably is.** The scanner appears to match `§` plus a roman numeral and
stop, without consuming `:` and the address after it. Code spans are already skipped — a
backticked address in the same repository is not reported — so the extractor is the
layer, not the reporter.

## Block E — Adoption

## Block F — The plugin

### §RK1113 install --check reads the wrong wiring variant

`install` writes a project's surfaces two ways. The default points the hook, the server
and the skill at a checkout — `${CLAUDE_PROJECT_DIR}/../roadkeep/scripts/roadkeep.py` —
and `--committed` points them at `.claude/hooks/roadkeep-launch.py`, a launcher
committed to the adopting repository so a session that installs no plugin and clones
nothing still has a guard.

`--check` compares against the default alone. On a project adopted with `--committed` it
reports every one of those surfaces as drifted and names the plain `install` as the
repair. Running it rewrites them to the checkout path, which is the one change the
committed launcher exists to prevent: the file stays on disk, nothing references it, and
the web session loses its hook.

Measured on the dockerdesk repository at commit acc7fc1, a tree with no local edits:
`install --check` answered "3 surface(s) differ", the plain `install` then changed
`.mcp.json`, `.claude/settings.json` and `.claude/skills/roadkeep/SKILL.md`, and
`install --committed` restored all three to exactly HEAD. Nothing had drifted; the check
was reading a variant that project never chose. The `SessionStart` message is built from
the same answer, so such a session opens by being told its own wiring is stale — and an
agent that believes it spends its first turn undoing the adoption.

What decides the answer is already on disk: a committed launcher that the settings and
the server actually reference is the project saying which variant it is. Read that
first, and report drift against it.

### §RK1114 A partial ship leaves a line the picker offers and the claim refuses

`ship <id> --part` writes a ledger entry and deliberately leaves the roadmap line open
at ⏳, because the rest of it is still a task. Its own answer says so, and names `ship
<id>` as the command that finishes it later. So a ⏳ line with a partial entry is the one
state the tool creates on purpose to mean "come back to this".

The claim path does not read it that way. It looks for the id in the ledger, finds the
partial ✅, and refuses — with the rule about status living in exactly one file, which is
the right rule about the wrong situation: the roadmap says ⏳ and the ledger says "half
of it", and those do not disagree.

Measured on the dockerdesk repository, one command after the other, nothing else
changed:

    $ roadkeep pick
    DD2  Block A  ⏳  docs/ROADMAP.md:7
      because  lowest ready id

    $ roadkeep brief DD2
    DD2  Block A  ⏳  ready  docs/ROADMAP.md:7

    $ roadkeep brief DD2 --claim
    roadkeep: DD2 already carries ✅ in the changelog at docs/CHANGELOG.md:6: status lives in
    exactly one file, because two files that both express it will eventually express different
    ones and nothing says which is right

`pick` names it, `brief` calls it ready, and the one verb that starts work on it
refuses. `status <id> --claim` is no way round either, since moving ⏳ to 🛠 to take a
claim discards the fact that half of it shipped — which is the whole thing that marker
carries.

The picker and the claim disagree about one line, and the picker is right: an id in the
ledger is a finished task only when the roadmap no longer carries the line.

### §RK1115 The pause a budget forbids

pportal's PP55 named an instrument the machine does not have, so the honest door was a
pause. It refused twice, and the second refusal is this line. `defer` wraps the author's
sentence rather than rewriting it - `set aside (<reason>): <why>` - and then charges the
whole composed string to `[limits].why`. PP55's why is 165 characters against a limit of
169, so the 14-character prefix alone overflows by 10 before a reason is written at all:

```
roadkeep defer PP55 --reason 'no Reflex panel here'
roadkeep: refused, nothing written:
  why: 199 characters, limit is 169 (roadkeep.toml:60 [limits].why) ...
  delete 30 characters - about 5 words [why.too-long]
```

A reason of zero characters still fails. So a line written to its budget cannot be
paused at all, and the tool is what encouraged writing it that way: `brief` prints "why
3 of 168 left" as headroom to fill. What remains are the two terminal doors, for a line
that is neither shipped nor abandoned.

The message compounds it. It names `[limits].why` and the author's own prose, says
nothing about the prefix that actually overflowed, and sends the reader to trim a
sentence they did not write and that the module promises never to rewrite.

The fix is a decision rather than an obvious edit: charge only the author's half to the
limit and let the derived prefix ride free, give the wrapped form a budget of its own,
or keep the refusal and make it name the prefix and point at `amend`.

## Block G — The editor surface (the backlog where the file is open)
