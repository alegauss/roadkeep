# roadkeep — Shipped Ledger

> What has **shipped**, indexed by Block — one entry per task. `git log` is
> authoritative for detail. Active work lives in [ROADMAP.md](ROADMAP.md); design
> rationale for unshipped work lives in [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> An entry is its roadmap line with the marker set to ✅ and the `deps` and
> `→ §RK<n>` fields dropped — the rationale section is deleted when the task ships,
> so a pointer to it would not resolve. The block headings mirror ROADMAP.md.

## Block A — The model

- ✅ **RK1** **Nothing knows what a task line is, so every check is a regex over prose** — a schema over the six fields (id, status, block, deps, symptom, why, ref) is the only thing that can refuse an over-length line at write time.
- ✅ **RK2** **A parser that cannot re-render what it read corrupts the file it edits** — parse → render → byte-identical is the invariant that lets a CLI own writes to a hand-written Markdown file.
- ✅ **RK3** **Hardcoding one project's vocabulary makes the tool single-use** — `roadmap.toml` carries prefix, file paths, marker set and per-field limits, so Turing's `STRATEGY.md` and Shio's absence of one are both configurations.
- ✅ **RK4** **The next id cannot be inferred from a block header, and a wrong guess collides with a retired one** — take the max across every configured file, in one command, with no counter file to drift.
- ✅ **RK27** **A pointer's target is numbered by hand, and deleting a section leaves a hole nobody renumbers** — keying each rationale section by task id makes the pointer derivable from the line, so shipping costs no renumbering and resolving it costs no reading of the outline.
- ✅ **RK28** **A dep the tool cannot resolve reads exactly like one that is merely pending** — `Block P` and `real design partners` are real deps on work outside the backlog, so a resolver has to name them unresolvable instead of counting them unfinished.
- ✅ **RK31** **The reasoning behind a shipped decision survives only in a commit nobody greps** — the shipping commit is derived from the ledger's own diff, so the reasoning is one lookup away and no stored hash can rot when history is rewritten.
- ✅ **RK37** **A dep on a block that does not exist resolves as satisfied** — a block is declared by a heading and by nothing else, so a dep naming one no heading declares is unresolvable, never a block that happens to have nothing open.
- ✅ **RK43** **A changelog whose lines carry no status marker parses as zero entries and zero rejects** — a bullet that leads with a bold id is now a reject naming the empty slot, and `markers.ledger = false` states a ledger's marker once instead of on all 920 of its lines.
- ✅ **RK44** **Under ref_scheme = outline a heading numbers itself, so 151 headings yield zero sections** — the anchor is read per scheme, so an outline numbers its own headings and keeps the sigil on the pointer: Shio's 151 headings are 146 sections and its 72 pointers all resolve.
- ✅ **RK47** **A lettered outline subsection is no anchor, so 20 of Turing's headings are sections nothing sees** — the anchor's final segment may be one lowercase letter, measured and not guessed: it admits Turing's 20 lettered headings and nothing more, one of them 779 words the budget was not charging.

## Block B — Authoring

- ✅ **RK5** **Writing the line by hand is where the prose leaks in** — the fields are refused at input, so the limit is met before a sentence is composed to fill it and the file is only ever touched by a line that renders back to what was written.
- ✅ **RK6** **Shipping a task is four edits across three files, so one is always missed** — the three edits are one command that validates every one of them before a file is touched, and the roadmap line is removed rather than stubbed so status keeps one home.
- ✅ **RK7** **Two files can disagree about one task's status** — the marker is written in the roadmap alone, and a sibling file carrying one for the same id is refused rather than reconciled because nothing says which of the two would be right.
- ✅ **RK8** **A dep annotation goes stale the moment its target ships** — the annotation is derived from the resolver on every write, so a shipped dep never reads as pending and a marker nobody typed is never invented.
- ✅ **RK9** **The four files are not four of the same thing, and prose has no line to validate** — prose is governed by section instead: an anchor a pointer resolves, a budget in words, and a place derived from the block, with drop being the edit ship already calls.
- ✅ **RK38** **A write reports an exit code and nothing about what it changed, so only a human can react to it** — every mutator prints the id, the block and whether that block still holds an open line, which is the whole event a hook needs and the last thing the tool does about it.
- ✅ **RK41** **A fix that was never planned has no door into the ledger** — a fourth command writes the ledger entry alone, so a fix nobody planned is recorded without a fictitious roadmap line shipped in the same breath to carry it.
- ✅ **RK45** **A section belonging to no task lands after the last block, where it reads as that block's rationale** — the place is derived from the anchor: the end of the subtree of the longest anchor the new one extends, and one extending nothing this file declares is refused rather than appended.
- ✅ **RK64** **Shipping one of several tasks that share a section deletes the design the others still point at** — A section another open line points at is kept and the reason is reported, so shipping one of Shio's four tenant tasks no longer deletes the design the other three point at.
- ✅ **RK65** **A line can be created and removed but never corrected, so every adoption defect needs a hand-edit** — amend corrects an open line's why, deps or pointer — validated at input, symptom excluded — which is the door none of Shio's seventeen defects had.

## Block C — Query

- ✅ **RK10** **Counting a backlog by grep silently drops the lines it fails to match** — every count prints what it could not read beside what it did, so a broken line, a parked task and a marker this project never declared are visible instead of silently absent.
- ✅ **RK11** **Picking work means reading the whole file to find one task whose deps are shipped** — three tiers answer it and the answer names the one that fired: work already in progress, then the priority a project declares, then the lowest id whose deps all shipped.
- ✅ **RK12** **A task's design lives in a second file and nothing joins them** — one call joins the line, its rationale section and the paths its text names, and an absent section carries the reason it is absent instead of reading as a design that exists.
- ✅ **RK13** **A blocked task looks identical to a ready one, and one that unblocks half the backlog to one that unblocks nothing** — the walk is tested code instead of an ad-hoc traversal: it names the blocker chain, reports a cycle as a group, and counts how many tasks shipping this one unblocks.
- ✅ **RK29** **Starting a task costs reading two whole files to learn one line's worth of context** — one call composes the line, its rationale, its resolved deps, the blocker chain, what shipping it unblocks and the non-goals, bounded to fit a tool result.
- ✅ **RK32** **An id that exists in neither file was retired for a reason nobody recorded** — a line now leaves by three recorded doors: retire writes the forward pointer at the moment of the decision, and gaps resolves the older holes against the commit that removed them.
- ✅ **RK39** **A README and a site restate a backlog they cannot re-read, so both are stale from the first ship** — the restatement is derived: one marked README block and one JSON payload, idempotent and stamped with nothing, so a refresh with nothing to say makes no diff.
- ✅ **RK40** **A block's own next task is not askable, so a global answer reads as that block being finished** — every part of a scoped answer is about that block, so nothing open in Block C is the wording that means finished and a lower id elsewhere can no longer read as one.
- ✅ **RK42** **The landing page claimed 9 of 36 tasks shipped through twenty-five ships** — `export --site` splices the same projection into the page as HTML between the same two markers, so one call refreshes both restatements and a test fails when either drifts.

## Block D — The gate

- ✅ **RK14** **A format that is documented but not enforced is a format that drifts** — the gate is one command that re-reads every governed line through the schema that wrote it and exits 1 on any drift, so a hook and an Action share one contract and neither parses a report.
- ✅ **RK15** **A pointer to a section that does not exist reads as a design that does** — the pointer is resolved in both directions and the paths a line claims against disk, so a design that does not exist can no longer read as one that does.
- ✅ **RK16** **A report of ninety-two violations is a report nobody acts on** — the mechanical half is repaired from the parse and the editorial half is left, so the report that survives a first run on a real backlog is one somebody reads.
- ✅ **RK17** **A gate that runs only on a developer's machine is not a gate** — the same command is declared once as an action and once as a pre-commit hook, so the exit code is enforced where the commit happens and where the push lands.
- ✅ **RK30** **The instruction file loaded every turn has a budget nothing enforces** — the budget of a file loaded every turn is a declared number in the configuration and an exit code in the gate, instead of a sentence inside the file it governs.
- ✅ **RK34** **An invisible character reports a visible error about something else** — an invisible codepoint is reported as its own name, class and column and nothing else on that line is judged, so the diagnosis stops naming the consequence.
- ✅ **RK35** **A dep on a range or a block hides how much work it actually names** — a dep on a block or a range is reported with the open tasks it expands to, at exit zero, so the abbreviation stops costing whoever counts deps to judge a line.
- ✅ **RK36** **A rationale section can gain a requirement the line carrying its status never mentions** — a section edited while the line carrying its status was not is reported from the diff at exit zero, so a requirement written only into the reasoning is seen before it leaves with it.
- ✅ **RK46** **All 8 paths reported missing on Shio are globs, placeholders or files the task will create** — A roadmap names unshipped work, so its paths are the ones not there yet: resolve the claim in the ledger only, never for a token carrying a glob, an ellipsis or a placeholder.
- ✅ **RK60** **A project that adopts the tool with drift already in it has its every turn blocked by history** — The Stop gate keeps only findings on lines the working tree changed, so Shio's 278 fell to zero at the end of a turn that touched none of them.
- ✅ **RK58** **A refusal names a command the machine may not have, now that the plugin needs no install** — The refusal names mcp__roadkeep__add and ship before the shell form, so the route the same plugin certainly installed is the one it offers first.
- ✅ **RK61** **Under the outline scheme no check can say which task a section belongs to** — A section's owners are the anchor under the id scheme and the ids its heading names under an outline, so Shio's 39 stale sections and 9 orphans are visible.
- ✅ **RK63** **A heuristic read off this repository disabled the new check on the corpus it was written for** — Ownership is the claim a heading makes by naming a task, with no exemption for where the section sits, and this repository's own preface stopped making it.

## Block E — Adoption

- ✅ **RK18** **A tool that requires an empty repo cannot be adopted by the repo that needs it** — `init` scaffolds the files and config, and `adopt` reports what an existing backlog must change to pass.
- ✅ **RK19** **Installing from a git clone keeps a standard local** — publish to PyPI so `uvx roadkeep` runs with no checkout.
- ✅ **RK20** **Shio's 92 active lines average 142 words against a one-sentence rule** — migrating a real backlog is the only test of whether the schema fits a live project.
- ✅ **RK48** **A ledger whose lines carry no marker reads as prose, and every dep on one goes unknown** — The ledger's shape is declared in [ledger] — marker and symptom, either absent — so Shio's 234 entries parse and its unknown deps fall from 96 to 5.
- ✅ **RK51** **A link written relative to its own file is read as a path the repository lacks** — A token now resolves against the file's own directory as well as the root, so Shio's file-relative ledger links fall from 886 findings to 61.
- ✅ **RK50** **One budget judges a roadmap line and a ledger of history nobody will rewrite** — A limit is declared per role in [limits.<role>], so Shio's ledger keeps its own 4300 and its length findings fall from 600 to 134.
- ✅ **RK52** **A shipped line is told to move its second sentence to a section that was deleted on ship** — The two prose rules are per role in [rules.<role>], read by lint and by the write path alike, so Shio's findings fall from 629 to 347.
- ✅ **RK53** **An example line inside a fenced code block is read as a task and counted** — The parser tracks the fence, so a quoted example is text: the section documenting this change is one the tool refused to write before it.
- ✅ **RK49** **A follow-up nested under its parent line is invisible to every count and every pick** — An indented task line parses and keeps its indentation verbatim, so Shio's four nested follow-ups are counted, picked and never handed out twice.
- ✅ **RK54** **Deleting a section one line at a time validates half-deleted states nobody wrote** — A span is deleted in one validated edit, so a section quoting a fenced example is never half-removed and re-parsed as a file nobody wrote.
- ✅ **RK55** **A MIME type, an i18n key and a list of method names are reported as missing files** — A path claim is reported only when it has an extension and its directory exists, which takes Shio's 61 findings to the 1 naming a renamed file.
- ✅ **RK62** **A roadmap line for work already in the ledger has no door out of the roadmap** — ship closes a roadmap line whose id the ledger already records and whose marker the roadmap may not carry, leaving the entry untouched.

## Block F — The Claude Code plugin

- ✅ **RK22** **An agent can hand-edit the file the CLI is supposed to own** — A `PreToolUse` hook denies `Edit`/`Write` on a governed file and answers with the command to call, and a `Stop` hook runs `lint` so a `Bash` bypass is caught before the turn ends.
- ✅ **RK23** **Rules resident every turn spend the budget they exist to protect** — package the format as a skill with trigger phrases so it loads when a governed file is in play, and not before.
- ✅ **RK24** **Shelling out puts argument names in prose, where they are guessed** — expose `add`/`ship`/`pick`/`lint` as MCP tools so the field schema *is* the tool's input schema.
- ✅ **RK25** **A human driving the same standard should not have to learn the CLI** — `/roadkeep:add`, `/roadkeep:ship`, `/roadkeep:pick` and `/roadkeep:lint` over the one engine.
- ✅ **RK26** **A plugin installed by hand is a plugin one project has** — publish a `marketplace.json` so `/plugin install` reaches it.
- 🗑 **RK56** **Installing the plugin is not enough: every surface it declares calls a console script the user has to install first** — superseded by RK57: Its sentence lost a fragment to shell backtick substitution, and the format has no door that edits prose in place.
- ✅ **RK57** **Installing the plugin is not enough: every surface it declares calls a console script the user has to install first** — Both surfaces run python on the launcher at the plugin's own root, so /plugin install is the whole setup and no console script or PATH entry is needed.
- ✅ **RK59** **Four tools cover four commands, so the eight a task actually needs still require a shell** — Twelve tools cover the write path and the reads a task calls, nested commands included, so an installed plugin needs no shell for anything after init.
